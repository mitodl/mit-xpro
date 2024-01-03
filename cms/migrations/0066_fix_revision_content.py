# Generated by Django 3.2.23 on 2024-01-02 20:05

from django.db import migrations
from wagtail.models import Page, Revision


def migrate_content_type_id(apps, schema_editor):
    Site = apps.get_model("wagtailcore", "Site")
    site = Site.objects.filter(is_default_site=True).first()
    home_page = Page.objects.get(id=site.root_page.id)
    ContentType = apps.get_model("contenttypes", "ContentType")
    BlogIndexPage = apps.get_model("cms", "BlogIndexPage")

    blog_index_content_type, _ = ContentType.objects.get_or_create(
        app_label="cms", model="blogindexpage"
    )
    blog_index = BlogIndexPage.objects.first()
    if blog_index:
        blog_page_content = dict(
            title="Blog",
            content_type_id=blog_index_content_type.id,
            content_type=blog_index_content_type.id,
            locale_id=home_page.get_default_locale().id,
        )
        Revision.objects.filter(page_id=blog_index.id).update()


class Migration(migrations.Migration):
    dependencies = [
        ('cms', '0065_blogindexpage'),
    ]

    run_before = [("wagtailcore", "0072_alter_revision_content_type_notnull"), ]

    operations = [migrations.RunPython(migrate_content_type_id, migrations.RunPython.noop)]
