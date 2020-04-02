# -*- coding: utf-8 -*-
from django.db import models
#from django.utils import timezone
from django.core.validators import MinValueValidator
from django.utils.timezone import now
from model_utils.managers import InheritanceManager
import django_filters
from django.urls import reverse, reverse_lazy
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
import decimal, math
from django.db.models import Q
#from tinymce.models import HTMLField

from actstream import actions, action
from actstream.models import following, followers

import os
import requests
from stdimage import StdImageField
from datetime import date

from django.dispatch import receiver
from django.db.models.signals import post_save

from django.core.mail import send_mass_mail

DEGTORAD=3.141592654/180

class Choix():
    statut_adhesion = (('', '-----------'),
                   (0, _("Je souhaite devenir membre du collectif ACVI et utiliser le site")),
                   (1, _("Je suis membre d'un autre collectif du uppm pour la transition")),
                   (2, _("Je suis membre du collectif ACVI")))


LATITUDE_DEFAUT = '42.6976'
LONGITUDE_DEFAUT = '2.8954'

class Profil(AbstractUser):
    phone_regex = RegexValidator(regex=r'^\d{9,10}$', message="Le numero de telephone doit contenir 10 chiffres")
    telephone = models.CharField(validators=[phone_regex,], max_length=10, blank=True)  # validators should be a list

    date_registration = models.DateTimeField(verbose_name="Date de création", editable=False)

    inscrit_newsletter = models.BooleanField(verbose_name="J'accepte de recevoir des emails de UPPM", default=False)
    accepter_conditions = models.BooleanField(verbose_name="J'ai lu et j'accepte les conditions d'utilisation du site", default=False, null=False)
    accepter_annuaire = models.BooleanField(verbose_name="J'accepte d'apparaitre dans l'annuaire du site et la carte et rend mon profil visible par tous", default=True)

    date_notifications = models.DateTimeField(verbose_name="Date de validation des notifications",default=now)

    statut_adhesion = models.IntegerField(choices=Choix.statut_adhesion, default="0")

    def __str__(self):
        return self.username

    def __unicode__(self):
        return self.username

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.date_registration = now()

        return super(Profil, self).save(*args, **kwargs)

    def get_nom_class(self):
        return "Profil"

    def get_absolute_url(self):
        return reverse('profil', kwargs={'user_id':self.id})

    def getDistance(self, profil):
        x1 = float(self.adresse.latitude)*DEGTORAD
        y1 = float(self.adresse.longitude)*DEGTORAD
        x2 = float(profil.adresse.latitude)*DEGTORAD
        y2 = float(profil.adresse.longitude)*DEGTORAD
        x = (y2-y1) * math.cos((x1+x2)/2)
        y = (x2-x1)
        return math.sqrt(x*x + y*y) * 6371

    @property
    def statutMembre(self):
        return self.statut_adhesion

    @property
    def statutMembre_str(self):
        if self.statut_adhesion == 0:
            return "souhaite devenir membre du collectif"
        elif self.statut_adhesion == 1:
            return "membre d'un autre collectif"
        elif self.statut_adhesion == 2:
            return "membre du collectif ACVI"


    @property
    def is_membre_collectif(self):
        if self.statut_adhesion == 2:
            return True
        else:
            return False


    @property
    def inscrit_newsletter_str(self):
       return "oui" if self.inscrit_newsletter else "non"

@receiver(post_save, sender=Profil)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        for suiv in ['articles', '']:
            suivi, created = Suivis.objects.get_or_create(nom_suivi=suiv)
            actions.follow(instance, suivi, actor_only=True)

            action.send(instance, verb='inscription', url=instance.get_absolute_url(),
                        description="s'est inscrit sur le site")



def get_slug_from_names(name1, name2):
    return str(slugify(''.join(sorted((name1, name2), key=str.lower))))

class Conversation(models.Model):
    profil1 = models.ForeignKey(Profil, on_delete=models.CASCADE, related_name='profil1')
    profil2 = models.ForeignKey(Profil, on_delete=models.CASCADE, related_name='profil2')
    slug = models.CharField(max_length=100)
    date_creation = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name="Date de parution")
    date_dernierMessage = models.DateTimeField(verbose_name="Date de Modification", auto_now=True)
    dernierMessage = models.CharField(max_length=100, default=None, blank=True, null=True)

    class Meta:
        ordering = ('-date_dernierMessage',)

    def __str__(self):
        return "Conversation entre " + self.profil1.username + " et " + self.profil2.username

    def titre(self):
        return self.__str__()

    titre = property(titre)

    @property
    def auteur_1(self):
        return self.profil1.username

    @property
    def auteur_2(self):
        return self.profil2.username

    @property
    def messages(self):
        return self.__str__()


    def get_absolute_url(self):
        return reverse('lireConversation_2noms', kwargs={'destinataire1': self.profil1.username, 'destinataire2': self.profil2.username})

    def save(self, *args, **kwargs):
        self.slug = get_slug_from_names(self.profil1.username, self.profil2.username)
        super(Conversation, self).save(*args, **kwargs)




def getOrCreateConversation(nom1, nom2):
    try:
        convers = Conversation.objects.get(slug=get_slug_from_names(nom1, nom2))
    except Conversation.DoesNotExist:
        profil_1 = Profil.objects.get(username=nom1)
        profil_2 = Profil.objects.get(username=nom2)
        convers = Conversation.objects.create(profil1=profil_1, profil2=profil_2)

        conversations = Conversation.objects.filter(Q(profil2=profil_1) | Q(profil1=profil_1))
        for conv in conversations:
            if conv in following(profil_1):
                actions.follow(profil_1, convers)
                break

        conversations = Conversation.objects.filter(Q(profil2=profil_2) | Q(profil1=profil_2))
        for conv in conversations:
            if conv in following(profil_2):
                actions.follow(profil_2, convers)
                break

    return convers


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    message = models.TextField(null=False, blank=False)
    auteur = models.ForeignKey(Profil, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.__str()

    def __str__(self):
        return "(" + str(self.id) + ") " + str(self.auteur) + " " + str(self.date_creation)

    @property
    def get_edit_url(self):
        return reverse('modifierMessage',  kwargs={'id':self.id, 'type':'conversation'})

    @property
    def get_absolute_url(self):
        return self.conversation.get_absolute_url()



class MessageGeneral(models.Model):
    message = models.TextField(null=False, blank=False)
    auteur = models.ForeignKey(Profil, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.__str__()

    def __str__(self):
        return "(" + str(self.id) + ") " + str(self.auteur) + " " + str(self.date_creation)

    @property
    def get_edit_url(self):
        return reverse('modifierMessage',  kwargs={'id':self.id, 'type':'general'})

    @property
    def get_absolute_url(self):
        return  reverse('agora_general')

class Suivis(models.Model):
    nom_suivi = models.TextField(null=False, blank=False)

    def __unicode__(self):
        return self.__str__()

    def __str__(self):
        return str(self.nom_suivi)


class InscriptionNewsletter(models.Model):
    email = models.EmailField()
    date_inscription = models.DateTimeField(verbose_name="Date d'inscription", editable=False, auto_now_add=True)

    def __unicode__(self):
        return self.__str()

    def __str__(self):
        return str(self.email)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.date_inscription = now()
        return super(InscriptionNewsletter, self).save(*args, **kwargs)