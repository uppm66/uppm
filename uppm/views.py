# -*- coding: utf-8 -*-
'''
Created on 25 mai 2017

@author: tchenrezi
'''
from django.shortcuts import HttpResponseRedirect, render, redirect#, render, get_object_or_404, redirect, render_to_response,

from .forms import ContactForm, ProfilCreationForm, MessageForm, MessageGeneralForm, \
    ProducteurChangeForm, ChercherConversationForm, InscriptionNewsletterForm, \
    MessageChangeForm
from .models import Profil, Conversation, Message, MessageGeneral, getOrCreateConversation, Suivis, InscriptionNewsletter
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.core.mail import mail_admins, send_mail, BadHeaderError, send_mass_mail

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import Group, User
from django.views.decorators.csrf import csrf_exempt

from django.views.decorators.debug import sensitive_variables
#from django.views.decorators.debug import sensitive_post_parameters

#from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, CharField
from django.db.models.functions import Lower
from django.utils.html import strip_tags

from actstream import actions, action
from actstream.models import Action, any_stream, following,followers


from django.utils.timezone import now

CharField.register_lookup(Lower, "lower")

#import sys
#from io import BytesIO
#from django.core.files.uploadedfile import InMemoryUploadedFile
#from PIL import Image
#from braces.views import LoginRequiredMixin

def handler404(request, *args, **kwargs):  #page not found
    response = render(request, "404.html")
    response.status_code = 404
    return response

def handler500(request, *args, **kwargs):   #erreur du serveur
    response = render(request, "500.html")
    response.status_code = 500
    return response

def handler403(request, *args, **kwargs):   #non autorisé
    response = render(request, "403.html")
    response.status_code = 403
    return response

def handler400(request, *args, **kwargs):   #requete invalide
    response = render(request, "400.html")
    response.status_code = 400
    return response

def bienvenue(request):
    nbNotif = 0
    if request.user.is_authenticated:
        nbNotif = getNbNewNotifications(request)

    return render(request, 'bienvenue.html', { "nbNotif": nbNotif })


def presentation_site(request):
    return render(request, 'presentation_site.html')

def gallerie(request):
    return render(request, 'gallerie.html')

def faq(request):
    return render(request, 'faq.html')


def merci(request, template_name='merci.html'):
    return render(request, template_name)


@login_required
def profil_courant(request, ):
    return render(request, 'profil.html', {'user': request.user})


@login_required
def profil(request, user_id):
    try:
        user = Profil.objects.get(id=user_id)
        return render(request, 'profil.html', {'user': user,})
    except User.DoesNotExist:
            return render(request, 'profil_inconnu.html', {'userid': user_id})

@login_required
def profil_nom(request, user_username):
    try:
        user = Profil.objects.get(username=user_username)
        return render(request, 'profil.html', {'user': user, })
    except User.DoesNotExist:
        return render(request, 'profil_inconnu.html', {'userid': user_username})

@login_required
def profil_inconnu(request):
    return render(request, 'profil_inconnu.html')

@login_required
def annuaire(request):
    profils = Profil.objects.filter(accepter_annuaire=True).order_by('username')
    nb_profils = len(Profil.objects.all())
    return render(request, 'annuaire.html', {'profils':profils, "nb_profils":nb_profils} )


@login_required
def listeContacts(request):
    if not request.user.is_membre_collectif:
        return render(request, "notUPPM.html")
    listeMails = [
        {"type":'user_newsletter' ,"profils":Profil.objects.filter(inscrit_newsletter=True), "titre":"Liste des inscrits à la newsletter : "},
         {"type":'anonym_newsletter' ,"profils":InscriptionNewsletter.objects.all(), "titre":"Liste des inscrits anonymes à la newsletter : "},
      {"type":'user_adherent' , "profils":Profil.objects.filter(statut_adhesion=2), "titre":"Liste des adhérents : "},
        {"type":'user_futur_adherent', "profils":Profil.objects.filter(statut_adhesion=0), "titre":"Liste des personnes qui veulent adhérer à UPPM :"}
    ]
    return render(request, 'listeContacts.html', {"listeMails":listeMails})


@login_required
def listeFollowers(request):
    if not request.user.is_membre_collectif:
        return render(request, "notUPPM.html")
    listeArticles = []
    # for art in Projet.objects.all():
    #     suiveurs = followers(art)
    #     if suiveurs:
    #         listeArticles.append({"titre": art.titre, "url": art.get_absolute_url(), "followers": suiveurs, })

    return render(request, 'listeFollowers.html', {"listeArticles":listeArticles})

