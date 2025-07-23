from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from .models import User, WorkOrder, Campus, Office, ComputerTechnician, WorkOrderHistory

class CustomUserCreationForm(UserCreationForm):
    """Custom user registration form"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    department = forms.CharField(max_length=100, required=False)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 
                 'department', 'user_type', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_type'].widget = forms.Select(choices=[
            ('standard_user', 'Standard User'),
            ('TSG_staff', 'TSG Staff'),
        ])
        self.fields['user_type'].initial = 'standard_user'

class CustomAuthenticationForm(AuthenticationForm):
    """Custom login form"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )

class WorkOrderForm(forms.ModelForm):
    """Form for creating work order requests"""
    campus = forms.ModelChoiceField(
        queryset=Campus.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select Campus"
    )
    office = forms.ModelChoiceField(
        queryset=Office.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select Office"
    )
    type = forms.ChoiceField(
        choices=WorkOrder.TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_type'}),
        label='Type',
    )
    other_type = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Please specify', 'id': 'id_other_type', 'style': 'display:none;'}),
        label='If Others, please specify',
    )
    serial_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Serial Number (optional)'}),
        label='Serial Number',
    )
    category = forms.ChoiceField(
        choices=WorkOrder.CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='repair',
        label='Category',
        required=True,
    )
    
    class Meta:
        model = WorkOrder
        fields = ['campus', 'office', 'item', 'type', 'other_type', 'serial_number', 'category', 'issue_description']
        widgets = {
            'item': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Computer, Printer, Network Device'}),
            'issue_description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Please describe the issue in detail...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'campus' in self.data:
            try:
                campus_id = int(self.data.get('campus'))
                self.fields['office'].queryset = Office.objects.filter(campus_id=campus_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.campus:
            self.fields['office'].queryset = self.instance.campus.offices.all()

class WorkOrderAssignmentForm(forms.ModelForm):
    """Form for TSG staff to assign technicians to work orders (no remarks field)"""
    assigned_technician = forms.ModelChoiceField(
        queryset=ComputerTechnician.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select Technician",
        required=True
    )
    status = forms.ChoiceField(
        choices=WorkOrder.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )

    class Meta:
        model = WorkOrder
        fields = ['assigned_technician', 'status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If a technician is already assigned, disable the field to prevent reassignment
        if self.instance and self.instance.pk and self.instance.assigned_technician:
            self.fields['assigned_technician'].disabled = True

class WorkOrderUpdateForm(forms.ModelForm):
    """Form for updating work order status and details"""
    remarks = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=True
    )
    date_requested = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False
    )
    requested_by_name = forms.CharField(
        label='Requested By (Name)',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Edit requested by name'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['requested_by_name'].initial = self.instance.requested_by.get_full_name() if self.instance.requested_by else ''

    def clean_date_requested(self):
        date_requested = self.cleaned_data['date_requested']
        from django.utils import timezone
        today = timezone.now().date()
        if date_requested and date_requested < today:
            raise forms.ValidationError('Date requested cannot be set before today (%s).' % today.strftime('%B %d, %Y'))
        return date_requested

    class Meta:
        model = WorkOrder
        fields = ['status', 'remarks', 'date_requested']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class WorkOrderUserUpdateForm(forms.ModelForm):
    campus = forms.ModelChoiceField(
        queryset=Campus.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select Campus"
    )
    office = forms.ModelChoiceField(
        queryset=Office.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select Office"
    )
    type = forms.ChoiceField(
        choices=WorkOrder.TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_type'}),
        label='Type',
    )
    other_type = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Please specify', 'id': 'id_other_type', 'style': 'display:none;'}),
        label='If Others, please specify',
    )
    serial_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Serial Number (optional)'}),
        label='Serial Number',
    )
    category = forms.ChoiceField(
        choices=WorkOrder.CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='repair',
        label='Category',
        required=True,
    )

    class Meta:
        model = WorkOrder
        fields = ['campus', 'office', 'item', 'type', 'other_type', 'serial_number', 'category', 'issue_description']
        widgets = {
            'item': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Computer, Printer, Network Device'}),
            'issue_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Please describe the issue in detail...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'campus' in self.data:
            try:
                campus_id = int(self.data.get('campus'))
                self.fields['office'].queryset = Office.objects.filter(campus_id=campus_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.campus:
            self.fields['office'].queryset = self.instance.campus.offices.all()

class CampusForm(forms.ModelForm):
    """Form for managing campuses"""
    class Meta:
        model = Campus
        fields = ['name', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class OfficeForm(forms.ModelForm):
    """Form for managing offices"""
    class Meta:
        model = Office
        fields = ['name', 'campus', 'floor', 'room_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'campus': forms.Select(attrs={'class': 'form-control'}),
            'floor': forms.TextInput(attrs={'class': 'form-control'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ComputerTechnicianForm(forms.ModelForm):
    """Form for managing computer technicians"""
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(user_type='TSG_staff'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select TSG Staff Member"
    )
    
    class Meta:
        model = ComputerTechnician
        fields = ['user', 'specialization', 'is_available']
        widgets = {
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        } 