# Generated by Django 3.0.7 on 2024-11-12 12:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0011_auto_20241112_1006'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stock',
            name='units',
        ),
        migrations.AddField(
            model_name='stock',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]