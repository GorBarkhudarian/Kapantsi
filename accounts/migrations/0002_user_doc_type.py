from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='doc_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('national_id_card', 'National ID Card'),
                    ('passport', 'Physical Passport'),
                ],
                default='national_id_card',
                help_text='Type of identity document provided',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='user',
            name='national_id',
            field=models.CharField(
                blank=True,
                help_text='9-digit national ID card number, or 2 uppercase letters + 7 digits for passport',
                max_length=9,
                null=True,
                unique=True,
            ),
        ),
    ]
