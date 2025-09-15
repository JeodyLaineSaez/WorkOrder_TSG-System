from django.db import migrations, models


def create_default_statuses(apps, schema_editor):
    WorkOrderStatus = apps.get_model('workorders', 'WorkOrderStatus')
    
    # Create default statuses
    statuses = [
        {'name': 'pending', 'display_name': 'Pending', 'is_default': True},
        {'name': 'on_going', 'display_name': 'On Going', 'is_default': False},
        {'name': 'completed', 'display_name': 'Completed', 'is_default': False},
    ]
    
    for status in statuses:
        WorkOrderStatus.objects.create(**status)


def create_default_categories(apps, schema_editor):
    WorkOrderCategory = apps.get_model('workorders', 'WorkOrderCategory')
    
    # Create default categories
    categories = [
        {'name': 'repair', 'display_name': 'Repair'},
        {'name': 'maintenance', 'display_name': 'Maintenance'},
        {'name': 'checkup', 'display_name': 'Checkup'},
        {'name': 'cleaning', 'display_name': 'Cleaning'},
        {'name': 'data_backup_recovery', 'display_name': 'Data Backup and Recovery'},
        {'name': 'installation_setup', 'display_name': 'Installation and Setup'},
        {'name': 'reformatting_reinstallation', 'display_name': 'Reformatting and Reinstallation'},
        {'name': 'replacement', 'display_name': 'Replacement'},
        {'name': 'relocation_reassignment', 'display_name': 'Relocation/Reassignment'},
        {'name': 'update_upgrade_software', 'display_name': 'Update/Upgrade Software'},
    ]
    
    for category in categories:
        WorkOrderCategory.objects.create(**category)


def migrate_existing_workorders(apps, schema_editor):
    WorkOrder = apps.get_model('workorders', 'WorkOrder')
    WorkOrderStatus = apps.get_model('workorders', 'WorkOrderStatus')
    WorkOrderCategory = apps.get_model('workorders', 'WorkOrderCategory')

    # Get the status and category maps
    status_map = {status.name: status for status in WorkOrderStatus.objects.all()}
    category_map = {category.name: category for category in WorkOrderCategory.objects.all()}

    # Update all work orders
    for work_order in WorkOrder.objects.all():
        work_order.status = status_map[work_order.status]
        work_order.category = category_map[work_order.category]
        work_order.save()


def reverse_migrate_workorders(apps, schema_editor):
    WorkOrder = apps.get_model('workorders', 'WorkOrder')
    for work_order in WorkOrder.objects.all():
        work_order.status = work_order.status.name
        work_order.category = work_order.category.name
        work_order.save()


class Migration(migrations.Migration):
    dependencies = [
        ('workorders', '0004_alter_workorderhistory_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkOrderStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('display_name', models.CharField(max_length=100)),
                ('is_default', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Work Order Status',
                'verbose_name_plural': 'Work Order Statuses',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='WorkOrderCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('display_name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Work Order Category',
                'verbose_name_plural': 'Work Order Categories',
                'ordering': ['name'],
            },
        ),
        migrations.RunPython(create_default_statuses, migrations.RunPython.noop),
        migrations.RunPython(create_default_categories, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='workorder',
            name='status',
            field=models.ForeignKey(on_delete=models.PROTECT, related_name='work_orders', to='workorders.workorderstatus'),
        ),
        migrations.AlterField(
            model_name='workorder',
            name='category',
            field=models.ForeignKey(on_delete=models.PROTECT, related_name='work_orders', to='workorders.workordercategory'),
        ),
        migrations.RunPython(migrate_existing_workorders, reverse_migrate_workorders),
    ]
