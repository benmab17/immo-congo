from decimal import Decimal

import cloudinary.uploader
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from annonces.models import Logement, Photo


TEST_IMAGE_KEYWORDS = ("unsplash.com", "placehold.co", "res.cloudinary.com/demo")
SEEDED_ADDRESSES = [
    "Avenue Tombalbaye 18, Gombe",
    "Avenue Golf Club 7, Golf",
    "Route de Sake 44, Keshero",
    "Avenue Kasa-Vubu 112, Bandalungwa",
    "Avenue de la Justice 25, Ngaliema",
    "Boulevard Lumumba 320, Limete",
]

LISTINGS = [
    {
        "ville": Logement.VilleChoices.KINSHASA,
        "commune": "Gombe",
        "adresse": "Avenue Tombalbaye 18, Gombe",
        "categorie_bien": Logement.CategorieBienChoices.APPARTEMENT,
        "prix": Decimal("1200.00"),
        "type_transaction": Logement.TypeTransactionChoices.LOCATION,
        "description": (
            "Appartement moderne de 2 chambres a Gombe, avec groupe electrogene, "
            "parking, eau Regideso et finition propre. Ideal pour jeune couple ou cadre."
        ),
        "nb_chambres": 2,
        "nb_salles_bain": 2,
        "surface_m2": Decimal("95.00"),
        "contact_proprietaire": "Jonathan Mbuyi",
        "telephone_proprio": "+243 815 120 200",
        "eau_regideso": True,
        "elec_snel": True,
        "sentinelle": True,
        "parking": True,
        "cloture": True,
        "point_repere": "A deux minutes du Boulevard du 30 Juin",
        "gps_lat": -4.3226,
        "gps_long": 15.3121,
        "image_source": "https://placehold.co/1200x800/png?text=Appartement+Gombe",
    },
    {
        "ville": Logement.VilleChoices.LUBUMBASHI,
        "commune": "Golf",
        "adresse": "Avenue Golf Club 7, Golf",
        "categorie_bien": Logement.CategorieBienChoices.MAISON,
        "prix": Decimal("150000.00"),
        "type_transaction": Logement.TypeTransactionChoices.VENTE,
        "description": (
            "Maison basse de 3 chambres au quartier Golf a Lubumbashi, avec grand jardin, "
            "cloture, parking et bon acces. Convient pour residence familiale."
        ),
        "nb_chambres": 3,
        "nb_salles_bain": 2,
        "surface_m2": Decimal("240.00"),
        "contact_proprietaire": "Fidele Kalala",
        "telephone_proprio": "+243 997 401 118",
        "eau_regideso": True,
        "elec_snel": True,
        "sentinelle": False,
        "parking": True,
        "cloture": True,
        "point_repere": "Non loin du Golf Club de Lubumbashi",
        "gps_lat": -11.6586,
        "gps_long": 27.4732,
        "image_source": "https://placehold.co/1200x800/png?text=Maison+Golf",
    },
    {
        "ville": Logement.VilleChoices.GOMA,
        "commune": "Keshero",
        "adresse": "Route de Sake 44, Keshero",
        "categorie_bien": Logement.CategorieBienChoices.TERRAIN,
        "prix": Decimal("12000.00"),
        "type_transaction": Logement.TypeTransactionChoices.VENTE,
        "description": (
            "Terrain de 20/20 metres a Keshero avec vue degagee sur le lac. "
            "Dossier foncier en regle, acces praticable et quartier en developpement."
        ),
        "nb_chambres": 0,
        "nb_salles_bain": 0,
        "surface_m2": Decimal("400.00"),
        "contact_proprietaire": "Aline Bahati",
        "telephone_proprio": "+243 824 110 771",
        "eau_regideso": False,
        "elec_snel": False,
        "sentinelle": False,
        "parking": False,
        "cloture": False,
        "point_repere": "Vers la route qui descend sur le lac",
        "gps_lat": -1.6598,
        "gps_long": 29.2266,
        "image_source": "https://placehold.co/1200x800/png?text=Terrain+Keshero",
    },
    {
        "ville": Logement.VilleChoices.KINSHASA,
        "commune": "Bandalungwa",
        "adresse": "Avenue Kasa-Vubu 112, Bandalungwa",
        "categorie_bien": Logement.CategorieBienChoices.STUDIO,
        "prix": Decimal("300.00"),
        "type_transaction": Logement.TypeTransactionChoices.LOCATION,
        "description": (
            "Studio propre a Bandal avec douche interieure, courant regulier et "
            "proximite des transports. Ideal pour jeune travailleur ou etudiant serieux."
        ),
        "nb_chambres": 1,
        "nb_salles_bain": 1,
        "surface_m2": Decimal("32.00"),
        "contact_proprietaire": "Merveille Bokelo",
        "telephone_proprio": "+243 818 008 901",
        "eau_regideso": True,
        "elec_snel": True,
        "sentinelle": False,
        "parking": False,
        "cloture": True,
        "point_repere": "A quelques pas du rond-point Huileries",
        "gps_lat": -4.3389,
        "gps_long": 15.2811,
        "image_source": "https://placehold.co/1200x800/png?text=Studio+Bandal",
    },
    {
        "ville": Logement.VilleChoices.KINSHASA,
        "commune": "Ngaliema",
        "adresse": "Avenue de la Justice 25, Ngaliema",
        "categorie_bien": Logement.CategorieBienChoices.VILLA,
        "prix": Decimal("450000.00"),
        "type_transaction": Logement.TypeTransactionChoices.VENTE,
        "description": (
            "Villa de luxe a Ngaliema avec piscine, jardin, securite 24h/24, "
            "groupe electrogene et finitions haut de gamme. Bien adapte a une grande famille."
        ),
        "nb_chambres": 5,
        "nb_salles_bain": 4,
        "surface_m2": Decimal("520.00"),
        "contact_proprietaire": "Patrick Ilunga",
        "telephone_proprio": "+243 814 550 600",
        "eau_regideso": True,
        "elec_snel": True,
        "sentinelle": True,
        "parking": True,
        "cloture": True,
        "point_repere": "A proximite de l'avenue des Cliniques",
        "gps_lat": -4.3664,
        "gps_long": 15.2457,
        "image_source": "https://placehold.co/1200x800/png?text=Villa+Ngaliema",
    },
    {
        "ville": Logement.VilleChoices.KINSHASA,
        "commune": "Limete",
        "adresse": "Boulevard Lumumba 320, Limete",
        "categorie_bien": Logement.CategorieBienChoices.ENTREPOT,
        "prix": Decimal("2500.00"),
        "type_transaction": Logement.TypeTransactionChoices.LOCATION,
        "description": (
            "Depot a louer a Limete avec acces camions facile, grande cour de manoeuvre "
            "et alimentation electrique stable. Convient pour stockage ou distribution."
        ),
        "nb_chambres": 0,
        "nb_salles_bain": 1,
        "surface_m2": Decimal("680.00"),
        "contact_proprietaire": "Cedrick Muanza",
        "telephone_proprio": "+243 899 212 404",
        "eau_regideso": True,
        "elec_snel": True,
        "sentinelle": True,
        "parking": True,
        "cloture": True,
        "point_repere": "A cote de la 12e Rue industrielle",
        "gps_lat": -4.3313,
        "gps_long": 15.3154,
        "image_source": "https://placehold.co/1200x800/png?text=Entrepot+Limete",
    },
]


