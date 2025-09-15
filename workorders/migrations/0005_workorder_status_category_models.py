from django.db import migrations, models


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
        migrations.AddField(
            model_name='workorder',
            name='status_new',
            field=models.ForeignKey(null=True, on_delete=models.PROTECT, related_name='work_orders', to='workorders.workorderstatus'),
        ),
        migrations.AddField(
            model_name='workorder',
            name='category_new',
            field=models.ForeignKey(null=True, on_delete=models.PROTECT, related_name='work_orders', to='workorders.workordercategory'),
        ),
    ]