@login_required
def carte(request):
    profils = Profil.objects.filter(accepter_annuaire=1)
    return render(request, 'carte_cooperateurs.html', {'profils':profils, 'titre': "La carte des coopérateurs*" } )


@login_required
def profil_contact(request, user_id):
    recepteur = Profil.objects.get(id=user_id)
    if request.method == 'POST':
        form = ContactForm(request.POST or None, )
        if form.is_valid():
            sujet = "[permacat] "+ request.user.username + "(" + request.user.email+ ") vous a écrit: "+ form.cleaned_data['sujet']
            message_txt = form.cleaned_data['msg']
            message_html = form.cleaned_data['msg']
            recepteurs = [recepteur.email,]
            if form.cleaned_data['renvoi'] :
                recepteurs = [recepteur.email, request.user.email]

            send_mail(
                sujet,
                message_txt,
                request.user.email,
                recepteurs,
                html_message=message_html,
                fail_silently=False,
                )
            return render(request, 'contact/message_envoye.html', {'sujet': form.cleaned_data['sujet'], 'msg':message_html, 'envoyeur':request.user.username + " (" + request.user.email + ")", "destinataire":recepteur.username + " (" +recepteur.email+ ")"})
    else:
        form = ContactForm()
    return render(request, 'contact/profil_contact.html', {'form': form, 'recepteur':recepteur})


def contact_admins(request):
    if request.method == 'POST':
        form = ContactForm(request.POST or None, )
        if form.is_valid():
            if request.user.is_anonymous :
                envoyeur = "Anonyme "
            else:
                envoyeur = request.user.username + "(" + request.user.email+ ") "

            sujet =  envoyeur + form.cleaned_data['sujet']
            message_txt = envoyeur + ") a envoyé le message suivant : "
            message_html = form.cleaned_data['msg']
            try:
                mail_admins(sujet, message_txt, html_message=message_html)
                if form.cleaned_data['renvoi']:
                    send_mail(sujet, "Vous avez envoyé aux administrateurs du site uppm66.herokuapp.com le message suivant : " + message_html, request.user.email, [request.user.email,], fail_silently=False, html_message=message_html)

                return render(request, 'contact/message_envoye.html', {'sujet': sujet, 'msg': message_html,
                                                       'envoyeur': envoyeur,
                                                       "destinataire": "administrateurs "})
            except BadHeaderError:
                return render(request, 'erreur.html', {'msg':'Invalid header found.'})

            return render(request, 'erreur.html', {'msg':"Désolé, une ereur s'est produite"})
    else:
        form = ContactForm()
    return render(request, 'contact/contact.html', {'form': form, "isContactProducteur":False})

@login_required
class profil_modifier_user(UpdateView):
    model = Profil
    form_class = ProducteurChangeForm
    template_name_suffix = '_modifier'
    fields = ['username', 'first_name', 'last_name', 'email', 'accepter_annuaire', 'inscrit_newsletter']

    def get_object(self):
        return Profil.objects.get(id=self.request.user.id)


class profil_modifier(UpdateView):
    model = Profil
    form_class = ProducteurChangeForm
    template_name_suffix = '_modifier'
    #fields = ['username','email','first_name','last_name', 'site_web','description', 'competences', 'inscrit_newsletter']

    def get_object(self):
        return Profil.objects.get(id=self.request.user.id)

class profil_supprimer(DeleteView):
    model = Profil
    success_url = reverse_lazy('bienvenue')

    def get_object(self):
        return Profil.objects.get(id=self.request.user.id)

@sensitive_variables('password')
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('change_password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'registration/password_changer_form.html', {
        'form': form
    })

@sensitive_variables('user', 'password1', 'password2')
def register(request):
    if request.user.is_authenticated:
        return render(request, "erreur.html", {"msg":"Vous etes déjà inscrit et authentifié !"})

    form_profil = ProfilCreationForm(request.POST or None)
    if form_profil.is_valid():
        profil_courant = form_profil.save(commit=False,is_active = False)
        if profil_courant.statut_adhesion == 2:
            profil_courant.is_active=False
        profil_courant.save()
        return render(request, 'userenattente.html')

    return render(request, 'register.html', {"form_profil": form_profil,})

def cgu(request):
    return render(request, 'cgu.html', )

