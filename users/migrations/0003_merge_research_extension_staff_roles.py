from django.db import migrations, models


def merge_staff_roles(apps, schema_editor):
    CustomUser = apps.get_model('users', 'CustomUser')
    CustomUser.objects.filter(role__in=['RESEARCH_STAFF', 'EXTENSION_STAFF']).update(
        role='RESEARCH_EXTENSION_STAFF'
    )


def split_staff_roles(apps, schema_editor):
    CustomUser = apps.get_model('users', 'CustomUser')
    CustomUser.objects.filter(role='RESEARCH_EXTENSION_STAFF').update(role='RESEARCH_STAFF')


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_customuser_department'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(
                choices=[
                    ('ADMIN', 'Administrator'),
                    ('FACULTY', 'Faculty'),
                    ('RESEARCH_EXTENSION_STAFF', 'Research & Extension Staff'),
                ],
                default='FACULTY',
                max_length=30,
            ),
        ),
        migrations.RunPython(merge_staff_roles, split_staff_roles),
    ]
