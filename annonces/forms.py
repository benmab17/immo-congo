from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm

from .models import Logement, Photo, Signalement


User = get_user_model()


BASE_INPUT_CSS = (
    "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 "
    "text-sm outline-none transition focus:border-primary focus:bg-white"
)


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    default_error_messages = {
        "invalid": "Aucun fichier valide n'a été envoyé.",
        "missing": "Aucun fichier n'a été envoyé.",
        "empty": "Le fichier sélectionné est vide.",
        "max_length": "Le nom du fichier est trop long.",
        "contradiction": "Veuillez choisir un seul mode d’envoi.",
    }

    def clean(self, data, initial=None):
        if not data:
            return []
        if not isinstance(data, (list, tuple)):
            data = [data]
        single_file_clean = super().clean
        return [single_file_clean(item, initial) for item in data if item]


class PhoneSignupForm(forms.Form):
    phone = forms.CharField(
        max_length=30,
        label="Num\u00e9ro de t\u00e9l\u00e9phone",
        widget=forms.TextInput(attrs={"class": BASE_INPUT_CSS, "placeholder": "+243..."}),
    )
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": BASE_INPUT_CSS}),
    )
    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={"class": BASE_INPUT_CSS}),
    )

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        if User.objects.filter(username=phone).exists():
            raise forms.ValidationError("Ce num\u00e9ro est d\u00e9j\u00e0 utilis\u00e9.")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            self.add_error("password2", "Les mots de passe ne correspondent pas.")
        return cleaned_data

    def save(self):
        phone = self.cleaned_data["phone"]
        password = self.cleaned_data["password1"]
        return User.objects.create_user(username=phone, first_name=phone, password=password)


