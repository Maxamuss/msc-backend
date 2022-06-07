# Generated by Django 4.0.4 on 2022-06-07 12:12

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('syntax', '0015_alter_releasechange_object_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='release',
            name='functions',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name='release',
            name='modelschemas',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name='release',
            name='packages',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name='release',
            name='pages',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name='release',
            name='workflows',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name='releasechange',
            name='object_id',
            field=models.UUIDField(default=uuid.UUID('a70afd8c-1ef1-43c7-81ba-a7bf549723b3'), editable=False, null=True),
        ),
    ]
