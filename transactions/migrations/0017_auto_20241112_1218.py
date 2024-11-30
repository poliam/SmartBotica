# Generated by Django 3.0.7 on 2024-11-12 12:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0016_auto_20240416_1214'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Stock',
        ),
        migrations.RemoveField(
            model_name='purchasebill',
            name='supplier',
        ),
        migrations.RemoveField(
            model_name='salebill',
            name='address',
        ),
        migrations.RemoveField(
            model_name='salebill',
            name='email',
        ),
        migrations.RemoveField(
            model_name='salebill',
            name='name',
        ),
        migrations.RemoveField(
            model_name='salebill',
            name='phone',
        ),
        migrations.RemoveField(
            model_name='salebilldetails',
            name='discount_percentage',
        ),
        migrations.DeleteModel(
            name='Supplier',
        ),
    ]
