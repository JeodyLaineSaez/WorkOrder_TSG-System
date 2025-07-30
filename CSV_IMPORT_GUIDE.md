# CSV Import Guide for Work Order System

## Overview

The Work Order System now supports importing work orders from CSV files. This feature allows TSG staff to bulk import work order data, making it easier to migrate data from other systems or add multiple work orders at once.

## Features

- **Bulk Import**: Import multiple work orders from a single CSV file
- **Flexible Format**: Supports various date formats and field mappings
- **Error Handling**: Detailed error reporting for problematic rows
- **Template Download**: Download a sample CSV template to understand the required format
- **Auto-creation**: Automatically creates campuses and offices if they don't exist
- **Validation**: Validates required fields and data formats

## Accessing the Import Feature

### For TSG Staff:
1. **Dashboard**: Navigate to the dashboard and scroll down to the "Import/Export Work Orders" section
2. **Navigation Menu**: Go to Management → Import Work Orders
3. **Direct URL**: Access `/import-work-orders-csv/`

### For Regular Users:
- CSV import is only available to TSG staff members

## CSV File Format

### Required Columns

| Column | Description | Required | Example |
|--------|-------------|----------|---------|
| `campus` | Campus name | Yes | "City Camp" |
| `office` | Office name | Yes | "COT", "Library", "Registrar" |
| `item` | Item description | Yes | "Computer And Network", "Epson L3210" |
| `issue_description` | Problem description | Yes | "No magenta color in printer" |

### Optional Columns

| Column | Description | Required | Example |
|--------|-------------|----------|---------|
| `type` | Work order type | No | "desktop_laptop", "printer", "scanner" |
| `serial_number` | Item serial number | No | "K2501N01" |
| `requested_by` | Requester name | No | "John Doe", "jane.smith" |
| `date_requested` | Request date | No | "2024-01-15 09:30:00" |
| `assigned_technician` | Technician name | No | "Alvin", "adrian.na" |
| `category` | Work category | No | "repair", "maintenance", "checkup" |
| `remarks` | Additional notes | No | "Urgent request", "Done" |
| `date_completed` | Completion date | No | "2024-01-15 16:45:00" |
| `status` | Work order status | No | "pending", "on_going", "completed" |

### Supported Values

#### Type Values:
- `desktop_laptop` or `Desktop/Laptop Computer`
- `printer` or `Printer`
- `scanner` or `Scanner`
- `lan_internet` or `LAN/Internet`
- `other` or `Others`

#### Category Values:
- `repair` or `Repair`
- `maintenance` or `Maintenance`
- `checkup` or `Checkup`
- `cleaning` or `Cleaning`
- `data_backup_recovery` or `Data Backup and Recovery`
- `installation_setup` or `Installation and Setup`
- `reformatting_reinstallation` or `Reformatting and Reinstallation`
- `replacement` or `Replacement`
- `relocation_reassignment` or `Relocation/Reassignment`
- `update_upgrade_software` or `Update/Upgrade Software`

#### Status Values:
- `pending` or `Pending`
- `on_going` or `On Going`
- `completed` or `Completed`

### User and Technician Auto-Creation (Duplicate Prevention)

The system will automatically create users and technicians if they don't exist, with intelligent duplicate detection:

#### Requested By (requested_by):
- **Existing User**: Matches by username, email, or full name (case-insensitive)
- **Duplicate Prevention**: Uses exact matching to avoid creating multiple users with the same name
- **New User**: If not found, creates a new user with:
  - Username: lowercase name with underscores
  - First/Last name: split from full name
  - Email: username@example.com (placeholder)
  - User type: standard_user
- **Default**: Current user if creation fails

#### Assigned Technician (assigned_technician):
- **Existing Technician**: Matches by username, email, or full name (case-insensitive)
- **Duplicate Prevention**: Uses exact matching to avoid creating multiple technicians with the same name
- **New Technician**: If not found, creates a new user and technician with:
  - Username: lowercase name with underscores
  - First/Last name: split from full name
  - Email: username@example.com (placeholder)
  - User type: TSG_staff
  - Technician profile: General IT Support specialization
- **Default**: None if creation fails

#### Campus and Office:
- **Existing Campus/Office**: Matches by exact name (case-insensitive)
- **Duplicate Prevention**: Only creates new campuses/offices if they don't already exist
- **New Campus/Office**: Creates with proper relationships maintained

**Examples:**
- `"John Doe"` → matches existing user or creates new one with username="john_doe"
- `"Alvin"` → matches existing technician or creates new one with username="alvin"
- `"City Camp"` → matches existing campus or creates new one
- `"COT"` → matches existing office in "City Camp" or creates new one

### Date Formats Supported:

The system supports multiple date formats for both `date_requested` and `date_completed`:

