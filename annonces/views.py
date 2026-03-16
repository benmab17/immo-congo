import json
from functools import wraps

from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView, PasswordResetConfirmView
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import FormView, TemplateView

from .forms import (
    LogementForm,
    PhoneLoginForm,
    PhoneSignupForm,
    PhotoUploadForm,
    ProfileForm,
    SignalementForm,
    StyledPasswordChangeForm,
    StyledPasswordResetForm,
    StyledSetPasswordForm,
)
from .models import CommentaireAdmin, ContactUnlock, Favori, Logement, MessageVisiteur, Notification, Photo, Signalement


def resolve_media_url(value):
    if not value:
        return ""
    if isinstance(value, str):
        return value
    return getattr(value, "url", "") or str(value)


def attach_logement_image_url(logement):
    if getattr(logement, "image_url", ""):
        logement.image_url = resolve_media_url(logement.image_url)
        return logement
    main_photo = getattr(logement, "main_photo", None)
    image_value = getattr(main_photo, "image", None) if main_photo else None
    logement.image_url = resolve_media_url(image_value)
    return logement


DEFAULT_CITY_COMMUNES = {
    "Kinshasa": [
        "Gombe", "Limete", "Ngaliema", "Lingwala", "Kintambo", "Bandalungwa", "Barumbu",
        "Kalamu", "Kasavubu", "Kinshasa", "Kasa-Vubu", "Lemba", "Matete", "Masina",
        "Mont-Ngafula", "Ndjili", "Ngaba", "Ngaliema", "Ngiri-Ngiri", "Selembao",
    ],
    "Lubumbashi": ["Lubumbashi", "Kampemba", "Annexe", "Katuba", "Kenya", "Kamalondo", "Ruashi"],
    "Goma": ["Goma", "Karisimbi"],
    "Kolwezi": ["Dilala", "Manika"],
    "Kisangani": ["Makiso", "Mangobo", "Tshopo", "Kabondo", "Lubunga", "Kisangani"],
    "Mbuji-Mayi": ["Bipemba", "Diulu", "Kanshi", "Muya", "Dibindi"],
    "Kananga": ["Kananga", "Lukonga", "Katoka", "Ndesha", "Nganza"],
    "Bukavu": ["Ibanda", "Kadutu", "Bagira"],
    "Matadi": ["Matadi", "Nzanza", "Mvuzi"],
    "Boma": ["Kalamu", "Kabondo", "Nzadi", "Tiadi"],
    "Mbandaka": ["Mbandaka", "Wangata"],
    "Kindu": ["Kasuku", "Mikelenge", "Alunguli"],
    "Bunia": ["Mbunya", "Shari", "Nyakasanza"],
    "Uvira": ["Kalundu", "Mulongwe", "Kavimvira"],
    "Kikwit": ["Lukolela", "Nzinda", "Kazamba", "Lukemi"],
    "Tshikapa": ["Dibumba I", "Dibumba II", "Kanzala", "Mabondo", "Mbumba"],
    "Likasi": ["Likasi", "Kikula", "Panda", "Shituru"],
    "Kalemie": ["Kalemie", "Lukuga"],
    "Beni": ["Beni", "Ruwenzori", "Mulekera", "Beu"],
    "Butembo": ["Bulengera", "Kimemi", "Mususa", "Vulamba"],
    "Isiro": ["Kupa", "Mongbwalu", "Mambaya"],
}


MODERATOR_GROUP_NAME = "Mod\u00e9rateurs"
User = Logement._meta.get_field("proprietaire").remote_field.model


def staff_member_required(view_func):
    @wraps(view_func)
    @login_required(login_url="annonces:login")
    def wrapped(request, *args, **kwargs):
        user = request.user
        if user.is_superuser or user.groups.filter(name=MODERATOR_GROUP_NAME).exists():
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Acces reserve aux moderateurs.")

    return wrapped


def get_moderators():
    Group.objects.get_or_create(name=MODERATOR_GROUP_NAME)
    return User.objects.filter(
        Q(is_superuser=True) | Q(groups__name=MODERATOR_GROUP_NAME)
    ).distinct()


def user_can_view_private_logement(user, logement):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.groups.filter(name=MODERATOR_GROUP_NAME).exists():
        return True
    return logement.proprietaire_id == user.id


def get_public_notification_recipients(owner=None):
    queryset = User.objects.filter(is_active=True)
    if owner:
        queryset = queryset.exclude(id=owner.id)
    return queryset.distinct()


def notify_users(recipients, titre, message, logement=None, lien=""):
    notifications = []
    for recipient in recipients:
        notifications.append(
            Notification(
                recipient=recipient,
                logement=logement,
                titre=titre,
                message=message,
                lien=lien,
            )
        )
    if notifications:
        Notification.objects.bulk_create(notifications)


def build_trust_score(logement, photos_count=0):
    score = 20
    reasons = []

    if logement.statut == Logement.PublicationStatus.APPROUVEE:
        score += 30
        reasons.append("Annonce validée")
    if photos_count >= 5:
        score += 15
        reasons.append("Galerie complète")
    elif photos_count >= 3:
        score += 8
        reasons.append("Plusieurs photos")
    if logement.video_preuve:
        score += 12
        reasons.append("Vidéo fournie")
    if logement.carte_id_proprio:
        score += 8
        reasons.append("Identité vérifiable")
    if logement.gps_lat is not None and logement.gps_long is not None:
        score += 8
        reasons.append("GPS disponible")
    if logement.point_repere:
        score += 7
        reasons.append("Point de repère précis")

    if logement.eau_regideso and logement.elec_snel:
        score += 5
        reasons.append("Informations essentielles complètes")

    score = min(score, 100)
    if score >= 85:
        label = "Très fiable"
        tone = "emerald"
    elif score >= 65:
        label = "Fiable"
        tone = "blue"
    elif score >= 45:
        label = "Correct"
        tone = "amber"
    else:
        label = "À vérifier"
        tone = "slate"

    return {
        "value": score,
        "label": label,
        "tone": tone,
        "reasons": reasons[:4],
    }


