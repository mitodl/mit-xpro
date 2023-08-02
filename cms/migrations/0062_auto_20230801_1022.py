# Generated by Django 3.2.18 on 2023-08-01 10:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0033_remove_course_coursetopic_association'),
        ('cms', '0061_add_new_fields_in_webinarpage'),
    ]

    operations = [
        migrations.AddField(
            model_name='webinarpage',
            name='program',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='courses.program'),
        ),
        migrations.AlterField(
            model_name='webinarpage',
            name='course',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='courses.course'),
        ),
    ]
