from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("annonces", "0026_cloudinary_media_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="logement",
            name="carte_id_proprio",
            field=models.ImageField(upload_to="uploads/id_verif/"),
        ),
        migrations.AlterField(
            model_name="logement",
            name="video_preuve",
            field=models.FileField(blank=True, null=True, upload_to="uploads/videos/"),
        ),
        migrations.AlterField(
            model_name="photo",
            name="image",
            field=models.ImageField(upload_to="uploads/"),
        ),
    ]
