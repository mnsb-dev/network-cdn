# Import the models module from Django
# models contains classes for defining database tables
from django.db import models

# A "model" is a Python class that represents a database table
# Each attribute of the class becomes a column in the database

class Device(models.Model):
    """
    This model represents a network device (switch, router, etc.)
    Each device you want to manage will have one record in this table
    """
    
    # CharField = text field with limited length (max 100 characters)
    # unique=True means no two devices can have the same name
    name = models.CharField(max_length=100, unique=True)
    
    # GenericIPAddressField stores IPv4 or IPv6 addresses
    # default='localhost' means if not specified, use localhost
    host = models.GenericIPAddressField(default='localhost')
    
    # IntegerField stores whole numbers
    # default=5000 (GNS3 typically uses ports starting at 5000)
    port = models.IntegerField(default=5000)
    
    # CharField for the connection type (e.g., 'cisco_ios_telnet')
    device_type = models.CharField(max_length=50, default='cisco_ios_telnet')
    
    # blank=True means this field can be empty in forms
    username = models.CharField(max_length=50, blank=True)
    
    # CharField for password (in production, use encryption)
    password = models.CharField(max_length=100)
    
    # Enable password for privileged mode on Cisco devices
    enable_password = models.CharField(max_length=100, blank=True)
    
    # BooleanField = True/False
    # default=True means device is active unless marked inactive
    is_active = models.BooleanField(default=True)
    
    # DateTimeField automatically set when record is created
    auto_now_add=True #sets timestamp only on creation, never updates
    created_at = models.DateTimeField(auto_now_add=True)
    
    # The __str__ method defines how the object appears in admin interface
    def __str__(self):
        return self.name


class Interface(models.Model):
    """
    This model represents a network interface (port) on a device
    Each interface belongs to one device (ForeignKey relationship)
    """
    
    # ForeignKey creates a relationship: each Interface belongs to one Device
    # on_delete=models.CASCADE means: if the Device is deleted, delete all its Interfaces
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    
    # Interface name (e.g., 'GigabitEthernet0/1')
    name = models.CharField(max_length=50)
    
    # Port status: up, down, administratively down, etc.
    status = models.CharField(max_length=20)
    
    # VLAN assigned to this interface (e.g., '10', '1')
    vlan = models.CharField(max_length=20, blank=True)
    
    # Optional description (e.g., 'Uplink to Core Switch')
    description = models.CharField(max_length=200, blank=True)
    
    # DateTimeField that updates every time the record is saved
    auto_now=True #sets timestamp on every save (creation AND updates)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.device.name} - {self.name}"


class Vlan(models.Model):
    """
    This model represents a VLAN (Virtual Local Area Network)
    Each VLAN belongs to one device
    """
    
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    
    # VLAN ID number (1-4095 on most switches)
    vlan_id = models.IntegerField()
    
    # VLAN name (e.g., 'Engineering', 'HR')
    name = models.CharField(max_length=50)
    
    # VLAN status: active, suspend, etc.
    status = models.CharField(max_length=20)
    
    # Meta class contains additional configuration for the model
    class Meta:
        # unique_together ensures a device cannot have two VLANs with the same ID
        unique_together = ['device', 'vlan_id']
    
    def __str__(self):
        return f"VLAN {self.vlan_id}: {self.name}"