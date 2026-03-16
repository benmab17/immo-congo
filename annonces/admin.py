from django.contrib import admin

from .models import CommentaireAdmin, ContactUnlock, Favori, Logement, MessageVisiteur, Notification, Photo, Signalement


class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 1


@admin.register(Logement)
class LogementAdmin(admin.ModelAdmin):
    list_display = ("code_immo", "ville_affichee", "commune", "proprietaire", "verified_by", "approved_at", "rejected_at", "type_transaction", "prix", "devise", "disponibilite", "statut", "nb_chambres", "nb_salles_bain", "surface_m2")
    list_filter = (
        "ville",
        "type_transaction",
        "devise",
        "disponibilite",
        "statut",
        "eau_regideso",
        "elec_snel",
        "sentinelle",
        "parking",
        "cloture",
    )
    search_fields = ("code_immo", "adresse", "commune", "description", "contact_proprietaire", "telephone_proprio", "motif_rejet", "ville_autre", "verified_by__username")
    inlines = [PhotoInline]


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "logement")


@admin.register(ContactUnlock)
class ContactUnlockAdmin(admin.ModelAdmin):
    list_display = ("user", "logement", "unlocked_at")


@admin.register(CommentaireAdmin)
class CommentaireAdminModelAdmin(admin.ModelAdmin):
    list_display = ("logement", "auteur", "date_creation")
    search_fields = ("logement__commune", "auteur__username", "message")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "titre", "logement", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("recipient__username", "titre", "message")


@admin.register(Signalement)
class SignalementAdmin(admin.ModelAdmin):
    list_display = ("logement", "utilisateur", "motif", "created_at")
    list_filter = ("motif", "created_at")
    search_fields = ("logement__commune", "logement__ville_autre", "utilisateur__username", "commentaire")


@admin.register(Favori)
class FavoriAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "logement", "created_at")
    list_filter = ("created_at",)
    search_fields = ("utilisateur__username", "logement__commune", "logement__ville_autre")


@admin.register(MessageVisiteur)
class MessageVisiteurAdmin(admin.ModelAdmin):
    list_display = ("logement", "sender", "recipient", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("logement__commune", "sender__username", "recipient__username", "message")
