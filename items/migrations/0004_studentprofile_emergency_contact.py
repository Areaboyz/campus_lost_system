from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('items', '0003_studentprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentprofile',
            name='emergency_contact_name',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='emergency_contact_phone',
            field=models.CharField(blank=True, max_length=30),
        ),
    ]
