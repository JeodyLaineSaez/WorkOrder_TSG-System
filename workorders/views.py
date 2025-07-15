from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import User, WorkOrder, Campus, Office, ComputerTechnician
from .forms import (
    CustomUserCreationForm, CustomAuthenticationForm, WorkOrderForm,
    WorkOrderAssignmentForm, WorkOrderUpdateForm, CampusForm, OfficeForm,
    ComputerTechnicianForm, WorkOrderUserUpdateForm
)
from docxtpl import DocxTemplate
import os
from django import forms
from django.utils import dateformat

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

    context = {
        'total_work_orders': total_work_orders,
        'completed_work_orders': completed_work_orders,
        'pending_work_orders': pending_work_orders,
        'available_technicians': available_technicians,
        'page_obj': page_obj,
        'status_filter': status_filter,
    }

    return render(request, 'workorders/dashboard.html', context)

@login_required
def create_work_order_view(request):
    """Create new work order request"""
    if request.method == 'POST':
        form = WorkOrderForm(request.POST)
        if form.is_valid():
            work_order = form.save(commit=False)
            work_order.requested_by = request.user
            work_order.save()
            messages.success(request, 'Work order request created successfully!')
            return redirect('dashboard')
    else:
        form = WorkOrderForm()
    
    return render(request, 'workorders/create_work_order.html', {'form': form})

@login_required
@user_passes_test(is_tsg_staff)
def assign_work_order_view(request, work_order_id):
    """TSG staff can assign technicians to work orders"""
    work_order = get_object_or_404(WorkOrder, id=work_order_id)
    prev_technician = work_order.assigned_technician
    prev_status = work_order.status

    if request.method == 'POST':
        form = WorkOrderAssignmentForm(request.POST, instance=work_order)
        if form.is_valid():
            work_order = form.save(commit=False)
            work_order.assigned_by = request.user
            work_order.save()
            # If status is set to 'on_going', set technician unavailable
            if work_order.assigned_technician and work_order.status == 'on_going':
                work_order.assigned_technician.is_available = False
                work_order.assigned_technician.save()
            # If technician changed or status changed from on_going/completed, set previous technician available
            if prev_technician and prev_technician != work_order.assigned_technician and prev_status in ['on_going', 'completed']:
                prev_technician.is_available = True
                prev_technician.save()
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
            if request.user.is_tsg_staff() and work_order.status == 'completed':
                work_order.completed_by = request.user
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
    form = AccomplishmentReportForm(request.GET or None)
    work_orders = []
    if form.is_valid():
        date_started = form.cleaned_data['date_started']
        date_ended = form.cleaned_data['date_ended']
        work_orders = WorkOrder.objects.filter(
            assigned_technician__user=request.user,
            status='completed',
            date_completed__date__gte=date_started,
            date_completed__date__lte=date_ended
        ).order_by('date_completed')
    context = {
        'form': form,
        'work_orders': work_orders,
    }
    return render(request, 'workorders/manage_accomplishment_report.html', context)

@login_required
@user_passes_test(is_tsg_staff)
def export_accomplishment_report_view(request):
    form = AccomplishmentReportForm(request.GET or None)
    if not form.is_valid():
        messages.error(request, 'Please select a valid date range to export the report.')
        return redirect('manage_accomplishment_report')
    date_started = form.cleaned_data['date_started']
    date_ended = form.cleaned_data['date_ended']
    work_orders = WorkOrder.objects.filter(
        assigned_technician__user=request.user,
        status='completed',
        date_completed__date__gte=date_started,
        date_completed__date__lte=date_ended
    ).order_by('date_completed')

    # Prepare context for docxtpl
    table = []
    for wo in work_orders:
        table.append({
            'date_completed': dateformat.format(wo.date_completed, 'M d, Y H:i') if wo.date_completed else '',
            'issue_description': wo.issue_description,
            'requested_by': wo.requested_by.get_full_name(),
            'remarks': wo.remarks or '',
        })
    context = {
        'name': request.user.get_full_name().upper(),
        'date_started': date_started.strftime('%B %d, %Y'),
        'date_ended': date_ended.strftime('%B %d, %Y'),
        'date_today': timezone.now().strftime('%B %d, %Y'),
        'table': table,
    }
    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'ACCOMPLISHMENT_STAFF.docx')
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
        'wo_datetime_started': work_order.date_requested.strftime('%Y-%m-%d %H:%M'),
        'wo_equip_type': work_order.get_type_display() if hasattr(work_order, 'get_type_display') else work_order.type,
        'wo_description': work_order.issue_description,
        'wo_requested_by': work_order.requested_by.get_full_name(),
        'wo_status': work_order.get_status_display() if hasattr(work_order, 'get_status_display') else work_order.status,
        'wo_remark': work_order.remarks or '',
        'wo_datetime_completed': work_order.date_completed.strftime('%Y-%m-%d %H:%M') if work_order.date_completed else '',
        'wo_assigned_technician': work_order.assigned_technician.user.get_full_name() if work_order.assigned_technician else '',
    }
    doc.render(context)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename=work_order_{work_order.id}.docx'
    doc.save(response)
    return response