@login_required
def liens(request):
    liens = [
        'https://colibris-universite.org/mooc-permaculture/wakka.php?wiki=PagePrincipale',
        'https://ecocharte.herokuapp.com',
        'http://terre-avenirs-peyrestortes.org/',
        'https://val-respire.wixsite.com/asso',
        'https://www.colibris-lemouvement.org/',
        'http://sel66.free.fr',
        'https://www.monnaielibreoccitanie.org/',
        'http://lejeu.org/',
        'http://soudaqui.cat/wordpress/',
        'https://ponteillanature.wixsite.com/eco-nature',
        'https://cce-66.wixsite.com/mysite',
        'https://jardindenat.wixsite.com/website',
        'http://lagalline.net',
        'https://www.permapat.com',
        'https://permaculturelne.herokuapp.com',
        'https://framasoft.org',
        'https://alternatiba.eu/alternatiba66/',
        'http://www.le-message.org/?lang=fr',
        'https://reporterre.net/',
        'https://la-bas.org/',
    ]
    return render(request, 'liens.html', {'liens':liens})

def fairedon(request):
    return render(request, 'fairedon.html', )

@login_required
def chercher(request):
    recherche = str(request.GET.get('id_recherche')).lower()
    # if recherche:
    #     produits_list = Produit.objects.filter(Q(description__icontains=recherche) | Q(nom_produit__lower__contains=recherche), ).select_subclasses()
    #     articles_list = Article.objects.filter(Q(titre__lower__contains=recherche) | Q(contenu__icontains=recherche), )
    #     projets_list = Projet.objects.filter(Q(titre__lower__contains=recherche) | Q(contenu__icontains=recherche), )
    #     profils_list = Profil.objects.filter(Q(username__lower__contains=recherche)  | Q(description__icontains=recherche)| Q(competences__icontains=recherche), )
    # else:
    produits_list = []
    articles_list = []
    projets_list = []
    profils_list = []
    return render(request, 'chercher.html', {'recherche':recherche, 'articles_list':articles_list, 'produits_list':produits_list, "projets_list": projets_list, 'profils_list':profils_list})


@login_required
def lireConversation(request, destinataire):
    conversation = getOrCreateConversation(request.user.username, destinataire)
    messages = Message.objects.filter(conversation=conversation).order_by("date_creation")


    form = MessageForm(request.POST or None)
    if form.is_valid():
        message = form.save(commit=False)
        message.conversation = conversation
        message.auteur = request.user
        conversation.date_dernierMessage = message.date_creation
        conversation.dernierMessage =  ("(" + str(message.auteur) + ") " + str(strip_tags(message.message).replace('&nspb',' ')))[:96] + "..."
        conversation.save()
        message.save()
        url = conversation.get_absolute_url()
        action.send(request.user, verb='envoi_salon_prive', action_object=conversation, url=url, group=destinataire,
                    description="a envoyé un message privé à " + destinataire)
        profil_destinataire = Profil.objects.get(username=destinataire)
        if profil_destinataire in followers(conversation):
            sujet = "UPPM - quelqu'un vous a envoyé une message privé"
            message = request.user.username + " vous a envoyé un message privé. Vous pouvez y accéder en suivant ce lien : http://uppm66.herokuapp.com" +  url
            send_mail(sujet, message, "siteuppm66@gmail.com", [profil_destinataire.email, ], fail_silently=False,)
        return redirect(request.path)

    return render(request, 'lireConversation.html', {'conversation': conversation, 'form': form, 'messages_echanges': messages, 'destinataire':destinataire})



@login_required
def lireConversation_2noms(request, destinataire1, destinataire2):
    if request.user.username==destinataire1:
        return lireConversation(request, destinataire2)
    elif request.user.username==destinataire2:
        return lireConversation(request, destinataire1)
    else:
        return render(request, 'erreur.html', {'msg':"Vous n'êtes pas autorisé à voir cette conversation"})


class ListeConversations(ListView):
    model = Conversation
    context_object_name = "conversation_list"
    template_name = "conversations.html"
    paginate_by = 1

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        context['conversations'] = Conversation.objects.filter(Q(profil2__id=self.request.user.id) | Q(profil1__id=self.request.user.id)).order_by('-date_dernierMessage')

        return context

def chercherConversation(request):
    form = ChercherConversationForm(request.user, request.POST or None,)
    if form.is_valid():
        destinataire = (Profil.objects.all().order_by('username'))[int(form.cleaned_data['destinataire'])]
        return redirect('agora_conversation', destinataire=destinataire)
    else:
        return render(request, 'chercher_conversation.html', {'form': form})