def can_access_public_or_private_logement(request, logement):
    return logement.is_public_status or user_can_view_private_logement(request.user, logement)


def build_trust_score(logement, photos_count=0):
    score = 20
    reasons = []

    if logement.statut == Logement.PublicationStatus.APPROUVEE:
        score += 30
        reasons.append("Annonce verifiee")
    if photos_count >= 5:
        score += 15
        reasons.append("Galerie complete")
    elif photos_count >= 3:
        score += 8
        reasons.append("Plusieurs photos")
    if logement.video_preuve:
        score += 12
        reasons.append("Video fournie")
    if logement.carte_id_proprio:
        score += 8
        reasons.append("Identite verifiable")
    if logement.gps_lat is not None and logement.gps_long is not None:
        score += 8
        reasons.append("GPS disponible")
    if logement.point_repere:
        score += 7
        reasons.append("Point de repere precis")

    if logement.eau_regideso and logement.elec_snel:
        score += 5
        reasons.append("Informations essentielles completes")

    score = min(score, 100)
    if score >= 85:
        label = "Tres fiable"
        tone = "emerald"
    elif score >= 65:
        label = "Fiable"
        tone = "blue"
    elif score >= 45:
        label = "Correct"
        tone = "amber"
    else:
        label = "A verifier"
        tone = "slate"

    return {
        "value": score,
        "label": label,
        "tone": tone,
        "reasons": reasons[:4],
    }


