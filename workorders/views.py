from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import User, WorkOrder, Campus, Office, ComputerTechnician, WorkOrderHistory
from .forms import (
    CustomUserCreationForm, CustomAuthenticationForm, WorkOrderForm,
    WorkOrderAssignmentForm, WorkOrderUpdateForm, CampusForm, OfficeForm,
    ComputerTechnicianForm, WorkOrderUserUpdateForm
)
from docxtpl import DocxTemplate
import os
from django import forms
from django.utils import dateformat
import csv
from django.utils.encoding import smart_str
from datetime import timedelta
import pytz

def format_philippine_time(datetime_obj):
    """Format datetime object to Philippine time with AM/PM"""
    if datetime_obj:
        # Convert to Philippine time (UTC+8)
        ph_tz = pytz.timezone('Asia/Manila')
        if datetime_obj.tzinfo is None:
            # If naive datetime, assume it's in UTC and convert
            utc_tz = pytz.UTC
            datetime_obj = utc_tz.localize(datetime_obj)
        ph_time = datetime_obj.astimezone(ph_tz)
        return ph_time.strftime('%B %d, %Y at %I:%M %p')  # e.g., "July 29, 2025 at 02:30 PM"
    return ''

class AccomplishmentReportForm(forms.Form):
    date_started = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    date_ended = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

def is_tsg_staff(user):
    """Check if user is TSG staff"""
    return user.is_authenticated and user.is_tsg_staff()

def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'workorders/register.html', {'form': form})

def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
                return redirect('dashboard')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'workorders/login.html', {'form': form})

@login_required
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