class Command(BaseCommand):
    help = "Supprime les annonces de test evidentes et cree 6 annonces mock credibles pour la RDC."

    def _upload_image(self, source_url):
        uploaded = cloudinary.uploader.upload(source_url, resource_type="image", folder="immo_congo/mocks")
        image_name = f"{uploaded['public_id']}.{uploaded['format']}"
        return uploaded["secure_url"], image_name

    def _build_test_filter(self):
        query = (
            Q(commune__icontains="test")
            | Q(description__icontains="mock")
            | Q(description__icontains="verifier les medias")
            | Q(contact_proprietaire__iexact="Mock Owner")
            | Q(telephone_proprio__icontains="000000000")
            | Q(adresse__in=SEEDED_ADDRESSES)
        )
        for keyword in TEST_IMAGE_KEYWORDS:
            query |= Q(image_url__icontains=keyword)
        return query

    def handle(self, *args, **options):
        deleted_count, _ = Logement.objects.filter(self._build_test_filter()).delete()
        self.stdout.write(f"{deleted_count} annonces de test supprimees.")

        document_url, document_name = self._upload_image(
            "https://placehold.co/1200x800/png?text=Piece+Justificative"
        )
        self.stdout.write(f"Piece justificative mock chargee: {document_url}")

        created = []
        for payload in LISTINGS:
            image_url, image_name = self._upload_image(payload["image_source"])
            logement = Logement.objects.create(
                ville=payload["ville"],
                ville_autre="",
                commune=payload["commune"],
                adresse=payload["adresse"],
                image_url=image_url,
                categorie_bien=payload["categorie_bien"],
                prix=payload["prix"],
                devise=Logement.DeviseChoices.USD,
                type_transaction=payload["type_transaction"],
                disponibilite=Logement.DisponibiliteChoices.DISPONIBLE,
                statut=Logement.PublicationStatus.APPROUVEE,
                description=payload["description"],
                nb_chambres=payload["nb_chambres"],
                nb_salles_bain=payload["nb_salles_bain"],
                surface_m2=payload["surface_m2"],
                contact_proprietaire=payload["contact_proprietaire"],
                telephone_proprio=payload["telephone_proprio"],
                eau_regideso=payload["eau_regideso"],
                elec_snel=payload["elec_snel"],
                sentinelle=payload["sentinelle"],
                parking=payload["parking"],
                cloture=payload["cloture"],
                carte_id_proprio=document_name,
                point_repere=payload["point_repere"],
                gps_lat=payload["gps_lat"],
                gps_long=payload["gps_long"],
                approved_at=timezone.now(),
            )
            Photo.objects.create(logement=logement, image=image_name)
            created.append(f"{logement.code_immo} - {logement.titre}")

        self.stdout.write(self.style.SUCCESS("6 annonces mock RDC creees avec succes."))
        for line in created:
            self.stdout.write(f"- {line}")