def build_home_context(request):
    recent_threshold = timezone.now() - timezone.timedelta(days=2)
    show_history = request.GET.get("show_history") in {"1", "true", "on"}
    base_queryset = Logement.objects.filter(statut=Logement.PublicationStatus.APPROUVEE)
    logements_queryset = base_queryset.filter(
        disponibilite=Logement.DisponibiliteChoices.DISPONIBLE,
    )
    if show_history:
        logements_queryset = Logement.objects.filter(
            statut__in=[
                Logement.PublicationStatus.APPROUVEE,
                Logement.PublicationStatus.LOUE,
                Logement.PublicationStatus.VENDU,
            ]
        )
    logements_queryset = logements_queryset.prefetch_related(
        Prefetch("photos", queryset=Photo.objects.order_by("id"))
    )

    ville = request.GET.get("ville", "").strip()
    ville_autre = request.GET.get("ville_autre", "").strip()
    commune = request.GET.get("commune", "").strip()
    prix_min = request.GET.get("prix_min", "").strip()
    prix_max = request.GET.get("prix_max", "").strip()
    categorie_bien = request.GET.get("categorie_bien", "").strip()
    type_transaction = request.GET.get("type_transaction", "").strip()
    sort = request.GET.get("sort", "").strip()
    city_query = ville_autre if ville == Logement.VilleChoices.AUTRE else ville

    if city_query:
        logements_queryset = logements_queryset.filter(
            Q(ville__iexact=city_query) | Q(ville_autre__icontains=city_query)
        )
    if commune:
        logements_queryset = logements_queryset.filter(commune__icontains=commune)
    if categorie_bien:
        logements_queryset = logements_queryset.filter(categorie_bien=categorie_bien)
    if type_transaction:
        logements_queryset = logements_queryset.filter(type_transaction=type_transaction)
    if prix_min:
        try:
            logements_queryset = logements_queryset.filter(prix__gte=prix_min)
        except (TypeError, ValueError):
            pass
    if prix_max:
        try:
            logements_queryset = logements_queryset.filter(prix__lte=prix_max)
        except (TypeError, ValueError):
            pass

    communes_queryset = logements_queryset.exclude(commune="").exclude(commune__isnull=True)
    communes_suggestions = list(
        communes_queryset.values_list("commune", flat=True).distinct()
    )

    sort_options = {
        "recent": "-id",
        "prix_asc": "prix",
        "prix_desc": "-prix",
        "surface_desc": "-surface_m2",
    }
    logements_queryset = logements_queryset.order_by(sort_options.get(sort, "-id"))

    logements = list(logements_queryset)
    compare_ids = set(request.session.get("compare_logements", []))
    favorite_ids = set()
    if request.user.is_authenticated:
        favorite_ids = set(
            Favori.objects.filter(utilisateur=request.user, logement__in=logements)
            .values_list("logement_id", flat=True)
        )
    for logement in logements:
        logement.main_photo = logement.photos.first()
        attach_logement_image_url(logement)
        logement.is_favorite = logement.id in favorite_ids
        logement.is_compared = logement.id in compare_ids
        logement.trust_score = build_trust_score(logement, photos_count=logement.photos.count())
        logement.is_new = bool(logement.created_at and logement.created_at >= recent_threshold)

    ville_communes_map = {
        city: list(dict.fromkeys(communes))
        for city, communes in DEFAULT_CITY_COMMUNES.items()
    }
    for logement in logements_queryset.only("ville", "ville_autre", "commune"):
        ville_key = logement.ville_affichee
        if not ville_key or not logement.commune:
            continue
        ville_communes_map.setdefault(ville_key, [])
        if logement.commune not in ville_communes_map[ville_key]:
            ville_communes_map[ville_key].append(logement.commune)

    hero_stats = {
        "logements_verifies": Logement.objects.filter(
            statut=Logement.PublicationStatus.APPROUVEE
        ).count(),
        "agences_partenaires": User.objects.filter(
            is_active=True,
            logements__statut__in=[
                Logement.PublicationStatus.APPROUVEE,
                Logement.PublicationStatus.LOUE,
                Logement.PublicationStatus.VENDU,
            ],
        )
        .annotate(total_biens_publics=Count("logements", distinct=True))
        .filter(total_biens_publics__gte=3)
        .distinct()
        .count(),
        "proprietaires_satisfaits": User.objects.filter(is_active=True).count(),
    }
    result_summary = {
        "count": len(logements),
        "city_label": city_query or "toutes les villes",
        "contract_label": dict(Logement.TypeTransactionChoices.choices).get(type_transaction, "tous les contrats"),
        "category_label": categorie_bien or "toutes les categories",
        "sort_label": {
            "": "Plus recents",
            "prix_asc": "Prix croissant",
            "prix_desc": "Prix decroissant",
            "surface_desc": "Plus spacieux",
        }.get(sort, "Plus recents"),
    }
    smart_suggestions = []
    if not city_query:
        smart_suggestions.append({"label": "Kinshasa", "query": "?ville=Kinshasa"})
        smart_suggestions.append({"label": "Location", "query": "?type_transaction=LOCATION"})
        smart_suggestions.append({"label": "Appartement", "query": "?categorie_bien=Appartement"})
    else:
        if type_transaction != Logement.TypeTransactionChoices.LOCATION:
            smart_suggestions.append(
                {
                    "label": f"Location a {city_query}",
                    "query": f"?ville={city_query}&type_transaction=LOCATION",
                }
            )
        if type_transaction != Logement.TypeTransactionChoices.VENTE:
            smart_suggestions.append(
                {
                    "label": f"Vente a {city_query}",
                    "query": f"?ville={city_query}&type_transaction=VENTE",
                }
            )
    market_highlights = {
        "villes_couvertes": Logement.objects.exclude(statut=Logement.PublicationStatus.BROUILLON)
        .values_list("ville", flat=True)
        .distinct()
        .count(),
        "locations_actives": base_queryset.filter(type_transaction=Logement.TypeTransactionChoices.LOCATION).count(),
        "ventes_actives": base_queryset.filter(type_transaction=Logement.TypeTransactionChoices.VENTE).count(),
    }
    map_logements = [
        {
            "id": logement.id,
            "title": logement.offre_label,
            "price": f"{logement.prix} {logement.devise}",
            "ville": logement.ville_affichee,
            "commune": logement.commune,
            "lat": logement.gps_lat,
            "lng": logement.gps_long,
            "url": f"/logements/{logement.id}/",
        }
        for logement in logements
        if logement.gps_lat is not None and logement.gps_long is not None
    ]

    return {
        "default_image_url": "https://placehold.co/900x700/f8f7f2/003399?text=Immo+Congo",
        "logements": logements,
        "villes_choix": [choice for choice, _ in Logement.VilleChoices.choices],
        "communes_suggestions": communes_suggestions,
        "ville_communes_map_json": json.dumps(ville_communes_map),
        "filters": {
            "ville": ville,
            "ville_autre": ville_autre,
            "commune": commune,
            "prix_min": prix_min,
            "prix_max": prix_max,
            "categorie_bien": categorie_bien,
            "type_transaction": type_transaction,
            "show_history": show_history,
            "sort": sort,
        },
        "categories_bien": [choice for choice, _ in Logement.CategorieBienChoices.choices],
        "types_transaction": [choice for choice, _ in Logement.TypeTransactionChoices.choices],
        "hero_stats": hero_stats,
        "result_summary": result_summary,
        "smart_suggestions": smart_suggestions[:3],
        "market_highlights": market_highlights,
        "map_logements_json": json.dumps(map_logements),
    }


def home(request):
    context = build_home_context(request)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_to_string("annonces/_home_results.html", context, request=request)
        return JsonResponse(
            {
                "ok": True,
                "html": html,
                "map_logements_json": context["map_logements_json"],
                "result_summary": context["result_summary"],
            }
        )
    return render(request, "annonces/home.html", context)


