import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("annonces", "0025_logement_image_url"),
    ]

    operations = [
        migrations.AlterField(
            model_name="logement",
            name="carte_id_proprio",
            field=cloudinary.models.CloudinaryField(max_length=255, verbose_name="image"),
        ),
        migrations.AlterField(
            model_name="logement",
            name="video_preuve",
            field=cloudinary.models.CloudinaryField(
                blank=True,
                null=True,
                resource_type="video",
                max_length=255,
                verbose_name="video",
            ),
        ),
        migrations.AlterField(
            model_name="photo",
            name="image",
            field=cloudinary.models.CloudinaryField(max_length=255, verbose_name="image"),
        ),
    ]
