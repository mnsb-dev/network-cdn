"""
telnet_helper.py - Clean, reliable telnet connection to Cisco switches
"""

import subprocess
import re


def run_command(host, port, command, timeout=20):
    """
    Run a single command on a switch and return the output.
    Properly disables pagination first.
    """
    try:
        # Send commands in sequence with proper delays
        # Step 1: Disable pagination
        # Step 2: Send the actual command
        full_script = f"""
(
echo ""
sleep 1
echo "terminal length 0"
sleep 2
echo "{command}"
sleep 4
echo "exit"
) | telnet {host} {port} 2>&1
"""
        result = subprocess.run(full_script, shell=True, capture_output=True, text=True, timeout=timeout)
        
        output = result.stdout
        
        # Clean up the output
        lines = output.split('\n')
        cleaned_lines = []
        start_capturing = False
        
        for line in lines:
            line = line.rstrip()
            
            # Skip telnet negotiation
            if 'Trying' in line or 'Connected to' in line or 'Escape character' in line:
                continue
            if 'telnet>' in line:
                continue
            if line.startswith('^]'):
                continue
            if '--More--' in line:
                continue
            if 'Connection closed' in line:
                continue
            
            # Start capturing when we see the actual command output
            if command in line:
                start_capturing = True
                continue
            
            # Skip the pagination command and exit
            if 'terminal length 0' in line:
                continue
            if 'exit' in line:
                continue
            
            # Capture lines that are actual output
            if start_capturing and line:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
        
    except subprocess.TimeoutExpired:
        print(f"Timeout on {host}:{port}")
        return ""
    except Exception as e:
        print(f"Error: {e}")
        return ""


def get_interfaces(host, port):
    """Get all interfaces with their status - Flexible column detection"""
    output = run_command(host, port, "show interfaces status")
    
    interfaces = []
    lines = output.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip header lines
        if 'Port' in line and 'Name' in line and 'Status' in line:
            continue
        if '-----' in line:
            continue
        
        parts = line.split()
        if len(parts) < 3:
            continue
        
        port_name = parts[0]
        if not port_name.startswith(('Gi', 'Fa', 'Et', 'Te')):
            continue
        
        # Determine which column contains the status
        # Common patterns:
        # Pattern 1: Port  Name  Status  Vlan  Duplex  Speed  Type
        # Pattern 2: Port  Status  Vlan  Duplex  Speed  Type (Name missing)
        # Pattern 3: Port  Vlan  Status  Duplex  Speed  Type (Vlan in wrong place)
        
        # Check if the second part is a VLAN number or a status
        second_part = parts[1] if len(parts) > 1 else ''
        third_part = parts[2] if len(parts) > 2 else ''
        
        # If second part looks like a VLAN number (digits only) and third part looks like status
        if second_part.isdigit() and third_part in ['connected', 'notconnect', 'disabled', 'down', 'up']:
            # Pattern: Port  Vlan  Status  ...
            vlan = second_part
            status = third_part
            duplex = parts[3] if len(parts) > 3 else 'auto'
            speed = parts[4] if len(parts) > 4 else 'auto'
            port_type = parts[5] if len(parts) > 5 else ''
        else:
            # Assume standard pattern: Port  Name  Status  Vlan  ...
            # Or Port  Status  Vlan  ... (Name missing)
            status_idx = 1
            vlan_idx = 2
            
            # If the second part is a status word, then Name column is empty
            if second_part in ['connected', 'notconnect', 'disabled', 'down', 'up']:
                status = second_part
                vlan = third_part
                duplex = parts[3] if len(parts) > 3 else 'auto'
                speed = parts[4] if len(parts) > 4 else 'auto'
                port_type = parts[5] if len(parts) > 5 else ''
            else:
                # Try to find status by scanning
                status = 'unknown'
                vlan = '1'
                for i, part in enumerate(parts):
                    if part in ['connected', 'notconnect', 'disabled']:
                        status = part
                        vlan = parts[i+1] if i+1 < len(parts) else '1'
                        duplex = parts[i+2] if i+2 < len(parts) else 'auto'
                        speed = parts[i+3] if i+3 < len(parts) else 'auto'
                        port_type = parts[i+4] if i+4 < len(parts) else ''
                        break
        
        interfaces.append({
            'port': port_name,
            'name': '',
            'status': status,
            'vlan': vlan,
            'speed': speed,
            'duplex': duplex,
            'type': port_type
        })
    
    return interfaces


