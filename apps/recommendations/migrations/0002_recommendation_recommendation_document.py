# Generated by Django 5.0.6 on 2024-12-13 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recommendations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='recommendation',
            name='recommendation_document',
            field=models.FileField(default='null', upload_to='recommendation_document/'),
            preserve_default=False,
        ),
    ]
