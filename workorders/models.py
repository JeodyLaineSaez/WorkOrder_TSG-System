from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator
from django.utils import timezone

class User(AbstractUser):
    """Custom User model with role-based access"""
    USER_TYPE_CHOICES = [
        ('TSG_staff', 'TSG Staff'),
        ('standard_user', 'Standard User'),
    ]
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='standard_user')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def is_tsg_staff(self):
        return self.user_type == 'TSG_staff'
    
    def is_standard_user(self):
        return self.user_type == 'standard_user'

class Campus(models.Model):
    """Campus locations"""
    name = models.CharField(max_length=100, unique=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Office(models.Model):
    """Office locations within campuses"""
    name = models.CharField(max_length=100)
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name='offices')
    floor = models.CharField(max_length=10, blank=True, null=True)
    room_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['campus', 'name']
    
    def __str__(self):
        return f"{self.campus.name} - {self.name}"

class ComputerTechnician(models.Model):
    """Computer technicians who can be assigned to work orders"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='technician_profile')
    specialization = models.CharField(max_length=100, blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.specialization}"

class WorkOrder(models.Model):
    """Work order request model"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('on_going', 'On Going'),
        ('completed', 'Completed')
    ]
    
    TYPE_CHOICES = [
        ('desktop_laptop', 'Desktop/Laptop Computer'),
        ('printer', 'Printer'),
        ('scanner', 'Scanner'),
        ('lan_internet', 'LAN/Internet'),
        ('other', 'Others'),
    ]

    CATEGORY_CHOICES = [
        ('repair', 'Repair'),
        ('maintenance', 'Maintenance'),
        ('checkup', 'Checkup'),
    ]
    
    # Request details
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name='work_orders')
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='work_orders')
    item = models.CharField(max_length=200, validators=[MinLengthValidator(3)])
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='desktop_laptop')
    other_type = models.CharField(max_length=100, blank=True, null=True, help_text="Specify if type is Others")
    issue_description = models.TextField(validators=[MinLengthValidator(10)])
    serial_number = models.CharField(max_length=100, blank=True, null=True, help_text="Serial number of the item (optional)")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Repair')
    
    # Request metadata
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requested_work_orders')
    date_requested = models.DateField(default=timezone.now)
    
    # Assignment details (TSG Staff only)
    assigned_technician = models.ForeignKey(ComputerTechnician, on_delete=models.SET_NULL, 
                                         related_name='assigned_work_orders', null=True, blank=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                  related_name='assigned_work_orders', null=True, blank=True)
    date_assigned = models.DateTimeField(null=True, blank=True)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    remarks = models.TextField(max_length=150)
    date_completed = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                   related_name='completed_work_orders', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"WO-{self.id:06d} - {self.item} ({self.status})"
    
    def save(self, *args, **kwargs):
        # Auto-update date_assigned when technician is assigned
        if self.assigned_technician and not self.date_assigned:
            self.date_assigned = timezone.now()
        
        # Auto-update date_completed when status changes to completed
        if self.status == 'completed' and not self.date_completed:
            self.date_completed = timezone.now()
        
        super().save(*args, **kwargs)


class WorkOrderHistory(models.Model):
    """Track changes to work orders"""
    work_order = models.ForeignKey('WorkOrder', on_delete=models.CASCADE)
    changed_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)
    field_name = models.CharField(max_length=100)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.work_order} - {self.field_name} changed at {self.changed_at}"
