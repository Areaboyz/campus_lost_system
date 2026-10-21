from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('items', '0004_studentprofile_emergency_contact'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentprofile',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to='profile_pictures/'),
        ),
    ]
