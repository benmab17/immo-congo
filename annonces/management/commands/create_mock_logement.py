from django.core.management.base import BaseCommand
from django.utils import timezone

import cloudinary.uploader

from annonces.models import Logement, Photo


class Command(BaseCommand):
    help = "Create one mock Logement with a Cloudinary image and video."

    def handle(self, *args, **options):
        image = cloudinary.uploader.upload(
            "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2",
            resource_type="image",
        )

        video = cloudinary.uploader.upload(
            "https://res.cloudinary.com/demo/video/upload/dog.mp4",
            resource_type="video",
        )

        image_name = f"{image['public_id']}.{image['format']}"

        logement = Logement.objects.create(
            ville=Logement.VilleChoices.KINSHASA,
            ville_autre="",
            commune=f"Gombe Test {timezone.now().strftime('%Y%m%d%H%M%S')}",
            adresse="Avenue des Huileries 10",
            image_url=image["secure_url"],
            categorie_bien=Logement.CategorieBienChoices.APPARTEMENT,
            prix="1500.00",
            devise=Logement.DeviseChoices.USD,
            type_transaction=Logement.TypeTransactionChoices.LOCATION,
            disponibilite=Logement.DisponibiliteChoices.DISPONIBLE,
            statut=Logement.PublicationStatus.APPROUVEE,
            description="Appartement mock pour verifier les medias Cloudinary en production.",
            nb_chambres=2,
            nb_salles_bain=1,
            surface_m2="85.00",
            contact_proprietaire="Mock Owner",
            telephone_proprio="+243000000000",
            eau_regideso=True,
            elec_snel=True,
            sentinelle=False,
            parking=True,
            cloture=True,
            video_preuve=video["public_id"],
            carte_id_proprio=image_name,
            point_repere="En face du supermarche",
            gps_lat=-4.3276,
            gps_long=15.3136,
        )

        Photo.objects.create(
            logement=logement,
            image=image_name,
        )

        self.stdout.write(self.style.SUCCESS("Mock logement created successfully"))
