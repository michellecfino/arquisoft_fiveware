# Generated migration for models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('status', models.CharField(choices=[('active', 'Activo'), ('inactive', 'Inactivo')], default='active', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Proyecto',
                'verbose_name_plural': 'Proyectos',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('completed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='src.project')),
            ],
            options={
                'verbose_name': 'Tarea',
                'verbose_name_plural': 'Tareas',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('success', 'Éxito'), ('degraded', 'Degradado'), ('failed', 'Fallo')], default='success', max_length=20)),
                ('failure_reason', models.CharField(choices=[('none', 'Ninguno'), ('heartbeat', 'Heartbeat'), ('timeout', 'Timeout'), ('connection_error', 'Error de Conexión'), ('unknown', 'Desconocido')], default='none', max_length=50)),
                ('total_tasks', models.IntegerField(default=0)),
                ('completed_tasks', models.IntegerField(default=0)),
                ('completion_percentage', models.FloatField(default=0.0)),
                ('response_time_ms', models.FloatField(default=0.0)),
                ('query_time_ms', models.FloatField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('last_activity', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='src.project')),
            ],
            options={
                'verbose_name': 'Reporte',
                'verbose_name_plural': 'Reportes',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['project', '-created_at'], name='src_report_project_created_idx'),
                    models.Index(fields=['status', '-created_at'], name='src_report_status_created_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='HeartbeatStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_available', models.BooleanField(default=True)),
                ('last_probe_time', models.DateTimeField(auto_now=True)),
                ('last_failure_reason', models.CharField(blank=True, max_length=255, null=True)),
                ('project', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='heartbeat_status', to='src.project')),
            ],
            options={
                'verbose_name': 'Estado Heartbeat',
                'verbose_name_plural': 'Estados Heartbeat',
            },
        ),
    ]
