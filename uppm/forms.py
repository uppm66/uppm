from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Profil, Message, MessageGeneral, Choix, InscriptionNewsletter
from captcha.fields import CaptchaField
from django_summernote.widgets import SummernoteWidget


class ProfilCreationForm(UserCreationForm):
    username = forms.CharField(label="Pseudonyme*", help_text="Attention les majuscules sont importantes...")
    #description = forms.CharField(label=None, help_text="Une description de vous même", required=False, widget=forms.Textarea)
    #site_web = forms.CharField(label="Site web", help_text="n'oubliez pas le https://", required=False)
    captcha = CaptchaField()
    email = forms.EmailField(label="Email*",)

    accepter_annuaire = forms.BooleanField(required=False, label="J'accepte d'apparaitre dans l'annuaire du site et la carte et rend mon profil visible par tous les inscrits")
    accepter_conditions = forms.BooleanField(required=True, label="J'ai lu et j'accepte les Conditions Générales d'Utilisation du site",  )


    def __init__(self, request, *args, **kargs):
        super(ProfilCreationForm, self).__init__(request, *args, **kargs)

    class Meta(UserCreationForm):
        model = Profil
        fields = ['username', 'password1',  'password2', 'email', 'telephone', 'inscrit_newsletter', 'accepter_annuaire',  'accepter_conditions']
        exclude = ['slug', ]


    def save(self, commit = True, is_active=False):
        return super(ProfilCreationForm, self).save(commit)
        self.is_active=is_active



class ProducteurChangeForm(UserChangeForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    email = forms.EmailField(label="Email")
    username = forms.CharField(label="Pseudonyme")
    #description = forms.CharField(required=False, label="Description", help_text="Une description de vous même",widget=SummernoteWidget)
    inscrit_newsletter = forms.BooleanField(required=False)
    accepter_annuaire = forms.BooleanField(required=False, label="J'accepte d'apparaitre dans l'annuaire du site et la carte et rend mon profil visible par tous")
    password=None

    def __init__(self, *args, **kargs):
        super(ProducteurChangeForm, self).__init__(*args, **kargs)

    class Meta:
        model = Profil
        fields = ['username', 'first_name', 'last_name', 'email',  'telephone', 'accepter_annuaire', 'inscrit_newsletter']


class ProducteurChangeForm_admin(UserChangeForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    email = forms.EmailField(label="Email")
    username = forms.CharField(label="Pseudonyme")
    #description = forms.CharField(label="Description", initial="Une description de vous même", widget=forms.Textarea, required=False)
    inscrit_newsletter = forms.BooleanField(required=False)
    accepter_annuaire = forms.BooleanField(required=False)

    password = None

    class Meta:
        model = Profil
        fields = ['username', 'email',  'telephone', 'inscrit_newsletter', 'accepter_annuaire', 'statut_adhesion']

    def __init__(self, *args, **kwargs):
        super(ProducteurChangeForm_admin, self).__init__(*args, **kwargs)

class ContactForm(forms.Form):
    sujet = forms.CharField(max_length=100, label="Sujet",)
    msg = forms.CharField(label="Message", widget=SummernoteWidget)
    renvoi = forms.BooleanField(label="recevoir une copie",
                                     help_text="Cochez si vous souhaitez obtenir une copie du mail envoyé.", required=False
                                 )



class MessageForm(forms.ModelForm):

    class Meta:
        model = Message
        exclude = ['conversation','auteur']

        widgets = {
                'message': SummernoteWidget(),
            }

    def __init__(self, request, message=None, *args, **kwargs):
        super(MessageForm, self).__init__(request, *args, **kwargs)
        if message:
           self.fields['message'].initial = message




class ChercherConversationForm(forms.Form):
    destinataire = forms.ChoiceField(label='destinataire')

    def __init__(self, user, *args, **kwargs):
        super(ChercherConversationForm, self).__init__(*args, **kwargs)
        self.fields['destinataire'].choices = [(i,u) for i, u in enumerate(Profil.objects.all().order_by('username')) if u != user]

class MessageGeneralForm(forms.ModelForm):
    class Meta:
        model = MessageGeneral
        exclude = ['auteur']

        widgets = {
            'message': SummernoteWidget(),
        }

    #def __init__(self, request, message=None, *args, **kwargs):
    #    super(MessageGeneralForm, self).__init__(request, *args, **kwargs)



class MessageChangeForm(forms.ModelForm):

    class Meta:
        model = MessageGeneral
        exclude = ['auteur']
        widgets = {
            'message': SummernoteWidget(),
        }


class InscriptionNewsletterForm(forms.ModelForm):

    class Meta:
        model = InscriptionNewsletter
        fields = ['email']