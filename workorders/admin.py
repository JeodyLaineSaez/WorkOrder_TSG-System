from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Campus, Office, ComputerTechnician, WorkOrder, WorkOrderHistory,
    WorkOrderStatus, WorkOrderCategory
)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone_number', 'department')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone_number', 'department')}),
    )

@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'created_at')
    search_fields = ('name', 'address')
    ordering = ('name',)

@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ('name', 'campus', 'floor', 'room_number', 'created_at')
    list_filter = ('campus', 'floor')
    search_fields = ('name', 'campus__name')
    ordering = ('campus__name', 'name')

@admin.register(ComputerTechnician)
class ComputerTechnicianAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'is_available', 'created_at')
    list_filter = ('is_available', 'specialization')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specialization')
    ordering = ('user__first_name', 'user__last_name')

@admin.register(WorkOrderStatus)
class WorkOrderStatusAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'name', 'is_default', 'created_at')
    search_fields = ('name', 'display_name')
    list_filter = ('is_default', 'created_at')
    ordering = ('name',)

    def get_readonly_fields(self, request, obj=None):
        if not (request.user.is_superuser or request.user.is_tsg_staff()):
            return ('name', 'display_name', 'is_default', 'created_at')
        return ('created_at',)

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.is_tsg_staff()

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_tsg_staff()

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_tsg_staff()

@admin.register(WorkOrderCategory)
class WorkOrderCategoryAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'name', 'description', 'created_at')
    search_fields = ('name', 'display_name', 'description')
    ordering = ('name',)

    def get_readonly_fields(self, request, obj=None):
        if not (request.user.is_superuser or request.user.is_tsg_staff()):
            return ('name', 'display_name', 'description', 'created_at')
        return ('created_at',)

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.is_tsg_staff()

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_tsg_staff()

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_tsg_staff()

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'campus', 'office', 'requested_by', 'status', 'assigned_technician', 'date_requested')
    list_filter = ('status', 'type', 'campus', 'date_requested')
    search_fields = ('item', 'issue_description', 'requested_by__username', 'assigned_technician__user__username')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    def get_readonly_fields(self, request, obj=None):
        """Make date_assigned editable for TSG staff and superusers"""
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if not (request.user.is_superuser or request.user.is_tsg_staff()):
            readonly_fields.append('date_assigned')
        return readonly_fields
    
    fieldsets = (
        ('Request Information', {
            'fields': ('campus', 'office', 'item', 'type', 'other_type', 'issue_description', 'category')
        }),
        ('Request Details', {
            'fields': ('requested_by', 'date_requested')
        }),
        ('Assignment', {
            'fields': ('assigned_technician', 'assigned_by', 'date_assigned')
        }),
        ('Status', {
            'fields': ('status', 'remarks', 'date_completed', 'completed_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(WorkOrderHistory)
class WorkOrderHistoryAdmin(admin.ModelAdmin):
    list_display = ('work_order', 'changed_by', 'field_name', 'changed_at')
    list_filter = ('field_name', 'changed_at')
    search_fields = ('work_order__item', 'changed_by__username')
    readonly_fields = ('work_order', 'changed_by', 'field_name', 'old_value', 'new_value', 'changed_at')
    ordering = ('-changed_at',)