class PhoneLoginForm(forms.Form):
    phone = forms.CharField(
        max_length=30,
        label="Num\u00e9ro de t\u00e9l\u00e9phone",
        widget=forms.TextInput(attrs={"class": BASE_INPUT_CSS, "placeholder": "+243..."}),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": BASE_INPUT_CSS}),
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        self.user = None

    def clean(self):
        cleaned_data = super().clean()
        phone = cleaned_data.get("phone", "").strip()
        password = cleaned_data.get("password")
        if phone and password:
            self.user = authenticate(self.request, username=phone, password=password)
            if self.user is None:
                raise forms.ValidationError("Num\u00e9ro ou mot de passe invalide.")
        return cleaned_data

    def get_user(self):
        return self.user


class ProfileForm(forms.ModelForm):
    phone = forms.CharField(
        max_length=30,
        label="Numéro de téléphone",
        widget=forms.TextInput(attrs={"class": BASE_INPUT_CSS, "placeholder": "+243..."}),
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": BASE_INPUT_CSS, "placeholder": "Votre prenom"}),
            "last_name": forms.TextInput(attrs={"class": BASE_INPUT_CSS, "placeholder": "Votre nom"}),
            "email": forms.EmailInput(attrs={"class": BASE_INPUT_CSS, "placeholder": "nom@exemple.com"}),
        }
        labels = {
            "first_name": "Prénom",
            "last_name": "Nom",
            "email": "Adresse e-mail",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["phone"].initial = self.instance.username

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        if not phone:
            raise forms.ValidationError("Le numéro de téléphone est obligatoire.")
        queryset = User.objects.exclude(pk=self.instance.pk).filter(username=phone)
        if queryset.exists():
            raise forms.ValidationError("Ce numero de telephone est deja utilise.")
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["phone"]
        if commit:
            user.save()
        return user


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": BASE_INPUT_CSS})
        self.fields["old_password"].label = "Ancien mot de passe"
        self.fields["new_password1"].label = "Nouveau mot de passe"
        self.fields["new_password2"].label = "Confirmation du nouveau mot de passe"
        self.fields["new_password1"].help_text = (
            "<ul class='list-disc space-y-1 pl-5'>"
            "<li>Votre mot de passe ne doit pas etre trop proche de vos informations personnelles.</li>"
            "<li>Votre mot de passe doit contenir au moins 8 caracteres.</li>"
            "<li>Votre mot de passe ne doit pas etre un mot de passe couramment utilise.</li>"
            "<li>Votre mot de passe ne peut pas etre uniquement numerique.</li>"
            "</ul>"
        )


class StyledPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].label = "Adresse e-mail de récupération"
        self.fields["email"].widget.attrs.update(
            {
                "class": BASE_INPUT_CSS,
                "placeholder": "nom@exemple.com",
            }
        )


class StyledSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": BASE_INPUT_CSS})
        self.fields["new_password1"].label = "Nouveau mot de passe"
        self.fields["new_password2"].label = "Confirmation du nouveau mot de passe"
        self.fields["new_password1"].help_text = (
            "<ul class='list-disc space-y-1 pl-5'>"
            "<li>Votre mot de passe ne doit pas etre trop proche de vos informations personnelles.</li>"
            "<li>Votre mot de passe doit contenir au moins 8 caracteres.</li>"
            "<li>Votre mot de passe ne doit pas etre un mot de passe couramment utilise.</li>"
            "<li>Votre mot de passe ne peut pas etre uniquement numerique.</li>"
            "</ul>"
        )


class SignalementForm(forms.ModelForm):
    class Meta:
        model = Signalement
        fields = ["motif", "commentaire"]
        widgets = {
            "motif": forms.Select(attrs={"class": BASE_INPUT_CSS}),
            "commentaire": forms.Textarea(
                attrs={
                    "class": BASE_INPUT_CSS,
                    "rows": 3,
                    "placeholder": "Ajoutez un détail utile pour aider la modération.",
                }
            ),
        }
        labels = {
            "motif": "Motif du signalement",
            "commentaire": "Commentaire",
        }


class LogementForm(forms.ModelForm):
    MAX_VIDEO_SIZE = 20 * 1024 * 1024

    def clean(self):
        cleaned_data = super().clean()
        ville = cleaned_data.get("ville")
        ville_autre = (cleaned_data.get("ville_autre") or "").strip()

        if ville == Logement.VilleChoices.AUTRE and not ville_autre:
            self.add_error("ville_autre", "Pr\u00e9cisez le nom de la ville.")
        if ville != Logement.VilleChoices.AUTRE:
            cleaned_data["ville_autre"] = ""

        return cleaned_data

    def clean_video_preuve(self):
        video = self.cleaned_data.get("video_preuve")
        if not video:
            return video
        if getattr(video, "size", 0) > self.MAX_VIDEO_SIZE:
            raise forms.ValidationError("La vidéo dépasse 20 Mo. Réduisez sa taille avant l'envoi.")
        return video

    class Meta:
        model = Logement
        fields = [
            "ville",
            "ville_autre",
            "commune",
            "adresse",
            "point_repere",
            "categorie_bien",
            "type_transaction",
            "prix",
            "devise",
            "disponibilite",
            "description",
            "nb_chambres",
            "nb_salles_bain",
            "surface_m2",
            "telephone_proprio",
            "eau_regideso",
            "elec_snel",
            "sentinelle",
            "parking",
            "cloture",
            "type_piece_justificative",
            "video_preuve",
            "carte_id_proprio",
            "gps_lat",
            "gps_long",
        ]
        widgets = {
            "ville": forms.Select(attrs={"class": BASE_INPUT_CSS}),
            "ville_autre": forms.TextInput(attrs={"class": BASE_INPUT_CSS, "placeholder": "Saisissez la ville"}),
            "commune": forms.TextInput(
                attrs={
                    "class": BASE_INPUT_CSS,
                    "list": "communes-list",
                    "placeholder": "Choisissez ou saisissez la commune",
                    "autocomplete": "off",
                }
            ),
            "adresse": forms.TextInput(
                attrs={
                    "class": BASE_INPUT_CSS,
                    "placeholder": "Ex. : Avenue Kasa-Vubu 24, derriere la station Total",
                }
            ),
            "point_repere": forms.TextInput(
                attrs={
                    "class": BASE_INPUT_CSS,
                    "placeholder": "Ex. : A cote de la station Total, derriere l'arret de bus",
                }
            ),
            "categorie_bien": forms.Select(attrs={"class": BASE_INPUT_CSS}),
            "type_transaction": forms.Select(attrs={"class": BASE_INPUT_CSS}),
            "prix": forms.NumberInput(attrs={"class": BASE_INPUT_CSS, "step": "0.01"}),
            "devise": forms.Select(attrs={"class": BASE_INPUT_CSS}),
            "disponibilite": forms.Select(attrs={"class": BASE_INPUT_CSS}),
            "description": forms.Textarea(attrs={"class": BASE_INPUT_CSS, "rows": 5}),
            "nb_chambres": forms.NumberInput(attrs={"class": BASE_INPUT_CSS}),
            "nb_salles_bain": forms.NumberInput(attrs={"class": BASE_INPUT_CSS}),
            "surface_m2": forms.NumberInput(attrs={"class": BASE_INPUT_CSS, "step": "0.01"}),
            "telephone_proprio": forms.TextInput(attrs={"class": BASE_INPUT_CSS, "placeholder": "+243..."}),
            "type_piece_justificative": forms.Select(attrs={"class": BASE_INPUT_CSS}),
            "video_preuve": forms.ClearableFileInput(attrs={"class": BASE_INPUT_CSS}),
            "carte_id_proprio": forms.ClearableFileInput(attrs={"class": BASE_INPUT_CSS}),
            "gps_lat": forms.NumberInput(attrs={"class": "hidden", "step": "any"}),
            "gps_long": forms.NumberInput(attrs={"class": "hidden", "step": "any"}),
        }
        labels = {
            "ville_autre": "Autre ville",
            "adresse": "Adresse complète",
            "point_repere": "Point de repère",
            "categorie_bien": "Cat\u00e9gorie du bien",
            "type_transaction": "Type de transaction",
            "nb_salles_bain": "Nombre de salles de bain",
            "surface_m2": "Surface (m\u00b2)",
            "telephone_proprio": "T\u00e9l\u00e9phone du propri\u00e9taire",
            "elec_snel": "\u00c9lectricit\u00e9 SNEL",
            "cloture": "Cl\u00f4ture",
            "type_piece_justificative": "Type de piece justificative",
            "video_preuve": "Vid\u00e9o de preuve",
            "carte_id_proprio": "Piece justificative du proprietaire",
        }
        error_messages = {
            "video_preuve": {
                "invalid": "Aucune vidéo valide n'a été envoyée. Sélectionnez un fichier vidéo puis réessayez.",
                "missing": "Aucune vidéo n'a été envoyée.",
            },
            "carte_id_proprio": {
                "invalid": "Aucune image valide n'a été envoyée pour la pièce d'identité.",
                "missing": "Aucune image n'a été envoyée pour la pièce d'identité.",
            },
        }


class PhotoUploadForm(forms.Form):
    MIN_PHOTOS = 5
    MAX_PHOTOS = 10

    photos = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={"class": BASE_INPUT_CSS, "accept": "image/*"}),
        label="Photos du logement",
        error_messages={
            "invalid": "Aucune photo valide n'a été envoyée. Sélectionnez une ou plusieurs images puis réessayez.",
            "missing": "Aucune photo n'a été envoyée.",
            "empty": "Une des photos sélectionnées est vide.",
        },
    )

    def __init__(self, *args, **kwargs):
        self.existing_count = kwargs.pop("existing_count", 0)
        super().__init__(*args, **kwargs)

    def clean_photos(self):
        photos = self.files.getlist("photos")
        total_count = self.existing_count + len(photos)
        if total_count < self.MIN_PHOTOS:
            missing = self.MIN_PHOTOS - total_count
            raise forms.ValidationError(
                f"Ajoutez au moins {self.MIN_PHOTOS} photos pour publier ce bien. "
                f"Il vous manque encore {missing} photo(s)."
            )
        if len(photos) > self.MAX_PHOTOS:
            raise forms.ValidationError(f"Vous pouvez s\u00e9lectionner au maximum {self.MAX_PHOTOS} photos \u00e0 la fois.")
        if total_count > self.MAX_PHOTOS:
            remaining = max(self.MAX_PHOTOS - self.existing_count, 0)
            raise forms.ValidationError(
                f"Ce bien peut contenir au maximum {self.MAX_PHOTOS} photos. "
                f"Vous pouvez encore ajouter {remaining} photo(s)."
            )
        return photos
