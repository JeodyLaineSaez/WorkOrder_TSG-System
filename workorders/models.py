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
    
    def get_display_name(self):
        """Get the full name for display purposes"""
        full_name = self.get_full_name()
        if full_name.strip():
            return full_name
        return self.username

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
        return f"{self.user.get_display_name()} - {self.specialization}"
    
    def get_average_handling_time_hours(self):
        """Calculate average handling time in hours for completed work orders"""
        completed_status = WorkOrderStatus.objects.filter(name='completed').first()
        completed_work_orders = self.assigned_work_orders.filter(
            status=completed_status,
            date_completed__isnull=False,
            date_assigned__isnull=False
        )
        total_handling_time = 0
        count = 0
        
        for wo in completed_work_orders:
            handling_time = wo.get_handling_time_hours()
            if handling_time is not None:
                total_handling_time += handling_time
                count += 1
        
        if count > 0:
            return round(total_handling_time / count, 2)
        return 0
    
    def get_completed_work_orders_count(self):
        """Get count of completed work orders"""
        completed_status = WorkOrderStatus.objects.filter(name__iexact='completed').first()
        if completed_status:
            return self.assigned_work_orders.filter(status=completed_status).count()
        return 0
    
    def get_ongoing_work_orders_count(self):
        """Get count of ongoing work orders"""
        ongoing_status = WorkOrderStatus.objects.filter(name__iexact='on_going').first()
        if ongoing_status:
            return self.assigned_work_orders.filter(status=ongoing_status).count()
        return 0
    
    def is_currently_available(self):
        """Check if technician is currently available (no ongoing work orders and is_available=True)"""
        if not self.is_available:
            return False
        return self.get_ongoing_work_orders_count() == 0
    
    def get_current_work_orders(self):
        """Get all current work orders (pending and ongoing)"""
        pending_status = WorkOrderStatus.objects.filter(name='pending').first()
        ongoing_status = WorkOrderStatus.objects.filter(name='on_going').first()
        return self.assigned_work_orders.filter(status__in=[pending_status, ongoing_status])
    
    def get_availability_status(self):
        """Get detailed availability status"""
        if not self.is_available:
            return {
                'status': 'unavailable',
                'reason': 'Manually set to unavailable',
                'ongoing_count': 0
            }
        
        ongoing_count = self.get_ongoing_work_orders_count()
        if ongoing_count > 0:
            return {
                'status': 'busy',
                'reason': f'Has {ongoing_count} ongoing work order(s)',
                'ongoing_count': ongoing_count
            }
        else:
            return {
                'status': 'available',
                'reason': 'No ongoing work orders',
                'ongoing_count': 0
            }

class WorkOrderStatus(models.Model):
    """Status options for work orders"""
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Work Order Status'
        verbose_name_plural = 'Work Order Statuses'
        ordering = ['name']
    
    def __str__(self):
        return self.display_name
    
    def save(self, *args, **kwargs):
        if self.is_default:
            # Ensure only one default status exists
            WorkOrderStatus.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

class WorkOrderCategory(models.Model):
    """Categories for work orders"""
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Work Order Category'
        verbose_name_plural = 'Work Order Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.display_name

class WorkOrder(models.Model):
    """Work order request model"""
    TYPE_CHOICES = [
        ('desktop_laptop', 'Desktop/Laptop Computer'),
        ('printer', 'Printer'),
        ('scanner', 'Scanner'),
        ('lan_internet', 'LAN/Internet'),
        ('other', 'Others'),
    ]
    
    # Request details
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name='work_orders')
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='work_orders')
    item = models.CharField(max_length=200, validators=[MinLengthValidator(3)])
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='desktop_laptop')
    other_type = models.CharField(max_length=100, blank=True, null=True, help_text="Specify if type is Others")
    issue_description = models.TextField(validators=[MinLengthValidator(10)])
    serial_number = models.CharField(max_length=100, blank=True, null=True, help_text="Serial number of the item (optional)")
    category = models.ForeignKey(WorkOrderCategory, on_delete=models.PROTECT, related_name='work_orders')
    
    # Request metadata
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requested_work_orders')
    date_requested = models.DateTimeField(default=timezone.now)
    
    # Assignment details (TSG Staff only)
    assigned_technician = models.ForeignKey(ComputerTechnician, on_delete=models.SET_NULL, 
                                         related_name='assigned_work_orders', null=True, blank=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                  related_name='assigned_work_orders', null=True, blank=True)
    date_assigned = models.DateTimeField(null=True, blank=True)
    
    # Status and tracking
    status = models.ForeignKey(WorkOrderStatus, on_delete=models.PROTECT, related_name='work_orders')
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
        # Auto-update date_assigned when technician is assigned (Philippine time)
        if self.assigned_technician and not self.date_assigned:
            self.date_assigned = timezone.now()
        
        # Auto-update date_completed when status changes to completed (Philippine time)
        if self.status and self.status.name == 'completed' and not self.date_completed:
            self.date_completed = timezone.now()
        
        super().save(*args, **kwargs)
    
    def get_handling_time_hours(self):
        """Calculate handling time in hours from assignment to completion"""
        if self.date_completed and self.date_assigned:
            handling_time = self.date_completed - self.date_assigned
            return round(handling_time.total_seconds() / 3600, 2)
        return None
    
    def get_total_time_hours(self):
        """Calculate total time in hours from request to completion"""
        if self.date_completed and self.date_requested:
            total_time = self.date_completed - self.date_requested
            return round(total_time.total_seconds() / 3600, 2)
        return None


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