@login_required
def dashboard_view(request):
    """Dashboard view with statistics and work order list"""
    # Get statistics
    total_work_orders = WorkOrder.objects.count()
    completed_work_orders = WorkOrder.objects.filter(status='completed').count()
    pending_work_orders = WorkOrder.objects.filter(status='pending').count()
    available_technicians = ComputerTechnician.objects.filter(is_available=True).count()

    # Show all work orders to all users, but exclude completed unless specifically filtered
    work_orders = WorkOrder.objects.all()
    status_filter = request.GET.get('status')
    if status_filter:
        work_orders = work_orders.filter(status=status_filter)
    else:
        work_orders = work_orders.exclude(status='completed')

    # Pagination
    paginator = Paginator(work_orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get pending work orders for alert notification
    pending_work_orders_list = WorkOrder.objects.filter(status='pending').order_by('date_requested')
    
    context = {
        'total_work_orders': total_work_orders,
        'completed_work_orders': completed_work_orders,
        'pending_work_orders': pending_work_orders,
        'available_technicians': available_technicians,
        'page_obj': page_obj,
        'status_filter': status_filter,
        'pending_work_orders_list': pending_work_orders_list,
    }

    # Date filtering
    period = request.GET.get("period", "week")
    today = timezone.now().date()

    if period == "month":
        start_date = today.replace(day=1)
        end_date = today
    elif period == "year":
        start_date = today.replace(month=1, day=1)
        end_date = today
    else:  # default to week
        start_date = today - timedelta(days=6)  # Last 7 days including today
        end_date = today

    # Technician filter
    technician_id = request.GET.get("technician", "all")
    all_technicians = ComputerTechnician.objects.select_related('user').all()
    context["all_technicians"] = all_technicians
    context["selected_technician"] = technician_id

    # Get selected technician name for display
    selected_technician_name = "All Technicians"
    if technician_id != "all":
        try:
            selected_tech = all_technicians.get(id=int(technician_id))
            selected_technician_name = selected_tech.user.get_display_name()
        except (ValueError, ComputerTechnician.DoesNotExist):
            selected_technician_name = "All Technicians"
            technician_id = "all"  # Reset to all if invalid technician ID

    context["selected_technician_name"] = selected_technician_name

    # Get work orders for the period
    start_datetime = timezone.make_aware(timezone.datetime.combine(start_date, timezone.datetime.min.time()))
    end_datetime = timezone.make_aware(timezone.datetime.combine(end_date, timezone.datetime.max.time()))
    work_orders = WorkOrder.objects.filter(date_requested__gte=start_datetime, date_requested__lte=end_datetime)
    if technician_id != "all":
        work_orders = work_orders.filter(assigned_technician_id=technician_id)

    # Generate all dates in the period
    from datetime import date
    all_dates = []
    current_date = start_date
    while current_date <= end_date:
        all_dates.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)

    # Initialize chart data with all dates and zero values
    chart_data = {}
    if technician_id == "all":
        # For all technicians, create entries for each technician
        for tech in all_technicians:
            tech_name = tech.user.get_display_name()
            chart_data[tech_name] = {}
            for date_str in all_dates:
                chart_data[tech_name][date_str] = {"pending": 0, "on_going": 0, "completed": 0}
    else:
        # For specific technician
        chart_data[selected_technician_name] = {}
        for date_str in all_dates:
            chart_data[selected_technician_name][date_str] = {"pending": 0, "on_going": 0, "completed": 0}

    # Populate chart data with actual work order counts
    for status in ['pending', 'on_going', 'completed']:
        status_qs = work_orders.filter(status=status)
        for wo in status_qs:
            date_str = wo.date_requested.strftime('%Y-%m-%d')
            if wo.assigned_technician:
                tech_name = wo.assigned_technician.user.get_display_name()
            else:
                tech_name = "Unassigned"
            
            # Add to chart data
            if technician_id == "all":
                if tech_name in chart_data:
                    chart_data[tech_name][date_str][status] += 1
            else:
                if selected_technician_name in chart_data:
                    chart_data[selected_technician_name][date_str][status] += 1

    # Calculate average handling time per technician
    avg_handling_times = {}
    
    if technician_id == "all":
        # Calculate for all technicians
        for tech in all_technicians:
            tech_name = tech.user.get_display_name()
            avg_handling_times[tech_name] = tech.get_average_handling_time_hours()
    else:
        # Calculate for specific technician
        try:
            selected_tech = all_technicians.get(id=int(technician_id))
            avg_handling_times[selected_technician_name] = selected_tech.get_average_handling_time_hours()
        except (ValueError, ComputerTechnician.DoesNotExist):
            avg_handling_times = {}

    # Calculate work order distribution by category
    category_data = {}
    for category_code, category_name in WorkOrder.CATEGORY_CHOICES:
        count = work_orders.filter(category=category_code).count()
        if count > 0:
            category_data[category_name] = count
    
    # Calculate work order distribution by office
    office_data = {}
    office_counts = work_orders.values('office__name').annotate(count=Count('id')).order_by('-count')
    for office in office_counts:
        if office['count'] > 0:
            office_data[office['office__name']] = office['count']
    
    context["chart_data"] = chart_data
    context["period"] = period
    context["all_dates"] = all_dates
    context["avg_handling_times"] = avg_handling_times
    context["category_data"] = category_data
    context["office_data"] = office_data
    
    # Debug information
    context["debug_technician_id"] = technician_id
    context["debug_technician_name"] = selected_technician_name
    
    return render(request, 'workorders/dashboard.html', context)

@login_required
def create_work_order_view(request):
    """Create new work order request"""
    if request.method == 'POST':
        form = WorkOrderForm(request.POST)
        if form.is_valid():
            work_order = form.save(commit=False)
            work_order.requested_by = request.user
            work_order.date_requested = timezone.now()  # Save Philippine time when request is submitted
            work_order.save()
            messages.success(request, 'Work order request created successfully!')
            return redirect('dashboard')
    else:
        form = WorkOrderForm()
    
    return render(request, 'workorders/create_work_order.html', {'form': form})

