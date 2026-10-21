from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('items', '0002_alter_category_options_alter_lostfounditem_options_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(blank=True, max_length=30)),
                ('register_purpose', models.CharField(choices=[('searching', 'Finding a lost item / searching'), ('reporting', 'Reporting found items'), ('both', 'Both searching and reporting')], default='both', max_length=20)),
                ('search_category', models.CharField(blank=True, choices=[('electronics', 'Electronics and laptops'), ('IDs', 'Student IDs and cards'), ('books', 'Books and course materials'), ('keys', 'Keys and wallets'), ('clothing', 'Clothing and accessories')], max_length=30)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='student_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