@login_required
def getNotifications(request):
    if request.user.is_membre_collectif:
        salons      = Action.objects.filter(Q(verb='envoi_salon') | Q(verb='envoi_salon_permacat'))[:30]
        articles    = Action.objects.filter(Q(verb='article_nouveau_permacat') | Q(verb='article_message_permacat')|
                                            Q(verb='article_nouveau') | Q(verb='article_message')| Q(verb='article_modifier')|
                                            Q(verb='article_modifier_permacat'))[:30]
    else:
        salons      = Action.objects.filter(Q(verb='envoi_salon') | Q(verb='envoi_salon_permacat'))[:30]
        articles    = Action.objects.filter(Q(verb='article_nouveau') | Q(verb='article_message')| Q(verb='article_modifier'))[:30]


    nbNotif = 6
    conversations = (any_stream(request.user).filter(Q(verb='envoi_salon_prive',)) | Action.objects.filter(Q(verb='envoi_salon_prive',  description="a envoyé un message privé à " + request.user.username) ))[:nbNotif]
    articles = [art for i, art in enumerate(articles) if i == 0 or not (art.description == articles[i-1].description  and art.actor == articles[i-1].actor)][:nbNotif]
    salons = [art for i, art in enumerate(salons) if i == 0 or not (art.description == salons[i-1].description and art.actor == salons[i-1].actor ) ][:nbNotif]
    inscription = Action.objects.filter(Q(verb='inscription') )

    return salons, articles, conversations, inscription

@login_required
def getNotificationsParDate(request):
    if request.user.is_membre_collectif:
        actions      = Action.objects.filter( \
            Q(verb='envoi_salon') | Q(verb='envoi_salon_permacat')|Q(verb='article_nouveau_permacat') |
            Q(verb='article_message_permacat')|Q(verb='article_nouveau') | Q(verb='article_message')|
            Q(verb='article_modifier')| Q(verb='article_modifier_permacat')|Q(verb='projet_nouveau_permacat')|
            Q(verb='envoi_salon_prive', description="a envoyé un message privé à " + request.user.username)   |Q(verb='inscription')
        ).order_by('-timestamp')
    else:
        actions      = Action.objects.filter(Q(verb='envoi_salon') | Q(verb='envoi_salon_permacat')|
                                             Q(verb='article_nouveau') | Q(verb='article_message')|
                                             Q(verb='article_modifier') |Q(verb='inscription') |
                                                Q(verb='envoi_salon_prive', description="a envoyé un message privé à " + request.user.username)
        ).order_by('-timestamp')

    actions = [art for i, art in enumerate(actions[:100]) if i == 0 or not (art.description == actions[i-1].description and art.actor == actions[i-1].actor ) ][:50]

    return actions

@login_required
def getNbNewNotifications(request):
    actions = getNotificationsParDate(request)
    actions = [action for action in actions if  request.user.date_notifications < action.timestamp]

    return len(actions)


@login_required
def get_notifications_news(request):
    actions = getNotificationsParDate(request)
    actions = [action for action in actions if  request.user.date_notifications < action.timestamp]
    return actions


@login_required
def notifications(request):
    salons, articles, conversations, inscriptions = getNotifications(request)
    return render(request, 'notifications/notifications.html', {'salons': salons, 'articles': articles, 'inscriptions':inscriptions, 'conversations':conversations})

@login_required
def notifications_news(request):
    actions = get_notifications_news(request)
    return render(request, 'notifications/notifications_last.html', {'actions':actions})


@login_required
def notificationsParDate(request):
    actions = getNotificationsParDate(request)
    return render(request, 'notifications/notificationsParDate.html', {'actions': actions, })

@login_required
def notificationsLues(request):
    request.user.date_notifications = now()
    request.user.save()
    return redirect('notifications_news')

