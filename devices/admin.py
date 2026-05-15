from django.contrib import admin
from .models import Device, Interface, Vlan

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['name', 'host', 'port', 'is_active']
    list_filter = ['is_active']

@admin.register(Interface)
class InterfaceAdmin(admin.ModelAdmin):
    list_display = ['device', 'name', 'status', 'vlan']

@admin.register(Vlan)
class VlanAdmin(admin.ModelAdmin):
    list_display = ['device', 'vlan_id', 'name', 'status']