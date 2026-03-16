from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone


User = get_user_model()


class Logement(models.Model):
    class VilleChoices(models.TextChoices):
        KINSHASA = "Kinshasa", "Kinshasa"
        LUBUMBASHI = "Lubumbashi", "Lubumbashi"
        GOMA = "Goma", "Goma"
        KOLWEZI = "Kolwezi", "Kolwezi"
        KISANGANI = "Kisangani", "Kisangani"
        MBUJI_MAYI = "Mbuji-Mayi", "Mbuji-Mayi"
        KANANGA = "Kananga", "Kananga"
        BUKAVU = "Bukavu", "Bukavu"
        MATADI = "Matadi", "Matadi"
        BOMA = "Boma", "Boma"
        MBANDAKA = "Mbandaka", "Mbandaka"
        KINDU = "Kindu", "Kindu"
        BUNIA = "Bunia", "Bunia"
        UVIRA = "Uvira", "Uvira"
        KIKWIT = "Kikwit", "Kikwit"
        TSHIKAPA = "Tshikapa", "Tshikapa"
        LIKASI = "Likasi", "Likasi"
        KALEMIE = "Kalemie", "Kalemie"
        BENI = "Beni", "Beni"
        BUTEMBO = "Butembo", "Butembo"
        ISIRO = "Isiro", "Isiro"
        AUTRE = "AUTRE", "Autre"

    class DeviseChoices(models.TextChoices):
        USD = "USD", "USD"
        CDF = "CDF", "CDF"

    class DisponibiliteChoices(models.TextChoices):
        DISPONIBLE = "Disponible", "Disponible"
        LOUE = "LOUE", "Lou\u00e9"
        VENDU = "VENDU", "Vendu"
        INDISPONIBLE = "Indisponible", "Indisponible"

    class PublicationStatus(models.TextChoices):
        BROUILLON = "BROUILLON", "Brouillon"
        EN_ATTENTE = "EN_ATTENTE", "En attente"
        APPROUVEE = "APPROUVEE", "Approuv\u00e9e"
        REJETEE = "REJETEE", "Rejet\u00e9e"
        LOUE = "LOUE", "Lou\u00e9"
        VENDU = "VENDU", "Vendu"

    class TypeTransactionChoices(models.TextChoices):
        LOCATION = "LOCATION", "Location"
        VENTE = "VENTE", "Vente"

    class CategorieBienChoices(models.TextChoices):
        APPARTEMENT = "Appartement", "Appartement"
        MAISON = "Maison", "Maison"
        VILLA = "Villa", "Villa"
        STUDIO = "Studio", "Studio"
        CHAMBRE = "Chambre", "Chambre"
        BUREAU = "Bureau", "Bureau"
        TERRAIN = "Terrain", "Terrain"
        ENTREPOT = "Entrepot", "Entrep\u00f4t"

    ville = models.CharField(max_length=20, choices=VilleChoices.choices)
    ville_autre = models.CharField(max_length=255, blank=True)
    code_immo = models.CharField(max_length=20, unique=True, null=True, blank=True, editable=False)
    proprietaire = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="logements",
        null=True,
        blank=True,
    )
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="verified_logements",
        null=True,
        blank=True,
    )
    commune = models.CharField(max_length=255)
    adresse = models.CharField(max_length=255, default="")
    categorie_bien = models.CharField(
        max_length=30,
        choices=CategorieBienChoices.choices,
        default=CategorieBienChoices.APPARTEMENT,
    )
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    devise = models.CharField(max_length=3, choices=DeviseChoices.choices)
    type_transaction = models.CharField(
        max_length=20,
        choices=TypeTransactionChoices.choices,
        default=TypeTransactionChoices.LOCATION,
    )
    disponibilite = models.CharField(
        max_length=20,
        choices=DisponibiliteChoices.choices,
        default=DisponibiliteChoices.DISPONIBLE,
        verbose_name="Disponibilit\u00e9",
    )
    statut = models.CharField(
        max_length=20,
        choices=PublicationStatus.choices,
        default=PublicationStatus.EN_ATTENTE,
    )
    description = models.TextField()
    nb_chambres = models.IntegerField()
    nb_salles_bain = models.IntegerField(default=1)
    surface_m2 = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    contact_proprietaire = models.CharField(max_length=30, blank=True)
    telephone_proprio = models.CharField(max_length=30, blank=True)
    eau_regideso = models.BooleanField(default=False)
    elec_snel = models.BooleanField(default=False)
    sentinelle = models.BooleanField(default=False)
    parking = models.BooleanField(default=False)
    cloture = models.BooleanField(default=False)
    video_preuve = models.FileField(upload_to="videos_verification/", blank=True, null=True)
    carte_id_proprio = models.ImageField(upload_to="id_verif/")
    point_repere = models.CharField(max_length=255, default="")
    gps_lat = models.FloatField(null=True, blank=True)
    gps_long = models.FloatField(null=True, blank=True)
    motif_rejet = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)

    @property
    def ville_affichee(self):
        return self.ville_autre if self.ville == self.VilleChoices.AUTRE and self.ville_autre else self.ville

    def __str__(self):
        return f"{self.ville_affichee} - {self.commune} ({self.prix} {self.devise})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.code_immo:
            year = (self.created_at or timezone.now()).year
            self.code_immo = f"IC-{year}-{self.pk:03d}"
            type(self).objects.filter(pk=self.pk).update(code_immo=self.code_immo)

    @property
    def prix_label(self):
        return "Prix par mois" if self.type_transaction == self.TypeTransactionChoices.LOCATION else "Prix total"

    @property
    def is_public_status(self):
        return self.statut in {
            self.PublicationStatus.APPROUVEE,
            self.PublicationStatus.LOUE,
            self.PublicationStatus.VENDU,
        }

    @property
    def offre_label(self):
        return f"{self.get_categorie_bien_display()} en {self.get_type_transaction_display()}"