@login_required
@user_passes_test(is_tsg_staff)
def assign_work_order_view(request, work_order_id):
    """TSG staff can assign technicians to work orders. Once assigned, technician cannot be changed."""
    work_order = get_object_or_404(WorkOrder, id=work_order_id)

    # If already assigned, do not allow editing
    if work_order.assigned_technician:
        messages.info(request, 'Technician has already been assigned to this work order and cannot be changed.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = WorkOrderAssignmentForm(request.POST, instance=work_order)
        if form.is_valid():
            work_order = form.save(commit=False)
            work_order.assigned_by = request.user
            work_order.save()
            messages.success(request, 'Work order assigned successfully!')
            return redirect('dashboard')
    else:
        form = WorkOrderAssignmentForm(instance=work_order)

    return render(request, 'workorders/assign_work_order.html', {
        'form': form,
        'work_order': work_order
    })

@login_required
def update_work_order_view(request, work_order_id):
    """Update work order status and details"""
    work_order = get_object_or_404(WorkOrder, id=work_order_id)
    prev_status = work_order.status

    # --- BEGIN: Track original values for change history ---
    original_values = {}
    tracked_fields = [
        'campus', 'office', 'item', 'type', 'other_type', 'issue_description', 'serial_number', 'category',
        'assigned_technician', 'assigned_by', 'date_assigned', 'status', 'remarks', 'date_completed', 'completed_by'
    ]
    for field in tracked_fields:
        value = getattr(work_order, field)
        # For ForeignKey fields, store the pk (or None)
        if hasattr(value, 'pk'):
            original_values[field] = value.pk if value else None
        else:
            original_values[field] = value
    # --- END: Track original values for change history ---

    if request.user.is_tsg_staff():
        form_class = WorkOrderUpdateForm
    else:
        # Only allow standard user to edit their own work order
        if work_order.requested_by != request.user:
            messages.error(request, 'You can only edit your own work order requests.')
            return redirect('dashboard')
        form_class = WorkOrderUserUpdateForm

    if request.method == 'POST':
        form = form_class(request.POST, instance=work_order)
        if form.is_valid():
            work_order = form.save(commit=False)
            
            # Handle TSG staff specific updates
            if request.user.is_tsg_staff():
                # Update date_requested if provided
                if 'date_requested' in form.cleaned_data and form.cleaned_data['date_requested']:
                    work_order.date_requested = form.cleaned_data['date_requested']
                
                # Update requested_by if requested_by_name is changed
                if 'requested_by_name' in form.cleaned_data:
                    requested_by_name = form.cleaned_data['requested_by_name'].strip()
                    if requested_by_name:
                        # Try to find a user with this full name, else create a new user
                        first_name, *last_name = requested_by_name.split(' ', 1)
                        last_name = last_name[0] if last_name else ''
                        user_qs = User.objects.filter(first_name=first_name, last_name=last_name)
                        if user_qs.exists():
                            work_order.requested_by = user_qs.first()
                        else:
                            # Create a new user with a unique username
                            from django.utils.text import slugify
                            base_username = slugify(f"{first_name}{last_name}")[:30]
                            username = base_username
                            counter = 1
                            while User.objects.filter(username=username).exists():
                                username = f"{base_username}{counter}"
                                counter += 1
                            new_user = User.objects.create(
                                username=username,
                                first_name=first_name,
                                last_name=last_name,
                                user_type='standard_user',
                            )
                            work_order.requested_by = new_user
                
                # Set completed_by if status is completed
                if work_order.status == 'completed':
                    work_order.completed_by = request.user
                    work_order.date_completed = timezone.now()
            else:
                # For standard users, prevent date_requested/requested_by from being changed
                work_order.date_requested = work_order.__class__.objects.get(pk=work_order.pk).date_requested
                work_order.requested_by = work_order.__class__.objects.get(pk=work_order.pk).requested_by
                # If status is set to completed, set date_completed to Philippine time
                if work_order.status == 'completed':
                    work_order.date_completed = timezone.now()
            
            # --- BEGIN: Compare and record changes ---
            for field in tracked_fields:
                old = original_values[field]
                new = getattr(work_order, field)
                # For ForeignKey fields, compare pk
                if hasattr(new, 'pk'):
                    new_val = new.pk if new else None
                else:
                    new_val = new
                if old != new_val:
                    # For display, get readable values for FKs
                    model_field = work_order._meta.get_field(field)
                    related_model = getattr(model_field, 'related_model', None)
                    if related_model is not None:
                        old_obj = related_model.objects.filter(pk=old).first() if old else None
                        new_obj = related_model.objects.filter(pk=new_val).first() if new_val else None
                        if field in ['assigned_by', 'completed_by']:
                            old_disp = old_obj.username if old_obj else ''
                            new_disp = new_obj.username if new_obj else ''
                        elif field in ['assigned_technician']:
                            old_disp = str(old_obj) if old_obj else ''
                            new_disp = str(new_obj) if new_obj else ''
                        else:
                            old_disp = getattr(old_obj, 'name', str(old_obj)) if old_obj else ''
                            new_disp = getattr(new_obj, 'name', str(new_obj)) if new_obj else ''
                    else:
                        old_disp = old
                        new_disp = new_val
                    WorkOrderHistory.objects.create(
                        work_order=work_order,
                        changed_by=request.user,
                        field_name=field,
                        old_value=old_disp,
                        new_value=new_disp,
                    )
            # --- END: Compare and record changes ---
            
            work_order.save()
            # If status changed to completed, set technician available
            if work_order.assigned_technician and prev_status != 'completed' and work_order.status == 'completed':
                work_order.assigned_technician.is_available = True
                work_order.assigned_technician.save()
            # If status changed to on_going, set technician unavailable
            if work_order.assigned_technician and prev_status != 'on_going' and work_order.status == 'on_going':
                work_order.assigned_technician.is_available = False
                work_order.assigned_technician.save()
            messages.success(request, 'Work order updated successfully!')
            return redirect('dashboard')
    else:
        form = form_class(instance=work_order)

    return render(request, 'workorders/update_work_order.html', {
        'form': form,
        'work_order': work_order
    })

@login_required
def work_order_detail_view(request, work_order_id):
    """View work order details (all users can view any work order)"""
    work_order = get_object_or_404(WorkOrder, id=work_order_id)
    return render(request, 'workorders/work_order_detail.html', {
        'work_order': work_order
    })

@login_required
@user_passes_test(is_tsg_staff)
def manage_campuses_view(request):
    """Manage campus locations"""
    campuses = Campus.objects.all()
    
    if request.method == 'POST':
        form = CampusForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Campus added successfully!')
            return redirect('manage_campuses')
    else:
        form = CampusForm()
    
    return render(request, 'workorders/manage_campuses.html', {
        'campuses': campuses,
        'form': form
    })

@login_required
@user_passes_test(is_tsg_staff)
def manage_offices_view(request):
    """Manage office locations"""
    offices = Office.objects.select_related('campus').all()
    
    if request.method == 'POST':
        form = OfficeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Office added successfully!')
            return redirect('manage_offices')
    else:
        form = OfficeForm()
    
    return render(request, 'workorders/manage_offices.html', {
        'offices': offices,
        'form': form
    })

@login_required
@user_passes_test(is_tsg_staff)
def manage_technicians_view(request):
    """Manage computer technicians"""
    technicians = ComputerTechnician.objects.select_related('user').all()
    
    if request.method == 'POST':
        form = ComputerTechnicianForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Technician added successfully!')
            return redirect('manage_technicians')
    else:
        form = ComputerTechnicianForm()
    
    return render(request, 'workorders/manage_technicians.html', {
        'technicians': technicians,
        'form': form
    })

@login_required
@user_passes_test(is_tsg_staff)
def manage_users_view(request):
    """Manage user accounts"""
    users = User.objects.all()
    return render(request, 'workorders/manage_users.html', {'users': users})

@login_required
@user_passes_test(is_tsg_staff)
def manage_accomplishment_report_view(request):
    """Manage accomplishment report with date filter (no AccomplishmentReportForm)"""
    from .models import WorkOrder, ComputerTechnician
    work_orders = WorkOrder.objects.filter(status='completed')
    date_started = request.GET.get('date_started')
    date_ended = request.GET.get('date_ended')
    technician_id = request.GET.get('technician')
    if date_started and date_ended:
        work_orders = work_orders.filter(date_requested__range=[date_started, date_ended])
    if technician_id:
        work_orders = work_orders.filter(assigned_technician_id=technician_id)
    
    # Order by work order number (ID) from past to current date completed
    work_orders = work_orders.order_by('id')
    
    # --- CHANGE: Only show current user's ComputerTechnician and 'All Technicians' if TSG staff ---
    if request.user.is_tsg_staff():
        user_tech = ComputerTechnician.objects.filter(user=request.user)
        if user_tech.exists():
            technicians = list(user_tech)
        else:
            technicians = []
        # Add a dummy for 'All Technicians' (handled in template)
        show_all = True
    else:
        technicians = []
        show_all = False
    return render(request, 'workorders/manage_accomplishment_report.html', {
        'work_orders': work_orders,
        'technicians': technicians,
        'show_all': show_all,
    })

@login_required
@user_passes_test(is_tsg_staff)
def export_accomplishment_report_view(request):
    form = AccomplishmentReportForm(request.GET or None)
    if not form.is_valid():
        messages.error(request, 'Please select a valid date range to export the report.')
        return redirect('manage_accomplishment_report')
    date_started = form.cleaned_data['date_started']
    date_ended = form.cleaned_data['date_ended']
    technician_id = request.GET.get('technician')
    work_orders = WorkOrder.objects.filter(
        status='completed',
        date_completed__date__gte=date_started,
        date_completed__date__lte=date_ended
    )
    if technician_id:
        work_orders = work_orders.filter(assigned_technician_id=technician_id)
    # Order by work order number (ID) from past to current date completed
    work_orders = work_orders.order_by('id')
    
    table = []
    for wo in work_orders:
        table.append({
            'date_completed': format_philippine_time(wo.date_completed),
            'category': wo.get_category_display(),
            'issue_description': wo.issue_description,
            'requested_by': wo.requested_by.get_full_name(),
            'remarks': wo.remarks or '',
        })
    # --- CHANGE: Use different template and context for TSG head if all technicians selected ---
    if not technician_id:
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'ACCOMPLISHMENT_HEAD.docx')
        context = {
            'date_started': date_started.strftime('%B %d, %Y'),
            'date_ended': date_ended.strftime('%B %d, %Y'),
            'date_today': format_philippine_time(timezone.now()),
            'table': table,
        }
    else:
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'ACCOMPLISHMENT_STAFF.docx')
        context = {
            'name': request.user.get_full_name().upper(),
            'date_started': date_started.strftime('%B %d, %Y'),
            'date_ended': date_ended.strftime('%B %d, %Y'),
            'date_today': format_philippine_time(timezone.now()),
            'table': table,
        }
    doc = DocxTemplate(template_path)
    doc.render(context)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename=accomplishment_report_{date_started}_{date_ended}.docx'
    doc.save(response)
    return response