def logement_detail(request, id):
    logement = get_object_or_404(
        Logement.objects.prefetch_related(
            Prefetch("photos", queryset=Photo.objects.order_by("id")),
            "signalements__utilisateur",
        ),
        id=id,
    )
    if (
        not can_access_public_or_private_logement(request, logement)
    ):
        messages.error(request, "Cette annonce est en cours de validation ou n'est plus disponible")
        return redirect("annonces:home")
    photos = list(logement.photos.all())
    trust_score = build_trust_score(logement, photos_count=len(photos))
    is_unlocked = request.user.is_authenticated and ContactUnlock.objects.filter(
        user=request.user,
        logement=logement,
    ).exists()
    has_signaled = request.user.is_authenticated and logement.signalements.filter(utilisateur=request.user).exists()
    is_favorite = request.user.is_authenticated and Favori.objects.filter(
        utilisateur=request.user,
        logement=logement,
    ).exists()
    is_compared = logement.id in request.session.get("compare_logements", [])
    similar_queryset = (
        Logement.objects.filter(
            statut__in=[
                Logement.PublicationStatus.APPROUVEE,
                Logement.PublicationStatus.LOUE,
                Logement.PublicationStatus.VENDU,
            ]
        )
        .exclude(id=logement.id)
        .prefetch_related(Prefetch("photos", queryset=Photo.objects.order_by("id")))
    )
    if logement.ville or logement.ville_autre:
        similar_queryset = similar_queryset.filter(
            Q(ville=logement.ville) | Q(ville_autre=logement.ville_autre)
        )
    if logement.categorie_bien:
        similar_queryset = similar_queryset.filter(categorie_bien=logement.categorie_bien)
    similar_logements = list(similar_queryset.order_by("-id")[:3])
    similar_favorite_ids = set()
    if request.user.is_authenticated and similar_logements:
        similar_favorite_ids = set(
            Favori.objects.filter(utilisateur=request.user, logement__in=similar_logements)
            .values_list("logement_id", flat=True)
        )
    for similar in similar_logements:
        similar.main_photo = similar.photos.first()
        attach_logement_image_url(similar)
        similar.is_favorite = similar.id in similar_favorite_ids
    return render(
        request,
        "annonces/details.html",
        {
            "default_image_url": "https://placehold.co/1200x900/f8f7f2/003399?text=Immo+Congo",
            "logement": logement,
            "photos": photos,
            "is_unlocked": is_unlocked,
            "has_signaled": has_signaled,
            "is_favorite": is_favorite,
            "is_compared": is_compared,
            "signalement_form": SignalementForm(),
            "similar_logements": similar_logements,
            "trust_score": trust_score,
            "trust_signals": {
                "photos_count": len(photos),
                "has_video": bool(logement.video_preuve),
                "has_gps": bool(logement.gps_lat and logement.gps_long),
                "has_landmark": bool(logement.point_repere),
                "verified_by": logement.verified_by,
            },
        },
    )


@login_required
def toggle_compare(request, logement_id):
    if request.method != "POST":
        return JsonResponse({"ok": False, "message": "Methode non autorisee."}, status=405)

    logement = get_object_or_404(Logement, id=logement_id)
    if not can_access_public_or_private_logement(request, logement):
        return JsonResponse({"ok": False, "message": "Annonce inaccessible."}, status=403)

    compare_ids = request.session.get("compare_logements", [])
    if logement_id in compare_ids:
        compare_ids.remove(logement_id)
        request.session["compare_logements"] = compare_ids
        request.session.modified = True
        return JsonResponse({"ok": True, "is_compared": False, "count": len(compare_ids)})

    if len(compare_ids) >= 3:
        return JsonResponse(
            {"ok": False, "message": "Vous pouvez comparer au maximum 3 biens."},
            status=400,
        )

    compare_ids.append(logement_id)
    request.session["compare_logements"] = compare_ids
    request.session.modified = True
    return JsonResponse({"ok": True, "is_compared": True, "count": len(compare_ids)})


def compare_view(request):
    compare_ids = request.session.get("compare_logements", [])
    logements = list(
        Logement.objects.filter(id__in=compare_ids)
        .prefetch_related(Prefetch("photos", queryset=Photo.objects.order_by("id")))
        .select_related("proprietaire")
    )
    logements = [logement for logement in logements if can_access_public_or_private_logement(request, logement)]
    for logement in logements:
        logement.main_photo = logement.photos.first()
        attach_logement_image_url(logement)
        logement.trust_score = build_trust_score(logement, photos_count=logement.photos.count())
    return render(request, "annonces/compare.html", {"logements": logements})


def proprietaire_profile(request, user_id):
    proprietaire = get_object_or_404(User, id=user_id, is_active=True)
    logements = list(
        Logement.objects.filter(
            proprietaire=proprietaire,
            statut__in=[
                Logement.PublicationStatus.APPROUVEE,
                Logement.PublicationStatus.LOUE,
                Logement.PublicationStatus.VENDU,
            ],
        )
        .prefetch_related(Prefetch("photos", queryset=Photo.objects.order_by("id")))
        .order_by("-id")
    )
    for logement in logements:
        logement.main_photo = logement.photos.first()
        attach_logement_image_url(logement)
        logement.trust_score = build_trust_score(logement, photos_count=logement.photos.count())
    stats = {
        "total": len(logements),
        "en_ligne": len([item for item in logements if item.statut == Logement.PublicationStatus.APPROUVEE]),
        "historique": len([item for item in logements if item.statut in {Logement.PublicationStatus.LOUE, Logement.PublicationStatus.VENDU}]),
    }
    return render(
        request,
        "annonces/proprietaire_profile.html",
        {
            "proprietaire": proprietaire,
            "logements": logements,
            "stats": stats,
        },
    )


@login_required
def messagerie_view(request):
    received_unread = request.user.received_logement_messages.filter(is_read=False)
    threads_map = {}
    messages_queryset = (
        MessageVisiteur.objects.filter(Q(sender=request.user) | Q(recipient=request.user))
        .select_related("logement", "sender", "recipient")
        .order_by("-created_at")
    )
    for message in messages_queryset:
        other_user = message.recipient if message.sender_id == request.user.id else message.sender
        key = (message.logement_id, other_user.id)
        if key not in threads_map:
            threads_map[key] = {
                "logement": message.logement,
                "other_user": other_user,
                "last_message": message,
                "unread_count": 0,
            }
        if message.recipient_id == request.user.id and not message.is_read:
            threads_map[key]["unread_count"] += 1
    received_unread.update(is_read=True)
    threads = list(threads_map.values())
    return render(request, "annonces/messagerie.html", {"threads": threads})


