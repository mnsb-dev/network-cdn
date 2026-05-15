# automation/views.py

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import subprocess
import time

from devices.models import Device
from devices.ollama_helper import generate_config_safe


def ai_config(request):
    """Display the AI configuration page"""
    devices = Device.objects.filter(is_active=True)
    context = {
        'devices': devices,
        'title': 'AI Configuration Assistant'
    }
    return render(request, 'automation/ai_config.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def api_generate_config(request):
    """Generate configuration from natural language prompt"""
    try:
        data = json.loads(request.body)
        user_prompt = data.get('prompt', '')
        model = data.get('model', 'phi3')
        
        if not user_prompt:
            return JsonResponse({
                'success': False,
                'error': 'Please enter a configuration request'
            })
        
        success, result = generate_config_safe(user_prompt, model)
        
        if success:
            return JsonResponse({
                'success': True,
                'commands': result,
                'prompt': user_prompt
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_http_methods(["POST"])
def api_deploy_config(request):
    """Deploy configuration to a device"""
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        commands = data.get('commands', [])
        
        if not device_id:
            return JsonResponse({
                'success': False,
                'error': 'Device ID required'
            })
        
        try:
            device = Device.objects.get(id=device_id, is_active=True)
        except Device.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Device not found'
            })
        
        if not commands:
            return JsonResponse({
                'success': False,
                'error': 'No commands to deploy'
            })
        
        # Create a temporary script file
        script_content = "#!/bin/bash\n"
        script_content += "sleep 1\n"
        script_content += "echo ''\n"
        script_content += "sleep 1\n"
        script_content += "echo enable\n"
        script_content += "sleep 1\n"
        script_content += "echo configure terminal\n"
        script_content += "sleep 1\n"
        
        for cmd in commands:
            script_content += f"echo {cmd}\n"
            script_content += "sleep 0.5\n"
        
        script_content += "echo end\n"
        script_content += "sleep 1\n"
        script_content += "echo write memory\n"
        script_content += "sleep 2\n"
        script_content += "echo exit\n"
        
        # Write to file
        import tempfile
        import os
        fd, script_path = tempfile.mkstemp(suffix='.sh', text=True)
        os.write(fd, script_content.encode())
        os.close(fd)
        os.chmod(script_path, 0o755)
        
        # Execute the script
        telnet_cmd = f"{script_path} | telnet {device.host} {device.port} 2>&1"
        result = subprocess.run(telnet_cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        # Clean up
        os.unlink(script_path)
        
        return JsonResponse({
            'success': True,
            'message': 'Configuration deployed',
            'output': result.stdout[:500]
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })