# Generated by Django 2.2.20 on 2021-04-28 16:28

"""
Data migrations moved to cms/migrations/0068_new_page_data_migrations.py in response to Page model change
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("wagtailcore", "0062_comment_models_and_pagesubscription"),
        ("cms", "0051_new_page_data_migrations"),
    ]
    operations = [
        migrations.RunPython(migrations.RunPython.noop, migrations.RunPython.noop)
    ]
