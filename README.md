# Work Order Management System

A comprehensive Django web application for managing IT support work order requests with role-based access control and real-time tracking.

## Features

### User Management
- **TSG Staff**: Full administrative access with ability to manage users, assign technicians, and control system settings
- **Standard Users**: Limited access to create work orders and view their own requests

### Dashboard
- Real-time statistics showing total, completed, and pending work orders
- Available technician count
- Filterable work order list with pagination
- Status-based filtering (Pending, On Going, Completed)

### Work Order Management
- **Standard Users**: Can create work order requests with campus, office, item, issue type, and description
- **TSG Staff**: Can assign technicians, update status, add remarks, and mark work orders as completed
- Dynamic form fields (office selection based on campus)
- Comprehensive work order tracking with timestamps

### Administrative Features
- Campus and office management
- Computer technician management
- User account management
- Work order history tracking

## Technology Stack

- **Backend**: Django 5.2.4
- **Database**: PostgreSQL
- **Frontend**: Bootstrap 5, jQuery
- **Forms**: Django Crispy Forms with Bootstrap 5
- **Authentication**: Django's built-in authentication system

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL
- pip

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd workorder_system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure PostgreSQL**
   - Create a PostgreSQL database named `workorder_db`
   - Update database settings in `workorder_system/settings.py`:
     ```python
     DATABASES = {
         'default': {
             'ENGINE': 'django.db.backends.postgresql',
             'NAME': 'workorder_db',
             'USER': 'your_username',
             'PASSWORD': 'your_password',
             'HOST': 'localhost',
             'PORT': '5432',
         }
     }
     ```

5. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Open your browser and go to `http://127.0.0.1:8000`
   - Register a new account or login with the superuser credentials

## Database Schema

### Core Models

#### User (Custom User Model)
- `username`, `email`, `first_name`, `last_name`
- `user_type`: TSG_staff or standard_user
- `phone_number`, `department`

#### Campus
- `name`, `address`, `created_at`

#### Office
- `name`, `campus` (ForeignKey), `floor`, `room_number`

#### ComputerTechnician
- `user` (OneToOneField), `specialization`, `is_available`

#### WorkOrder
- Request details: `campus`, `office`, `item`, `issue_type`, `issue_description`
- Assignment: `assigned_technician`, `assigned_by`, `date_assigned`
- Status tracking: `status`, `remarks`, `date_completed`, `completed_by`
- Timestamps: `created_at`, `updated_at`

#### WorkOrderHistory
- Tracks all changes to work orders for audit purposes

## User Roles and Permissions

### TSG Staff
- Full access to all system features
- Can manage user accounts
- Can assign technicians to work orders
- Can update work order status and add remarks
- Can manage campuses, offices, and technicians
- Can view all work orders in the system

### Standard Users
- Can create work order requests
- Can view their own work orders
- Can view dashboard statistics
- Limited to basic functionality

## API Endpoints

### Authentication
- `POST /register/` - User registration
- `POST /login/` - User login
- `GET /logout/` - User logout

### Work Orders
- `GET /` - Dashboard with work order list
- `POST /create-work-order/` - Create new work order
- `GET /work-order/<id>/` - View work order details
- `POST /assign-work-order/<id>/` - Assign technician (TSG Staff only)
- `POST /update-work-order/<id>/` - Update work order (TSG Staff only)

### Management (TSG Staff only)
- `GET /manage-campuses/` - Manage campus locations
- `GET /manage-offices/` - Manage office locations
- `GET /manage-technicians/` - Manage computer technicians
- `GET /manage-users/` - Manage user accounts

### AJAX Endpoints
- `GET /ajax/get-offices/` - Get offices for selected campus

## Customization

### Adding New Issue Types
Edit the `TYPE_CHOICES` in `workorders/models.py`:
```python
TYPE_CHOICES = [
    ('hardware', 'Hardware Issue'),
    ('software', 'Software Issue'),
    ('network', 'Network Issue'),
    ('printer', 'Printer Issue'),
    ('other', 'Other'),
    # Add new types here
]
```

### Modifying User Roles
Update the `USER_TYPE_CHOICES` in `workorders/models.py`:
```python
USER_TYPE_CHOICES = [
    ('TSG_staff', 'TSG Staff'),
    ('standard_user', 'Standard User'),
    # Add new roles here
]
```

### Customizing the Dashboard
Modify the statistics in `workorders/views.py` dashboard_view function to add new metrics.

## Deployment

### Production Settings
1. Set `DEBUG = False` in settings.py
2. Configure proper database settings
3. Set up static file serving
4. Configure email settings for notifications
5. Set up proper security headers

### Environment Variables
Create a `.env` file for sensitive settings:
```
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/workorder_db
DEBUG=False
ALLOWED_HOSTS=your-domain.com
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please contact the development team or create an issue in the repository. 