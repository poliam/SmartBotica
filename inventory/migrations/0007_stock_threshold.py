# Generated by Django 3.0.7 on 2024-04-07 17:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0006_auto_20240326_1051'),
    ]

    operations = [
        migrations.AddField(
            model_name='stock',
            name='threshold',
            field=models.PositiveIntegerField(default=0),
        ),
    ]