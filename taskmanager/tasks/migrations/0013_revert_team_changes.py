# Generated manually to revert team management changes

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0012_auto_20250922_1014'),
    ]

    operations = [
        # Remove team-related fields from Task model
        migrations.RemoveField(
            model_name='task',
            name='assigned_team',
        ),
        migrations.RemoveField(
            model_name='task',
            name='team_seen',
        ),
        
        # Delete Team and TeamMember models
        migrations.DeleteModel(
            name='TeamMember',
        ),
        migrations.DeleteModel(
            name='Team',
        ),
        
        # Restore original Task.assigned_to field
        migrations.AlterField(
            model_name='task',
            name='assigned_to',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='Task', to=settings.AUTH_USER_MODEL),
        ),
    ]
