"""
Management command to test connection to a switch.
Usage: python manage.py test_switch --device-id 1
"""

# Django's management command base class
from django.core.management.base import BaseCommand

# Import our helper functions
from devices.netmiko_helper import get_vlans, get_interfaces
from devices.models import Device


class Command(BaseCommand):
    """
    This class defines the command.
    The name of the file (test_switch.py) becomes the command name.
    """
    
    # help text shown when running --help
    help = 'Test connection to a switch and display VLANs and interfaces'
    
    def add_arguments(self, parser):
        """
        Define command-line arguments.
        This allows: python manage.py test_switch --device-id 1
        """
        parser.add_argument(
            '--device-id',
            type=int,
            required=True,
            help='ID of the device in the database'
        )
    
    def handle(self, *args, **options):
        """
        This method runs when the command is executed.
        """
        
        # Get the device ID from command line
        device_id = options['device_id']
        
        # Retrieve the device from database
        try:
            device = Device.objects.get(id=device_id, is_active=True)
        except Device.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Device with id {device_id} not found'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Connecting to {device.name}...'))
        
        # Test 1: Get VLANs
        self.stdout.write('\n--- VLANs ---')
        vlans = get_vlans(device)
        
        if isinstance(vlans, list):
            for vlan in vlans[:10]:  # Show first 10 VLANs
                self.stdout.write(f"VLAN {vlan.get('vlan_id')}: {vlan.get('vlan_name')} ({vlan.get('status')})")
        else:
            self.stdout.write(self.style.ERROR(f'Error: {vlans}'))
        
        # Test 2: Get Interfaces
        self.stdout.write('\n--- Interfaces ---')
        interfaces = get_interfaces(device)
        
        if isinstance(interfaces, list):
            for interface in interfaces[:10]:  # Show first 10 interfaces
                self.stdout.write(f"{interface.get('port')}: {interface.get('status')} (VLAN {interface.get('vlan')})")
        else:
            self.stdout.write(self.style.ERROR(f'Error: {interfaces}'))
        
        self.stdout.write(self.style.SUCCESS('\nTest completed!'))