class Photo(models.Model):
    logement = models.ForeignKey(
        Logement,
        on_delete=models.CASCADE,
        related_name="photos",
    )
    image = models.ImageField(upload_to="logements_photos/")

    def __str__(self):
        return f"Photo {self.pk} - {self.logement}"


class ContactUnlock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contact_unlocks")
    logement = models.ForeignKey(Logement, on_delete=models.CASCADE, related_name="contact_unlocks")
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "logement"], name="unique_contact_unlock")
        ]

    def __str__(self):
        return f"{self.user} - {self.logement}"


class CommentaireAdmin(models.Model):
    logement = models.ForeignKey(
        Logement,
        on_delete=models.CASCADE,
        related_name="commentaires_admin",
    )
    auteur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="commentaires_admin",
    )
    message = models.TextField()
    read_by_owner = models.BooleanField(default=False)
    read_by_staff = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date_creation"]

    def __str__(self):
        return f"{self.auteur} - {self.logement}"


class Notification(models.Model):
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    logement = models.ForeignKey(
        Logement,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    titre = models.CharField(max_length=255)
    message = models.TextField()
    lien = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient} - {self.titre}"


class Signalement(models.Model):
    class MotifChoices(models.TextChoices):
        ARNAQUE = "ARNAQUE", "Arnaque"
        DEJA_LOUE = "DEJA_LOUE", "Deja loue"
        PRIX_INCORRECT = "PRIX_INCORRECT", "Prix incorrect"
        FAUSSE_INFO = "FAUSSE_INFO", "Fausse information"

    logement = models.ForeignKey(
        Logement,
        on_delete=models.CASCADE,
        related_name="signalements",
    )
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="signalements",
    )
    motif = models.CharField(max_length=30, choices=MotifChoices.choices)
    commentaire = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["logement", "utilisateur"], name="unique_signalement_par_utilisateur")
        ]

    def __str__(self):
        return f"{self.logement} - {self.get_motif_display()}"


class Favori(models.Model):
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favoris",
    )
    logement = models.ForeignKey(
        Logement,
        on_delete=models.CASCADE,
        related_name="favoris",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["utilisateur", "logement"], name="unique_favori_par_utilisateur")
        ]

    def __str__(self):
        return f"{self.utilisateur} - {self.logement}"


class MessageVisiteur(models.Model):
    logement = models.ForeignKey(
        Logement,
        on_delete=models.CASCADE,
        related_name="messages_visiteurs",
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_logement_messages",
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_logement_messages",
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender} -> {self.recipient} ({self.logement})"
