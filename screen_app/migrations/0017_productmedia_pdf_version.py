# Generated by Django 5.1.5 on 2025-01-29 09:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("screen_app", "0016_remove_productmedia_image_version"),
    ]

    operations = [
        migrations.AddField(
            model_name="productmedia",
            name="pdf_version",
            field=models.FileField(
                blank=True, null=True, upload_to="product_media/pdf_versions/"
            ),
        ),
    ]
