from django.core.management.base import BaseCommand
from django.core.cache import cache
from devices.views import get_device_data
from devices.models import Device

class Command(BaseCommand):
    help = 'Preload device data into cache'

    def handle(self, *args, **options):
        devices = Device.objects.filter(is_active=True)
        for device in devices:
            self.stdout.write(f"Loading data for {device.name}...")
            get_device_data(device)
        self.stdout.write(self.style.SUCCESS('Cache preloaded successfully!'))