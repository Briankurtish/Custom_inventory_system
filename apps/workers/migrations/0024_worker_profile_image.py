# Generated by Django 5.0.6 on 2025-02-16 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workers', '0023_worker_last_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='worker',
            name='profile_image',
            field=models.ImageField(default='avatar.jpg', upload_to='Profile_Images'),
        ),
    ]