@login_required
def conversation_view(request, logement_id, user_id):
    logement = get_object_or_404(Logement, id=logement_id)
    if not logement.proprietaire:
        raise PermissionDenied("Conversation inaccessible.")
    other_user = get_object_or_404(User, id=user_id, is_active=True)

    if request.user.id not in {logement.proprietaire_id, other_user.id}:
        raise PermissionDenied("Conversation inaccessible.")
    if request.user.id == other_user.id and request.user.id != logement.proprietaire_id:
        raise PermissionDenied("Conversation inaccessible.")

    messages_queryset = (
        MessageVisiteur.objects.filter(logement=logement)
        .filter(
            (Q(sender=request.user) & Q(recipient=other_user))
            | (Q(sender=other_user) & Q(recipient=request.user))
        )
        .select_related("sender", "recipient")
        .order_by("created_at")
    )

    MessageVisiteur.objects.filter(
        logement=logement,
        sender=other_user,
        recipient=request.user,
        is_read=False,
    ).update(is_read=True)

    if request.method == "POST":
        message = (request.POST.get("message") or "").strip()
        if message:
            MessageVisiteur.objects.create(
                logement=logement,
                sender=request.user,
                recipient=other_user,
                message=message,
            )
            if other_user != request.user:
                notify_users(
                    [other_user],
                    "Nouveau message sur une annonce",
                    f"Vous avez recu un nouveau message concernant l'annonce a {logement.ville_affichee}, {logement.commune}.",
                    logement=logement,
                    lien=f"/messages/logements/{logement.id}/{request.user.id}/",
                )
            return redirect("annonces:conversation", logement_id=logement.id, user_id=other_user.id)
        messages.error(request, "Le message ne peut pas etre vide.")

    return render(
        request,
        "annonces/conversation.html",
        {
            "logement": logement,
            "other_user": other_user,
            "messages_thread": list(messages_queryset),
        },
    )


@login_required
def contact_owner_message(request, logement_id):
    logement = get_object_or_404(Logement, id=logement_id)
    if not logement.proprietaire:
        raise PermissionDenied("Annonce inaccessible.")
    if not can_access_public_or_private_logement(request, logement):
        raise PermissionDenied("Annonce inaccessible.")
    if request.user == logement.proprietaire:
        messages.info(request, "Vous etes le proprietaire de cette annonce.")
        return redirect("annonces:details", id=logement.id)
    if request.method == "POST":
        message = (request.POST.get("message") or "").strip()
        if message:
            MessageVisiteur.objects.create(
                logement=logement,
                sender=request.user,
                recipient=logement.proprietaire,
                message=message,
            )
            notify_users(
                [logement.proprietaire],
                "Nouveau message visiteur",
                f"Un visiteur vous a ecrit au sujet de votre annonce a {logement.ville_affichee}, {logement.commune}.",
                logement=logement,
                lien=f"/messages/logements/{logement.id}/{request.user.id}/",
            )
            messages.success(request, "Votre message a bien ete envoye au proprietaire.")
        else:
            messages.error(request, "Le message ne peut pas etre vide.")
    return redirect("annonces:conversation", logement_id=logement.id, user_id=logement.proprietaire.id)


@login_required
def create_logement(request):
    form = LogementForm(request.POST or None, request.FILES or None)
    photo_form = PhotoUploadForm(request.POST or None, request.FILES or None, existing_count=0)

    if request.method == "POST" and form.is_valid() and photo_form.is_valid():
        logement = form.save(commit=False)
        logement.proprietaire = request.user
        logement.statut = Logement.PublicationStatus.EN_ATTENTE
        logement.motif_rejet = None
        logement.verified_by = None
        logement.approved_at = None
        logement.rejected_at = None
        logement.contact_proprietaire = logement.telephone_proprio
        logement.save()

        for image in request.FILES.getlist("photos"):
            Photo.objects.create(logement=logement, image=image)

        notify_users(
            get_moderators(),
            "Nouvelle annonce a verifier",
            f"Une nouvelle annonce a ete soumise a {logement.ville_affichee}, {logement.commune}.",
            logement=logement,
            lien="/gestion-admin/",
        )

        messages.success(
            request,
            "Votre annonce a bien ete soumise. Elle est maintenant en attente de verification par l'equipe Immo Congo. "
            "Vous serez informe(e) une fois la validation terminee."
        )
        return redirect("annonces:details", id=logement.id)

    return render(
        request,
        "annonces/create_logement.html",
        {
            "form": form,
            "photo_form": photo_form,
            "ville_communes_map_json": json.dumps(DEFAULT_CITY_COMMUNES),
        },
    )


