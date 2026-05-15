import socket
import time
import re

def get_vlans(host, port, password, timeout=5):
    """Get VLANs with timeout - returns quickly even on failure"""
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        try:
            sock.connect((host, port))
        except:
            return []
        
        time.sleep(0.5)
        
        # Send Enter
        sock.send(b"\r\n")
        time.sleep(0.5)
        
        # Send password
        sock.send(password.encode() + b"\r\n")
        time.sleep(0.5)
        
        # Send command
        sock.send(b"terminal length 0\r\n")
        time.sleep(0.5)
        sock.send(b"show vlan brief\r\n")
        time.sleep(1)
        
        # Read output
        output = b""
        start = time.time()
        while time.time() - start < 3:
            try:
                sock.settimeout(0.5)
                chunk = sock.recv(4096)
                if not chunk:
                    break
                output += chunk
            except socket.timeout:
                break
            except:
                break
        
        sock.close()
        
        # Parse output
        output_str = output.decode('utf-8', errors='ignore')
        vlans = []
        for line in output_str.split('\n'):
            match = re.match(r'^(\d+)\s+(\S+)\s+(\S+)\s+(.+)$', line.strip())
            if match and match.group(1).isdigit():
                vlans.append({
                    'vlan_id': match.group(1),
                    'vlan_name': match.group(2),
                    'status': match.group(3),
                    'interfaces': match.group(4).strip() if match.group(4) != '-' else ''
                })
        return vlans
        
    except Exception as e:
        print(f"Error getting VLANs: {e}")
        return []
    finally:
        if sock:
            try:
                sock.close()
            except:
                pass