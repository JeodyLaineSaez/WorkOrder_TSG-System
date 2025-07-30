from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import WorkOrder, Campus, Office, ComputerTechnician, User

# Create your tests here.

class WorkOrderUpdateTestCase(TestCase):
    def setUp(self):
        # Create test users
        self.tsg_staff = User.objects.create_user(
            username='tsg_staff',
            password='testpass123',
            user_type='TSG_staff',
            first_name='John',
            last_name='Doe'
        )
        
        self.standard_user = User.objects.create_user(
            username='standard_user',
            password='testpass123',
            user_type='standard_user',
            first_name='Jane',
            last_name='Smith'
        )
        
        # Create test campus and office
        self.campus = Campus.objects.create(name='Test Campus')
        self.office = Office.objects.create(
            name='Test Office',
            campus=self.campus
        )
        
        # Create test work order
        self.work_order = WorkOrder.objects.create(
            campus=self.campus,
            office=self.office,
            item='Test Computer',
            type='desktop_laptop',
            issue_description='Test issue description',
            requested_by=self.standard_user,
            date_requested=timezone.now() - timedelta(days=5),  # 5 days ago
            status='pending',
            remarks='Initial remarks'
        )
        
        self.client = Client()

    def test_tsg_staff_can_update_status_and_remarks_required(self):
        """Test that TSG staff must provide status and remarks"""
        self.client.login(username='tsg_staff', password='testpass123')
        
        # Try to submit without remarks
        response = self.client.post(
            reverse('update_work_order', args=[self.work_order.id]),
            {
                'status': 'completed',
                'remarks': '',  # Empty remarks should fail
                'date_requested': '',
                'requested_by_name': ''
            }
        )
        
        self.assertEqual(response.status_code, 200)  # Form should not submit
        self.assertContains(response, 'Remarks are required for work order updates.')

    def test_tsg_staff_can_update_date_requested_future_only(self):
        """Test that TSG staff cannot set date_requested to past dates"""
        self.client.login(username='tsg_staff', password='testpass123')
        
        # Try to set date_requested to yesterday
        yesterday = (timezone.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        
        response = self.client.post(
            reverse('update_work_order', args=[self.work_order.id]),
            {
                'status': 'completed',
                'remarks': 'Test remarks',
                'date_requested': yesterday,
                'requested_by_name': ''
            }
        )
        
        self.assertEqual(response.status_code, 200)  # Form should not submit
        self.assertContains(response, 'Date requested cannot be set to a date before today.')

    def test_tsg_staff_can_submit_with_original_past_date_requested(self):
        """Test that TSG staff can submit updates even with original past date_requested"""
        self.client.login(username='tsg_staff', password='testpass123')
        
        # Keep the original date_requested (5 days ago) and submit update
        original_date_str = self.work_order.date_requested.strftime('%Y-%m-%dT%H:%M')
        
        response = self.client.post(
            reverse('update_work_order', args=[self.work_order.id]),
            {
                'status': 'completed',
                'remarks': 'Work completed successfully',
                'date_requested': original_date_str,
                'requested_by_name': ''
            }
        )
        
        self.assertEqual(response.status_code, 302)  # Should redirect (success)
        
        # Verify work order was updated
        self.work_order.refresh_from_db()
        self.assertEqual(self.work_order.status, 'completed')
        self.assertEqual(self.work_order.remarks, 'Work completed successfully')
        self.assertIsNotNone(self.work_order.date_completed)
        self.assertEqual(self.work_order.completed_by, self.tsg_staff)

    def test_tsg_staff_can_complete_work_order_with_past_date_requested(self):
        """Test that TSG staff can complete work orders even with past date_requested"""
        self.client.login(username='tsg_staff', password='testpass123')
        
        # Keep original date_requested (5 days ago) but complete the work order
        response = self.client.post(
            reverse('update_work_order', args=[self.work_order.id]),
            {
                'status': 'completed',
                'remarks': 'Work completed successfully',
                'date_requested': self.work_order.date_requested.strftime('%Y-%m-%dT%H:%M'),
                'requested_by_name': ''
            }
        )
        
        self.assertEqual(response.status_code, 302)  # Should redirect (success)
        
        # Verify work order was updated
        self.work_order.refresh_from_db()
        self.assertEqual(self.work_order.status, 'completed')
        self.assertEqual(self.work_order.remarks, 'Work completed successfully')
        self.assertIsNotNone(self.work_order.date_completed)
        self.assertEqual(self.work_order.completed_by, self.tsg_staff)

    def test_tsg_staff_can_update_requested_by_name(self):
        """Test that TSG staff can update the requested by name"""
        self.client.login(username='tsg_staff', password='testpass123')
        
        response = self.client.post(
            reverse('update_work_order', args=[self.work_order.id]),
            {
                'status': 'on_going',
                'remarks': 'Updated remarks',
                'date_requested': '',
                'requested_by_name': 'New User Name'
            }
        )
        
        self.assertEqual(response.status_code, 302)  # Should redirect (success)
        
        # Verify work order was updated
        self.work_order.refresh_from_db()
        self.assertEqual(self.work_order.status, 'on_going')
        self.assertEqual(self.work_order.remarks, 'Updated remarks')
        
        # Check if new user was created
        new_user = User.objects.filter(first_name='New', last_name='User Name').first()
        self.assertIsNotNone(new_user)
        self.assertEqual(self.work_order.requested_by, new_user)

    def test_tsg_staff_can_update_date_requested_to_future(self):
        """Test that TSG staff can update date_requested to future dates"""
        self.client.login(username='tsg_staff', password='testpass123')
        
        # Set date_requested to tomorrow
        tomorrow = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        
        response = self.client.post(
            reverse('update_work_order', args=[self.work_order.id]),
            {
                'status': 'pending',
                'remarks': 'Updated remarks',
                'date_requested': tomorrow,
                'requested_by_name': ''
            }
        )
        
        self.assertEqual(response.status_code, 302)  # Should redirect (success)
        
        # Verify work order was updated
        self.work_order.refresh_from_db()
        self.assertEqual(self.work_order.status, 'pending')
        self.assertEqual(self.work_order.remarks, 'Updated remarks')
        # Date should be updated to tomorrow
        self.assertEqual(self.work_order.date_requested.date(), (timezone.now() + timedelta(days=1)).date())

    def test_standard_user_cannot_update_date_requested_or_requested_by(self):
        """Test that standard users cannot update date_requested or requested_by"""
        self.client.login(username='standard_user', password='testpass123')
        
        original_date = self.work_order.date_requested
        original_user = self.work_order.requested_by
        
        response = self.client.post(
            reverse('update_work_order', args=[self.work_order.id]),
            {
                'campus': self.campus.id,
                'office': self.office.id,
                'item': 'Updated Item',
                'type': 'desktop_laptop',
                'other_type': '',
                'serial_number': '',
                'category': 'repair',
                'issue_description': 'Updated description'
            }
        )
        
        self.assertEqual(response.status_code, 302)  # Should redirect (success)
        
        # Verify work order was updated but date_requested and requested_by remain unchanged
        self.work_order.refresh_from_db()
        self.assertEqual(self.work_order.item, 'Updated Item')
        self.assertEqual(self.work_order.issue_description, 'Updated description')
        self.assertEqual(self.work_order.date_requested, original_date)
        self.assertEqual(self.work_order.requested_by, original_user)