@login_required
def edit_logement(request, id):
    logement = get_object_or_404(Logement, id=id, proprietaire=request.user)
    form = LogementForm(request.POST or None, request.FILES or None, instance=logement)
    photo_form = PhotoUploadForm(
        request.POST or None,
        request.FILES or None,
        existing_count=logement.photos.count(),
    )

    if request.method == "POST" and form.is_valid() and photo_form.is_valid():
        logement = form.save(commit=False)
        logement.contact_proprietaire = logement.telephone_proprio
        logement.statut = Logement.PublicationStatus.EN_ATTENTE
        logement.motif_rejet = None
        logement.verified_by = None
        logement.approved_at = None
        logement.rejected_at = None
        logement.save()

        for image in request.FILES.getlist("photos"):
            Photo.objects.create(logement=logement, image=image)

        notify_users(
            get_moderators(),
            "Annonce modifiee a verifier",
            f"Une annonce modifiee a ete renvoyee en verification a {logement.ville_affichee}, {logement.commune}.",
            logement=logement,
            lien="/gestion-admin/",
        )

        messages.success(
            request,
            "Vos modifications ont bien ete enregistrees. L'annonce a ete renvoyee en verification avant sa remise en ligne."
        )
        return redirect("annonces:mes_annonces")

    return render(
        request,
        "annonces/create_logement.html",
        {
            "form": form,
            "photo_form": photo_form,
            "is_edit": True,
            "logement": logement,
            "ville_communes_map_json": json.dumps(DEFAULT_CITY_COMMUNES),
        },
    )


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("annonces:home")

    form = PhoneSignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Votre compte a \u00e9t\u00e9 cr\u00e9\u00e9.")
        return redirect("annonces:home")
    return render(request, "annonces/signup.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("annonces:home")

    next_url = request.GET.get("next") or request.POST.get("next") or ""
    form = PhoneLoginForm(request.POST or None, request=request)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        messages.success(request, "Connexion r\u00e9ussie.")
        return redirect(next_url or "annonces:home")
    return render(request, "annonces/login.html", {"form": form, "next": next_url})


def logout_view(request):
    logout(request)
    messages.success(request, "Vous \u00eates d\u00e9connect\u00e9.")
    return redirect("annonces:home")


@login_required
def unlock_contact(request, logement_id):
    logement = get_object_or_404(Logement, id=logement_id)
    if logement.statut != Logement.PublicationStatus.APPROUVEE:
        messages.error(request, "Le contact n'est pas disponible pour cette annonce.")
        return redirect("annonces:details", id=logement_id)
    ContactUnlock.objects.get_or_create(user=request.user, logement=logement)
    messages.success(request, "Contact debloque. Paiement simule avec succes.")
    return redirect("annonces:details", id=logement_id)


@login_required
def signaler_annonce(request, logement_id):
    logement = get_object_or_404(Logement, id=logement_id)
    if (
        logement.statut not in {
            Logement.PublicationStatus.APPROUVEE,
            Logement.PublicationStatus.LOUE,
            Logement.PublicationStatus.VENDU,
        }
        and not user_can_view_private_logement(request.user, logement)
    ):
        raise PermissionDenied("Cette annonce n'est pas accessible.")
    if request.method != "POST":
        return redirect("annonces:details", id=logement_id)

    existing_signalement = Signalement.objects.filter(logement=logement, utilisateur=request.user).first()
    if existing_signalement:
        messages.info(request, "Vous avez deja signale cette annonce.")
        return redirect("annonces:details", id=logement_id)

    form = SignalementForm(request.POST)
    if form.is_valid():
        signalement = form.save(commit=False)
        signalement.logement = logement
        signalement.utilisateur = request.user
        signalement.save()
        notify_users(
            get_moderators(),
            "Nouvelle alerte annonce",
            f"Une annonce a ete signalee a {logement.ville_affichee}, {logement.commune}.",
            logement=logement,
            lien="/gestion-admin/",
        )
        messages.success(request, "Le signalement a bien ete envoye a l'equipe de moderation.")
    else:
        messages.error(request, "Impossible d'envoyer le signalement. Verifiez les informations saisies.")
    return redirect("annonces:details", id=logement_id)


@login_required
def toggle_favori(request, logement_id):
    if request.method != "POST":
        return JsonResponse({"ok": False, "message": "Methode non autorisee."}, status=405)

    logement = get_object_or_404(Logement, id=logement_id)
    if (
        logement.statut not in {
            Logement.PublicationStatus.APPROUVEE,
            Logement.PublicationStatus.LOUE,
            Logement.PublicationStatus.VENDU,
        }
        and not user_can_view_private_logement(request.user, logement)
    ):
        return JsonResponse({"ok": False, "message": "Annonce inaccessible."}, status=403)

    favori, created = Favori.objects.get_or_create(utilisateur=request.user, logement=logement)
    if created:
        return JsonResponse({"ok": True, "is_favorite": True, "message": "Annonce ajoutee aux favoris."})

    favori.delete()
    return JsonResponse({"ok": True, "is_favorite": False, "message": "Annonce retiree des favoris."})


@login_required
def update_listing_status(request, id, target_status):
    if request.method != "POST":
        return redirect("annonces:mes_annonces")

    logement = get_object_or_404(Logement, id=id, proprietaire=request.user)
    allowed_statuses = {
        Logement.PublicationStatus.LOUE: Logement.DisponibiliteChoices.LOUE,
        Logement.PublicationStatus.VENDU: Logement.DisponibiliteChoices.VENDU,
    }

    if target_status not in allowed_statuses:
        messages.error(request, "Statut non autoris\u00e9.")
        return redirect("annonces:mes_annonces")

    logement.statut = target_status
    logement.disponibilite = allowed_statuses[target_status]
    logement.save(update_fields=["statut", "disponibilite"])
    messages.success(request, "Le statut du bien a \u00e9t\u00e9 mis \u00e0 jour.")
    return redirect("annonces:mes_annonces")


@login_required
def mes_annonces(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    annonces = list(
        Logement.objects.filter(proprietaire=request.user)
        .prefetch_related(
            Prefetch(
                "commentaires_admin",
                queryset=CommentaireAdmin.objects.select_related("auteur").order_by("date_creation"),
            )
        )
        .order_by("-id")
    )
    unread_message_ids = []
    for annonce in annonces:
        annonce.admin_comment_count = 0
        for commentaire in annonce.commentaires_admin.all():
            if commentaire.auteur != request.user and not commentaire.read_by_owner:
                annonce.admin_comment_count += 1
                unread_message_ids.append(commentaire.id)
    if unread_message_ids:
        CommentaireAdmin.objects.filter(id__in=unread_message_ids).update(read_by_owner=True)
    return render(request, "annonces/mes_annonces.html", {"annonces": annonces})


@staff_member_required
def tableau_moderation(request):
    Group.objects.get_or_create(name=MODERATOR_GROUP_NAME)
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    ville = request.GET.get("ville", "").strip()
    type_transaction = request.GET.get("type_transaction", "").strip()
    categorie_bien = request.GET.get("categorie_bien", "").strip()
    search = request.GET.get("search", "").strip()

    if request.method == "POST":
        annonce_id = request.POST.get("logement_id")
        action = request.POST.get("action")
        logement = get_object_or_404(Logement, id=annonce_id)

        if action == "approve":
            logement.statut = Logement.PublicationStatus.APPROUVEE
            logement.motif_rejet = None
            logement.verified_by = request.user
            logement.approved_at = timezone.now()
            logement.rejected_at = None
            logement.save(update_fields=["statut", "motif_rejet", "verified_by", "approved_at", "rejected_at"])
            if logement.proprietaire:
                notify_users(
                    [logement.proprietaire],
                    "Annonce approuvee",
                    f"Votre annonce a {logement.ville_affichee}, {logement.commune} a ete approuvee et mise en ligne.",
                    logement=logement,
                    lien="/mes-annonces/",
                )
            notify_users(
                get_public_notification_recipients(owner=logement.proprietaire),
                "Nouveau bien disponible",
                f"{logement.offre_label} disponible a {logement.ville_affichee}, {logement.commune}.",
                logement=logement,
                lien=f"/logements/{logement.id}/",
            )
            messages.success(request, "Annonce approuvee et mise en ligne.")
        elif action == "reject":
            logement.statut = Logement.PublicationStatus.REJETEE
            logement.motif_rejet = (request.POST.get("motif_rejet") or "").strip() or "Motif non precise."
            logement.verified_by = request.user
            logement.rejected_at = timezone.now()
            logement.approved_at = None
            logement.save(update_fields=["statut", "motif_rejet", "verified_by", "approved_at", "rejected_at"])
            if logement.proprietaire:
                notify_users(
                    [logement.proprietaire],
                    "Annonce rejetee",
                    f"Votre annonce a {logement.ville_affichee}, {logement.commune} a ete rejetee. Consultez le motif et le chat.",
                    logement=logement,
                    lien="/mes-annonces/",
                )
            messages.success(request, "Annonce rejetee. Le proprietaire peut corriger et republier.")
        elif action == "ban_user" and logement.proprietaire:
            owner = logement.proprietaire
            owner.is_active = False
            owner.save(update_fields=["is_active"])
            Logement.objects.filter(proprietaire=owner).update(
                statut=Logement.PublicationStatus.BROUILLON,
                disponibilite=Logement.DisponibiliteChoices.INDISPONIBLE,
            )
            messages.success(request, "Le proprietaire a ete banni et toutes ses annonces ont ete retirees du site.")

        return redirect("annonces:gestion_admin")

    annonces = (
        Logement.objects.filter(statut=Logement.PublicationStatus.EN_ATTENTE)
        .prefetch_related(
            Prefetch(
                "commentaires_admin",
                queryset=CommentaireAdmin.objects.select_related("auteur").order_by("date_creation"),
            ),
            Prefetch(
                "signalements",
                queryset=Signalement.objects.select_related("utilisateur").order_by("-created_at"),
            ),
        )
    )
    if ville:
        annonces = annonces.filter(Q(ville__iexact=ville) | Q(ville_autre__icontains=ville))
    if type_transaction:
        annonces = annonces.filter(type_transaction=type_transaction)
    if categorie_bien:
        annonces = annonces.filter(categorie_bien=categorie_bien)
    if search:
        annonces = annonces.filter(
            Q(commune__icontains=search)
            | Q(ville__icontains=search)
            | Q(ville_autre__icontains=search)
            | Q(proprietaire__username__icontains=search)
            | Q(telephone_proprio__icontains=search)
        )
    annonces = annonces.order_by("-id")
    annonces = list(annonces)
    unread_staff_ids = []
    for annonce in annonces:
        annonce.signalement_count = len(list(annonce.signalements.all()))
        annonce.owner_unread_count = 0
        for commentaire in annonce.commentaires_admin.all():
            if commentaire.auteur == annonce.proprietaire and not commentaire.read_by_staff:
                annonce.owner_unread_count += 1
                unread_staff_ids.append(commentaire.id)
    if unread_staff_ids:
        CommentaireAdmin.objects.filter(id__in=unread_staff_ids).update(read_by_staff=True)

    base_stats_queryset = Logement.objects.all()
    if ville:
        base_stats_queryset = base_stats_queryset.filter(Q(ville__iexact=ville) | Q(ville_autre__icontains=ville))
    if type_transaction:
        base_stats_queryset = base_stats_queryset.filter(type_transaction=type_transaction)
    if categorie_bien:
        base_stats_queryset = base_stats_queryset.filter(categorie_bien=categorie_bien)
    if search:
        base_stats_queryset = base_stats_queryset.filter(
            Q(commune__icontains=search)
            | Q(ville__icontains=search)
            | Q(ville_autre__icontains=search)
            | Q(proprietaire__username__icontains=search)
            | Q(telephone_proprio__icontains=search)
        )

    stats = {
        "a_verifier": len(annonces),
        "total_en_ligne": base_stats_queryset.filter(statut=Logement.PublicationStatus.APPROUVEE).count(),
        "total_historique": base_stats_queryset.filter(
            statut__in=[Logement.PublicationStatus.LOUE, Logement.PublicationStatus.VENDU]
        ).count(),
    }
    alertes = list(
        Signalement.objects.select_related("logement", "utilisateur", "logement__proprietaire")
        .prefetch_related(Prefetch("logement__photos", queryset=Photo.objects.order_by("id")))
        .order_by("-created_at")
    )
    for alerte in alertes:
        alerte.main_photo = alerte.logement.photos.first() if hasattr(alerte.logement, "photos") else None
    return render(
        request,
        "annonces/tableau_moderation.html",
        {
            "annonces": annonces,
            "alertes": alertes,
            "stats": stats,
            "session_moderateur": request.user.get_full_name() or request.user.get_username(),
            "filters": {
                "ville": ville,
                "type_transaction": type_transaction,
                "categorie_bien": categorie_bien,
                "search": search,
            },
            "villes_choix": [choice for choice, _ in Logement.VilleChoices.choices if choice != Logement.VilleChoices.AUTRE],
            "categories_bien": [choice for choice, _ in Logement.CategorieBienChoices.choices],
            "types_transaction": [choice for choice, _ in Logement.TypeTransactionChoices.choices],
        },
    )


@staff_member_required
def envoyer_message_moderation(request, logement_id):
    if request.method != "POST":
        return redirect("annonces:gestion_admin")

    logement = get_object_or_404(Logement, id=logement_id)
    message = (request.POST.get("message") or "").strip()
    if not message:
        messages.error(request, "Le message du moderateur ne peut pas etre vide.")
        return redirect("annonces:gestion_admin")

    CommentaireAdmin.objects.create(
        logement=logement,
        auteur=request.user,
        message=message,
        read_by_owner=False,
        read_by_staff=True,
    )
    if logement.proprietaire:
        notify_users(
            [logement.proprietaire],
            "Nouveau message de l'administration",
            f"L'administration vous a laisse un message concernant votre annonce a {logement.ville_affichee}, {logement.commune}.",
            logement=logement,
            lien="/mes-annonces/",
        )
    messages.success(request, "Message envoye au proprietaire.")
    return redirect("annonces:gestion_admin")


@login_required
def repondre_commentaire(request, logement_id):
    if request.method != "POST":
        return redirect("annonces:mes_annonces")

    logement = get_object_or_404(Logement, id=logement_id, proprietaire=request.user)
    message = (request.POST.get("message") or "").strip()
    if not message:
        messages.error(request, "Votre reponse ne peut pas etre vide.")
        return redirect("annonces:mes_annonces")

    CommentaireAdmin.objects.create(
        logement=logement,
        auteur=request.user,
        message=message,
        read_by_owner=True,
        read_by_staff=False,
    )
    notify_users(
        get_moderators(),
        "Nouvelle reponse proprietaire",
        f"Le proprietaire a repondu dans le chat de l'annonce a {logement.ville_affichee}, {logement.commune}.",
        logement=logement,
        lien="/gestion-admin/",
    )
    messages.success(request, "Votre reponse a bien ete envoyee.")
    return redirect("annonces:mes_annonces")


@login_required
def notifications_view(request):
    notifications = request.user.notifications.select_related("logement").order_by("-created_at")
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, "annonces/notifications.html", {"notifications": notifications})


@login_required
def mon_profil(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Votre profil a bien ete mis a jour.")
        return redirect("annonces:mon_profil")
    return render(request, "annonces/mon_profil.html", {"form": form})


@login_required
def mes_favoris(request):
    favoris = (
        Favori.objects.filter(utilisateur=request.user)
        .select_related("logement")
        .prefetch_related(Prefetch("logement__photos", queryset=Photo.objects.order_by("id")))
    )
    favoris = list(favoris)
    for favori in favoris:
        favori.logement.main_photo = favori.logement.photos.first()
    return render(request, "annonces/mes_favoris.html", {"favoris": favoris})


class SitePasswordChangeView(PasswordChangeView):
    form_class = StyledPasswordChangeForm
    template_name = "annonces/password_change.html"
    success_url = reverse_lazy("annonces:mon_profil")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Votre mot de passe a ete mis a jour avec succes !")
        return response


class SitePasswordResetView(FormView):
    form_class = StyledPasswordResetForm
    template_name = "annonces/password_reset.html"
    success_url = reverse_lazy("annonces:password_reset_done")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("annonces:mon_profil")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.save(
            request=self.request,
            use_https=self.request.is_secure(),
            from_email=None,
            email_template_name="registration/password_reset_email.html",
            subject_template_name="registration/password_reset_subject.txt",
        )
        return super().form_valid(form)


class SitePasswordResetConfirmView(PasswordResetConfirmView):
    form_class = StyledSetPasswordForm
    template_name = "annonces/password_reset_confirm.html"
    success_url = reverse_lazy("annonces:password_reset_complete")


class SitePasswordResetDoneView(TemplateView):
    template_name = "annonces/password_reset_done.html"


class SitePasswordResetCompleteView(TemplateView):
    template_name = "annonces/password_reset_complete.html"


def about_view(request):
    return render(request, "annonces/about.html")


def terms_view(request):
    return render(request, "annonces/terms.html")


def privacy_view(request):
    return render(request, "annonces/privacy.html")


def contact_view(request):
    return render(request, "annonces/contact.html")


def safety_view(request):
    return render(request, "annonces/safety.html")


def pricing_view(request):
    return render(request, "annonces/pricing.html")


def help_center_view(request):
    return render(request, "annonces/help_center.html")


def agencies_view(request):
    return render(request, "annonces/agencies.html")


def premium_view(request):
    return render(request, "annonces/premium.html")
