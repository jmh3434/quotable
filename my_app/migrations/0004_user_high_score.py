# Generated by Django 3.1.5 on 2021-05-14 18:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('my_app', '0003_delete_timer'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='high_score',
            field=models.IntegerField(default=0, null=True),
        ),
    ]