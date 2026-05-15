import json
import re
from ollama import Client

OLLAMA_HOST = 'http://localhost:11434'
client = Client(host=OLLAMA_HOST)
DEFAULT_MODEL = 'phi3'


def extract_config_params(user_prompt, model=DEFAULT_MODEL):
    extraction_prompt = f"""
    Extract network configuration parameters from the following user request.
    Output ONLY valid JSON. No other text.
    
    JSON schema:
    {{
        "action": "create" or "delete" or "modify" or "shutdown" or "no_shutdown",
        "vlan_id": number (if mentioned, otherwise null),
        "vlan_name": string (if mentioned, otherwise null),
        "ports": string (e.g., "Gi0/5-8" if mentioned, otherwise null),
        "interface": string (if mentioned, otherwise null)
    }}
    
    User request: {user_prompt}
    """
    
    response = client.generate(model=model, prompt=extraction_prompt, stream=False)
    
    try:
        json_match = re.search(r'\{.*\}', response['response'], re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return json.loads(response['response'])
    except:
        return {'action': None, 'vlan_id': None, 'vlan_name': None, 'ports': None, 'interface': None}


def generate_config_from_params(params):
    commands = ['configure terminal']
    
    action = params.get('action', '').lower()
    vlan_id = params.get('vlan_id')
    vlan_name = params.get('vlan_name', '')
    ports = params.get('ports')
    interface = params.get('interface')
    
    if action in ['delete', 'remove'] and vlan_id:
        commands.append(f'no vlan {vlan_id}')
    elif action == 'create' and vlan_id:
        commands.append(f'vlan {vlan_id}')
        if vlan_name:
            commands.append(f'name {vlan_name}')
        commands.append('exit')
    
    if action == 'shutdown' and interface:
        commands.append(f'interface {interface}')
        commands.append('shutdown')
        commands.append('exit')
    
    if action == 'no_shutdown' and interface:
        commands.append(f'interface {interface}')
        commands.append('no shutdown')
        commands.append('exit')
    
    if ports and action in ['create', 'modify'] and vlan_id:
        commands.append(f'interface range {ports}')
        commands.append('switchport mode access')
        commands.append(f'switchport access vlan {vlan_id}')
        commands.append('exit')
    
    commands.append('end')
    commands.append('write memory')
    
    return commands


def generate_config_safe(user_prompt, model=DEFAULT_MODEL):
    try:
        params = extract_config_params(user_prompt, model)
        commands = generate_config_from_params(params)
        return True, commands
    except Exception as e:
        return False, str(e)