#### Date and Time Formats:
- `YYYY-MM-DD HH:MM:SS` (e.g., "2024-01-15 09:30:00")
- `YYYY-MM-DD HH:MM` (e.g., "2024-01-15 09:30")
- `MM/DD/YYYY HH:MM:SS` (e.g., "01/15/2024 09:30:00")
- `MM/DD/YYYY HH:MM` (e.g., "01/15/2024 09:30")
- `DD/MM/YYYY HH:MM:SS` (e.g., "15/01/2024 09:30:00")
- `DD/MM/YYYY HH:MM` (e.g., "15/01/2024 09:30")
- `January 15, 2024 09:30:00`
- `January 15, 2024 09:30`

#### Date Only Formats:
- `YYYY-MM-DD` (e.g., "2024-01-15")
- `MM/DD/YYYY` (e.g., "01/15/2024")
- `DD/MM/YYYY` (e.g., "15/01/2024")
- `January 15, 2024`

**Notes:**
- **Date Retention**: The system preserves the actual dates from the CSV file
- If `date_requested` is missing or invalid, current time will be used
- If `date_completed` is missing or invalid, it will be set to None
- All dates are automatically converted to Philippine timezone (UTC+8)
- Empty date fields are handled gracefully
- **Empty Fields**: Empty columns are preserved as empty (not filled with defaults)

## Sample CSV File

```csv
campus,office,type,item,serial_number,issue_description,requested_by,date_requested,assigned_technician,category,remarks,date_completed,status
City Camp,COT,desktop_laptop,Computer And Network,K2501N01,No magenta color in printer,John Doe,July 21, 2025 at 08:00 AM,Alvin,repair,Urgent request,,pending
City Camp,Library,printer,Epson L3210,,Setup of computer network,Jane Smith,July 21, 2025 at 08:00 AM,Adrian Na,installation_setup,Done,July 21, 2025 at 03:20 PM,completed
City Camp,Registrar,lan_internet,Wifi Router,,No internet connection,Bob Johnson,July 21, 2025 at 08:00 AM,Daniel V. I,repair,Under investigation,July 21, 2025 at 03:22 PM,completed
City Camp,CAO,desktop_laptop,MSI Thin 1 K2501N01,K2501N01,Excel not visible,Ryan R. Es,July 22, 2025 at 08:00 AM,Jhun Jhun,maintenance,Software issue,July 22, 2025 at 03:24 PM,completed
City Camp,Legal,printer,HP LaserJet,,Paper jam issue,Ellen Jane,July 23, 2025 at 09:00 AM,,repair,,,pending
```

## How to Import

### Step 1: Prepare Your CSV File
1. Create a CSV file with the required columns
2. Ensure all required fields are filled
3. Use supported values for type, category, and status fields
4. Format dates correctly

### Step 2: Access Import Page
1. Log in as a TSG staff member
2. Navigate to Management → Import Work Orders
3. Or go to Dashboard → Import/Export Work Orders section

### Step 3: Upload and Import
1. Click "Choose File" and select your CSV file
2. Click "Import CSV" button
3. Review the import results and any error messages
4. Check the dashboard to see imported work orders

### Step 4: Download Template (Optional)
1. On the import page, click "Download Template"
2. Use the template as a starting point for your CSV file
3. Modify the sample data with your actual work order information

## Error Handling

The system provides detailed error reporting:

- **Missing Required Fields**: Rows without campus, office, item, or issue_description are skipped
- **Invalid Data**: Rows with invalid type, category, or status values use defaults
- **Date Parsing Errors**: Invalid dates default to current time (for requested) or null (for completed)
- **Import Summary**: Shows total imported and error counts

### Common Errors and Solutions:

1. **"Missing required fields"**
   - Ensure campus, office, item, and issue_description columns are present and filled

2. **"Invalid type/category/status"**
   - Use the exact values listed in the supported values section
   - Check for typos or extra spaces

3. **"Date parsing error"**
   - Use one of the supported date formats
   - Ensure dates are in a consistent format

## Best Practices

1. **Test with Small Files**: Start with a few rows to test the import process
2. **Backup Data**: Always backup existing data before bulk imports
3. **Validate Data**: Check your CSV file for errors before importing
4. **Use Templates**: Download and use the provided template as a starting point
5. **Review Results**: Always check the import summary and error messages

## File Size Limits

- Maximum file size: 5MB
- Supported format: CSV only
- Encoding: UTF-8 recommended

## Security Considerations

- Only TSG staff can import CSV files
- Files are validated for format and content
- Import operations are logged in the system
- Database transactions ensure data integrity

## Troubleshooting

### Import Fails Completely
- Check file format (must be CSV)
- Verify file size (under 5MB)
- Ensure you're logged in as TSG staff

### Some Rows Fail to Import
- Check error messages for specific row numbers
- Verify required fields are present
- Ensure data formats are correct

### No Work Orders Appear After Import
- Check if campuses and offices exist in the system
- Verify the import completed successfully
- Check the dashboard for imported work orders

## Support

If you encounter issues with CSV import:

1. Check the error messages on the import page
2. Verify your CSV format matches the template
3. Ensure all required fields are present
4. Contact system administrator for technical support

## Related Features

- **Export Work Orders**: Download existing work orders as CSV
- **Work Order Management**: View and manage imported work orders
- **Dashboard Analytics**: See imported work orders in system statistics 