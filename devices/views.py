from django.shortcuts import render
from django.core.cache import cache
from .models import Device
from .telnet_helper import (
    get_interfaces, get_vlans, get_system_info,
    get_mac_table, get_cdp_neighbors, get_port_security, get_stp_info
)

CACHE_TIMEOUT = 300

def get_device_data(device):
    """Get all device data from cache or fresh"""
    cache_key = f"device_data_all_{device.id}"
    data = cache.get(cache_key)
    
    if data is None:
        try:
            vlans = get_vlans(device.host, device.port)
            interfaces = get_interfaces(device.host, device.port)
            system_info = get_system_info(device.host, device.port)
            mac_table = get_mac_table(device.host, device.port)
            cdp_neighbors = get_cdp_neighbors(device.host, device.port)
            port_security = get_port_security(device.host, device.port)
            stp_info = get_stp_info(device.host, device.port)
            
            data = {
                'device': device,
                'vlans': vlans,
                'interfaces': interfaces,
                'system_info': system_info,
                'mac_table': mac_table,
                'cdp_neighbors': cdp_neighbors,
                'port_security': port_security,
                'stp_info': stp_info,
                'error': None
            }
            cache.set(cache_key, data, CACHE_TIMEOUT)
        except Exception as e:
            data = {
                'device': device,
                'vlans': [],
                'interfaces': [],
                'system_info': {},
                'mac_table': [],
                'cdp_neighbors': [],
                'port_security': [],
                'stp_info': {},
                'error': str(e)
            }
    
    return data

def dashboard(request):
    """Dashboard view with multiple tabs"""
    devices = Device.objects.filter(is_active=True)
    devices_data = [get_device_data(device) for device in devices]
    
    context = {
        'devices_data': devices_data,
        'title': 'Network CDN Dashboard'
    }
    return render(request, 'devices/dashboard.html', context)