def getInfosJourPrecedent(request, nombreDeJours):
    from datetime import datetime, timedelta
    timestamp_from = datetime.now().date() - timedelta(days=nombreDeJours)
    timestamp_to = datetime.now().date() - timedelta(days=nombreDeJours - 1)

    if request.user.is_membre_collectif:
        articles    = Action.objects.filter(Q(verb='article_nouveau_permacat', timestamp__gte = timestamp_from,timestamp__lte = timestamp_to,) | Q(verb='article_nouveau',timestamp__gte = timestamp_from, timestamp__lte = timestamp_to,))
        projets     = Action.objects.filter(Q(verb='projet_nouveau_permacat', timestamp__gte = timestamp_from,timestamp__lte = timestamp_to,) |Q(verb='projet_nouveau', timestamp__gte = timestamp_from,timestamp__lte = timestamp_to,))
        offres      = Action.objects.filter(Q(verb='ajout_offre', timestamp__gte = timestamp_from,timestamp__lte = timestamp_to,) | Q(verb='ajout_offre_permacat', timestamp__gte = timestamp_from,timestamp__lte = timestamp_to,))
    else:
        articles    = Action.objects.filter(Q(verb='article_nouveau', timestamp__gte = timestamp_from, timestamp__lte = timestamp_to,) | Q(verb='article_modifier', timestamp__gte = timestamp_from,timestamp__lte = timestamp_to,))
        projets     = Action.objects.filter(Q(verb='projet_nouveau', timestamp__gte = timestamp_from,timestamp__lte = timestamp_to,))
        offres      = Action.objects.filter(Q(verb='ajout_offre', timestamp__gte = timestamp_from,timestamp__lte = timestamp_to,))
    fiches = Action.objects.filter(verb__startswith='fiche')
    ateliers = Action.objects.filter(Q(verb__startswith='atelier')|Q(verb=''))
    conversations = (any_stream(request.user).filter(Q(verb='envoi_salon_prive', )) | Action.objects.filter(
        Q(verb='envoi_salon_prive', description="a envoyé un message privé à " + request.user.username)))[:nbNotif]

    articles = [art for i, art in enumerate(articles) if i == 0 or not (art.description == articles[i-1].description  and art.actor == articles[i-1].actor)]
    projets = [art for i, art in enumerate(projets) if i == 0 or not (art.description == projets[i-1].description and art.actor == projets[i-1].actor) ]
    offres = [art for i, art in enumerate(offres) if i == 0 or not (art.description == offres[i-1].description and art.actor == offres[i-1].actor) ]
    fiches = [art for i, art in enumerate(fiches) if i == 0 or not (art.description == fiches[i-1].description and art.actor == fiches[i-1].actor ) ]
    ateliers = [art for i, art in enumerate(ateliers) if i == 0 or not (art.description == ateliers[i-1].description and art.actor == ateliers[i-1].actor ) ]
    conversations = [art for i, art in enumerate(conversations) if i == 0 or not (art.description == conversations[i-1].description and art.actor == conversations[i-1].actor ) ]

    return articles, projets, offres, fiches, ateliers, conversations

def getTexteJourPrecedent(nombreDeJour):
    if nombreDeJour == 0:
        return "Aujourd'hui"
    elif nombreDeJour == 1:
        return "Hier"
    elif nombreDeJour == 2:
        return "Avant-hier"
    else:
        return "Il y a " + str(nombreDeJour) + " jours"

@login_required
def dernieresInfos(request):
    info_parjour = []
    for i in range(15):
        info_parjour.append({"jour":getTexteJourPrecedent(i), "infos":getInfosJourPrecedent(request, i)})
    return render(request, 'notifications/notifications_news.html', {'info_parjour': info_parjour,})


@login_required
def agora(request, ):
    messages = MessageGeneral.objects.all().order_by("date_creation")
    form = MessageGeneralForm(request.POST or None) 
    if form.is_valid(): 
        message = form.save(commit=False) 
        message.auteur = request.user 
        message.save()
        group, created = Group.objects.get_or_create(name='tous')
        url = reverse('agora_general')
        action.send(request.user, verb='envoi_salon', action_object=message, target=group, url=url, description="a envoyé un message dans le salon public")
        return redirect(request.path) 
    return render(request, 'agora.html', {'form': form, 'messages_echanges': messages})

@login_required
@csrf_exempt
def suivre_conversations(request, actor_only=True):
    """
    """
    conversations = Conversation.objects.filter(Q(profil2__id=request.user.id) | Q(profil1__id=request.user.id))
    for conv in conversations:
        if conv in following(request.user):
            actions.unfollow(request.user, conv)
        else:
            actions.follow(request.user, conv, actor_only=actor_only)
    return redirect('conversations')


def inscription_newsletter(request):
    form = InscriptionNewsletterForm(request.POST or None)
    if form.is_valid():
        inscription = form.save(commit=False)
        inscription.save()
        return render(request, 'merci.html', {'msg' :"Vous êtes inscrits à la newsletter"})
    return render(request, 'registration/inscription_newsletter.html', {'form':form})



@login_required
def modifier_message(request, id, type):
    if type == 'general':
        obj = MessageGeneral.objects.get(id=id)
    elif type == 'conversation':
        obj = Message.objects.get(id=id)
    else:
        return render(request, 'erreur.html', {'msg':"Le salon que vous cherchez n'existe pas, désolé."})


    form = MessageChangeForm(request.POST or None, instance=obj)

    if form.is_valid():
        object = form.save()
        if object.message and object.message !='<br>':
            object.date_modification = now()
            object.save()
            return redirect (object.get_absolute_url)
        else:
            object.delete()
            return reverse('agora_general')


    return render(request, 'modifierCommentaire.html', {'form': form, })