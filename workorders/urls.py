from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard and main functionality
    path('', views.dashboard_view, name='dashboard'),
    path('create-work-order/', views.create_work_order_view, name='create_work_order'),
    path('work-order/<int:work_order_id>/', views.work_order_detail_view, name='work_order_detail'),
    
    # TSG Staff only views
    path('assign-work-order/<int:work_order_id>/', views.assign_work_order_view, name='assign_work_order'),
    path('update-work-order/<int:work_order_id>/', views.update_work_order_view, name='update_work_order'),
    path('delete-work-order/<int:work_order_id>/', views.delete_work_order_view, name='delete_work_order'),
    path('export-work-order/<int:work_order_id>/', views.export_work_order_view, name='export_work_order'),
    
    # Management views (TSG Staff only)
    path('manage-campuses/', views.manage_campuses_view, name='manage_campuses'),
    path('manage-offices/', views.manage_offices_view, name='manage_offices'),
    path('manage-technicians/', views.manage_technicians_view, name='manage_technicians'),
    path('manage-users/', views.manage_users_view, name='manage_users'),
    path('manage-accomplishment-report/', views.manage_accomplishment_report_view, name='manage_accomplishment_report'),
    path('export-accomplishment-report/', views.export_accomplishment_report_view, name='export_accomplishment_report'),
    
    # AJAX endpoints
    path('ajax/get-offices/', views.get_offices_by_campus, name='get_offices_by_campus'),
    path('edit-technician/<int:technician_id>/', views.edit_technician_view, name='edit_technician'),
    path('edit-user/<int:user_id>/', views.edit_user_view, name='edit_user'),
    path('edit-office/<int:office_id>/', views.edit_office_view, name='edit_office'),
] 