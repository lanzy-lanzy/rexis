from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_statuses_forward(apps, schema_editor):
    Proposal = apps.get_model('proposals', 'Proposal')
    Proposal.objects.filter(status='PENDING').update(status='PENDING_RECOMMENDATION')


def migrate_statuses_backward(apps, schema_editor):
    Proposal = apps.get_model('proposals', 'Proposal')
    Proposal.objects.filter(status='PENDING_RECOMMENDATION').update(status='PENDING')
    Proposal.objects.filter(status='RECOMMENDED_APPROVAL').update(status='PENDING')
    Proposal.objects.filter(status='RECOMMENDED_REVISION').update(status='REJECTED')


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('proposals', '0004_proposalrequirement'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposal',
            name='submitted_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='proposals_submitted',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='proposal',
            name='submitted_on_behalf',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='proposal',
            name='recommended_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='proposals_recommended',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='proposal',
            name='recommendation_notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='proposal',
            name='recommended_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='proposal',
            name='project_progress_status',
            field=models.CharField(
                blank=True,
                choices=[
                    ('ONGOING', 'Ongoing'),
                    ('PRESENTED', 'Presented'),
                    ('COMPLETED', 'Completed'),
                ],
                max_length=20,
            ),
        ),
        migrations.RunPython(migrate_statuses_forward, migrate_statuses_backward),
        migrations.AlterField(
            model_name='proposal',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING_RECOMMENDATION', 'Pending Staff Recommendation'),
                    ('RECOMMENDED_APPROVAL', 'Recommended for Admin Approval'),
                    ('RECOMMENDED_REVISION', 'Recommended for Revision'),
                    ('APPROVED', 'Approved'),
                    ('REJECTED', 'Rejected'),
                ],
                default='PENDING_RECOMMENDATION',
                max_length=30,
            ),
        ),
    ]