from django.db import migrations

def fix_status_values(apps, schema_editor):
    ContestSubmission = apps.get_model('contests', 'ContestSubmission')
    # Update all submissions where status is not one of the valid choices
    ContestSubmission.objects.filter(status='accepted').update(
        status='finished'  # Set status to finished if it was incorrectly set to accepted
    )

class Migration(migrations.Migration):
    dependencies = [
        ('contests', '0008_alter_contestsubmission_final_verdict_and_more'),
    ]

    operations = [
        migrations.RunPython(fix_status_values),
    ]