# AJAX views for dynamic form updates
@login_required
def get_offices_by_campus(request):
    """Get offices for a specific campus via AJAX"""
    campus_id = request.GET.get('campus_id')
    offices = Office.objects.filter(campus_id=campus_id).values('id', 'name')
    return JsonResponse({'offices': list(offices)})

@require_POST
@login_required
@user_passes_test(is_tsg_staff)
def delete_work_order_view(request, work_order_id):
    """Delete work order (TSG staff only)"""
    work_order = get_object_or_404(WorkOrder, id=work_order_id)
    work_order.delete()
    messages.success(request, 'Work order deleted successfully!')
    return redirect('dashboard')

def export_work_order_view(request, work_order_id):
    """Export a work order as a filled DOCX template"""
    work_order = get_object_or_404(WorkOrder, id=work_order_id)
    # Permission: Only TSG staff or the user who requested can export
    if not request.user.is_tsg_staff() and work_order.requested_by != request.user:
        messages.error(request, 'You do not have permission to export this work order.')
        return redirect('dashboard')

    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'WORK ORDER REQUEST.docx')
    doc = DocxTemplate(template_path)

    context = {
        'wo_campus': work_order.campus.name,
        'wo_office': work_order.office.name,
        'wo_datetime_started': format_philippine_time(work_order.date_requested),
        'wo_equip_type': work_order.get_type_display() if hasattr(work_order, 'get_type_display') else work_order.type,
        'wo_description': work_order.issue_description,
        'wo_requested_by': work_order.requested_by.get_full_name(),
        'wo_category': work_order.get_category_display() if hasattr(work_order, 'get_category_display') else work_order.category,
        'wo_remark': work_order.remarks or '',
        'wo_datetime_completed': format_philippine_time(work_order.date_completed),
        'wo_assigned_technician': work_order.assigned_technician.user.get_full_name() if work_order.assigned_technician else '',
        'wo': work_order,
        'action_taken': work_order.get_category_display(),
    }
    doc.render(context)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename=work_order_{work_order.id}.docx'
    doc.save(response)
    return response

