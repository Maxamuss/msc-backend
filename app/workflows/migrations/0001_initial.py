# Generated by Django 4.0.4 on 2022-05-07 13:12

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('db', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Workflow',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('workflow_name', models.CharField(max_length=255)),
                ('definition', models.JSONField(default=dict)),
                ('model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workflows', to='db.modelschema')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