def get_vlans(host, port):
    """Get all VLANs with their ports - Fixed comma issue"""
    output = run_command(host, port, "show vlan brief")
    
    vlans = []
    lines = output.split('\n')
    current_vlan = None
    current_ports = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip header lines
        if 'VLAN' in line and 'Name' in line and 'Status' in line:
            continue
        if '----' in line:
            continue
        
        parts = line.split()
        
        # Check if this line starts with a VLAN ID (number)
        if len(parts) >= 3 and parts[0].isdigit():
            # Save previous VLAN
            if current_vlan:
                # Clean up ports - remove empty strings and duplicates
                clean_ports = []
                for p in current_ports:
                    p = p.strip()
                    if p and p != '-' and p not in clean_ports:
                        # Also remove any trailing commas that might be in the string
                        p = p.rstrip(',')
                        if p:
                            clean_ports.append(p)
                
                vlans.append({
                    'vlan_id': current_vlan['id'],
                    'name': current_vlan['name'],
                    'status': current_vlan['status'],
                    'ports': ', '.join(clean_ports) if clean_ports else ''
                })
            
            # Start new VLAN
            vlan_id = parts[0]
            name = parts[1]
            status = parts[2] if len(parts) > 2 else 'active'
            
            # Get ports from this line
            ports = []
            if len(parts) > 3:
                for p in parts[3:]:
                    p = p.strip().rstrip(',')
                    if p and p != '-':
                        ports.append(p)
            
            current_vlan = {'id': vlan_id, 'name': name, 'status': status}
            current_ports = ports
            
        elif current_vlan:
            # This line contains more ports (continuation of previous VLAN)
            for p in parts:
                p = p.strip().rstrip(',')
                if p and p != '-':
                    current_ports.append(p)
    
    # Save the last VLAN
    if current_vlan:
        clean_ports = []
        for p in current_ports:
            p = p.strip().rstrip(',')
            if p and p != '-' and p not in clean_ports:
                clean_ports.append(p)
        
        vlans.append({
            'vlan_id': current_vlan['id'],
            'name': current_vlan['name'],
            'status': current_vlan['status'],
            'ports': ', '.join(clean_ports) if clean_ports else ''
        })
    
    # Filter out default VLANs (1002-1005)
    result = []
    for vlan in vlans:
        try:
            vlan_id = int(vlan['vlan_id'])
            if vlan_id < 1002 or vlan_id > 1005:
                result.append(vlan)
        except ValueError:
            result.append(vlan)
    
    return result

def get_system_info(host, port):
    """Get system information"""
    output = run_command(host, port, "show version")
    
    info = {
        'version': 'Unknown',
        'uptime': 'Unknown',
        'hardware': 'Unknown',
        'serial': 'Unknown',
        'image': 'Unknown'
    }
    
    lines = output.split('\n')
    for line in lines:
        line_lower = line.lower()
        if 'version' in line_lower:
            match = re.search(r'Version\s+(\S+)', line)
            if match:
                info['version'] = match.group(1)
        if 'uptime' in line_lower:
            info['uptime'] = line.strip()
        if 'processor' in line_lower:
            info['hardware'] = line.strip()
        if 'system serial' in line_lower:
            parts = line.split()
            if len(parts) > 3:
                info['serial'] = parts[-1]
        if 'system image file' in line_lower:
            parts = line.split()
            if len(parts) > 3:
                info['image'] = parts[-1]
    
    return info


def get_mac_table(host, port):
    """Get MAC address table"""
    output = run_command(host, port, "show mac address-table")
    
    mac_entries = []
    lines = output.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if 'Mac Address Table' in line:
            continue
        if 'Vlan' in line and 'Mac Address' in line:
            continue
        if '----' in line:
            continue
        
        parts = line.split()
        if len(parts) >= 3 and parts[0].isdigit():
            mac_entries.append({
                'vlan': parts[0],
                'mac_address': parts[1],
                'type': parts[2] if len(parts) > 2 else 'dynamic',
                'ports': parts[3] if len(parts) > 3 else ''
            })
    
    return mac_entries


def get_cdp_neighbors(host, port):
    """Get CDP neighbors"""
    output = run_command(host, port, "show cdp neighbors")
    
    neighbors = []
    lines = output.split('\n')
    in_table = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if 'Device ID' in line:
            in_table = True
            continue
        if '----' in line:
            continue
        
        if in_table:
            parts = line.split()
            if len(parts) >= 6:
                neighbors.append({
                    'device_id': parts[0],
                    'local_interface': parts[1],
                    'capability': parts[5] if len(parts) > 5 else '',
                    'platform': parts[2] if len(parts) > 2 else '',
                    'port_id': parts[3] if len(parts) > 3 else ''
                })
    
    return neighbors


def get_port_security(host, port):
    """Get port security status"""
    output = run_command(host, port, "show port-security")
    
    ports = []
    lines = output.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if 'Port Security' in line:
            continue
        if '----' in line:
            continue
        
        parts = line.split()
        if len(parts) >= 1 and parts[0].startswith(('Gi', 'Fa', 'Et')):
            ports.append({
                'port': parts[0],
                'status': parts[1] if len(parts) > 1 else 'disabled',
                'max_addresses': parts[2] if len(parts) > 2 else 'N/A',
                'current_addresses': parts[3] if len(parts) > 3 else '0'
            })
    
    return ports


def get_stp_info(host, port):
    """Get Spanning Tree information"""
    output = run_command(host, port, "show spanning-tree")
    
    info = {
        'root_bridge': 'Unknown',
        'root_port': 'Unknown',
        'bridge_id': 'Unknown',
        'root_cost': 'Unknown'
    }
    
    lines = output.split('\n')
    for line in lines:
        line_lower = line.lower()
        if 'root bridge' in line_lower:
            info['root_bridge'] = line.strip()
        elif 'root port' in line_lower:
            info['root_port'] = line.strip()
        elif 'bridge id' in line_lower:
            info['bridge_id'] = line.strip()
        elif 'root cost' in line_lower:
            info['root_cost'] = line.strip()
    
    return info