@login_required
@user_passes_test(is_tsg_staff)
def edit_technician_view(request, technician_id):
    technician = get_object_or_404(ComputerTechnician, id=technician_id)
    if request.method == 'POST':
        form = ComputerTechnicianForm(request.POST, instance=technician)
        if form.is_valid():
            form.save()
            messages.success(request, 'Technician updated successfully!')
            return redirect('manage_technicians')
    else:
        form = ComputerTechnicianForm(instance=technician)
    return render(request, 'workorders/edit_technician.html', {'form': form, 'technician': technician})

@login_required
@user_passes_test(is_tsg_staff)
def edit_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully!')
            return redirect('manage_users')
    else:
        form = CustomUserCreationForm(instance=user)
    return render(request, 'workorders/edit_user.html', {'form': form, 'user_obj': user})

@login_required
@user_passes_test(is_tsg_staff)
def edit_office_view(request, office_id):
    office = get_object_or_404(Office, id=office_id)
    if request.method == 'POST':
        form = OfficeForm(request.POST, instance=office)
        if form.is_valid():
            form.save()
            messages.success(request, 'Office updated successfully!')
            return redirect('manage_offices')
    else:
        form = OfficeForm(instance=office)
    return render(request, 'workorders/edit_office.html', {'form': form, 'office': office})

@login_required
def export_work_orders_csv_view(request):
    """Export all work orders (pending, on_going, completed) as CSV, filtered by date_requested if date_started and date_ended are provided"""
    # --- CHANGE: Filter by date_requested if date_started and date_ended are provided ---
    work_orders = WorkOrder.objects.filter(status__in=['pending', 'on_going', 'completed']).order_by('id')
    date_started = request.GET.get('date_started')
    date_ended = request.GET.get('date_ended')
    if date_started and date_ended:
        work_orders = work_orders.filter(date_requested__range=[date_started, date_ended])
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=work_orders.csv'
    writer = csv.writer(response)
    writer.writerow([
        'Work Order ID', 'Campus', 'Office', 'Type', 'Item', 'Serial Number', 'Issue Description',
        'Requested By', 'Date Requested (PHT)', 'Assigned Technician', 'Category', 'Remarks', 'Date Completed (PHT)', 'Status'
    ])
    for wo in work_orders:
        writer.writerow([
            f'WO-{wo.id:06d}',
            smart_str(wo.campus.name),
            smart_str(wo.office.name),
            smart_str(wo.get_type_display() if hasattr(wo, 'get_type_display') else wo.type),
            smart_str(wo.item),
            smart_str(wo.serial_number or ''),
            smart_str(wo.issue_description),
            smart_str(wo.requested_by.get_full_name() if wo.requested_by else ''),
            format_philippine_time(wo.date_requested),
            smart_str(wo.assigned_technician.user.get_full_name() if wo.assigned_technician else ''),
            smart_str(wo.get_category_display() if hasattr(wo, 'get_category_display') else wo.category),
            smart_str(wo.remarks or ''),
            format_philippine_time(wo.date_completed),
            smart_str(wo.get_status_display() if hasattr(wo, 'get_status_display') else wo.status),
        ])
    return response
