from django.db import models
from uppm.models import Profil, Suivis
from django.urls import reverse
from django.utils import timezone
from django.core.mail import send_mass_mail
#from tinymce.models import HTMLField
from django.dispatch import receiver
from django.db.models.signals import post_save

from actstream.models import followers

class Choix():
    type_annonce = ('0','Atelier philo'), ('1','Boite à idée'), \
                   ('2', 'Intendance, logistique'), ('3', 'Projets futurs'), \
                   ('4',"Conférence mensuelle"),
    couleurs_annonces = {
       # 'Annonce':"#e0f7de", 'Administratif':"#dcc0de", 'Agenda':"#d4d1de", 'Entraide':"#cebacf",
       # 'Chantier':"#d1ecdc",'Jardinage':"#fcf6bd", 'Recette':"#d0f4de", 'Bricolage':"#fff2a0",
       # 'Culture':"#ffc4c8", 'Bon_plan':"#bccacf", 'Point':"#87bfae", 'Autre':"#bcb4b4"

        '0':"#d1ecdc",
        '1':"#D4CF7D",
        '2':"#E0E3AB",
        '3':"#AFE4C1",
        '4':"#fff2a0",
        '5':"#B2AFE4",
        '6':"#d0f4de",
        '7':"#b3b6e6",
        '8':"#3EA7BB",
        '9':"#349D9B",
        '10':"#bccacf",
    }

    def get_couleur(categorie):
        try:
            return Choix.couleurs_annonces[categorie]
        except:
            return Choix.couleurs_annonces["6"]

class Article(models.Model):
    categorie = models.CharField(max_length=30,         
        choices=(Choix.type_annonce),
        default='Annonce', verbose_name="categorie")
    titre = models.CharField(max_length=100,)
    auteur = models.ForeignKey(Profil, on_delete=models.CASCADE, default=None)
    slug = models.SlugField(max_length=100)
    contenu = models.TextField(null=True)
    date_creation = models.DateTimeField(verbose_name="Date de parution", default=timezone.now)
    date_modification = models.DateTimeField(verbose_name="Date de modification", default=timezone.now)
    estPublic = models.BooleanField(default=False, verbose_name='Public ou réservé aux membres du collectif ACVI')
    estModifiable = models.BooleanField(default=False, verbose_name="Modifiable par n'importe qui")

    date_dernierMessage = models.DateTimeField(verbose_name="Date du dernier message", auto_now=True)
    dernierMessage = models.CharField(max_length=100, default=None, blank=True, null=True)
    estArchive = models.BooleanField(default=False, verbose_name="Archiver l'article")

    start_time = models.DateTimeField(verbose_name="Date (optionnel, pour affichage dans l'agenda)", null=True,blank=True, help_text="jj/mm/année")
    end_time = models.DateTimeField(verbose_name="Date de fin (optionnel, pour affichage dans l'agenda)",  null=True,blank=True, help_text="jj/mm/année")

    class Meta:
        ordering = ('-date_creation', )
        
    def __str__(self):
        return self.titre

    def get_absolute_url(self):
        return reverse('blog:lireArticle', kwargs={'slug':self.slug})

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.date_creation = timezone.now()
        return super(Article, self).save(*args, **kwargs)

    @property
    def get_couleur(self):
        if self.categorie in Choix.couleurs_annonces:
            return Choix.couleurs_annonces[self.categorie]
        return Choix.couleurs_annonces["6"]


@receiver(post_save, sender=Article)
def on_save_articles(instance, created, **kwargs):
    if created:
        suivi, created = Suivis.objects.get_or_create(nom_suivi='articles')
        titre = "UPPM - nouvel article"
        message = " Un nouvel article a été créé " + \
                  "\n Vous pouvez y accéder en suivant ce lien : https://uppm66.herokuapp.com" + instance.get_absolute_url() + \
                  "\n\n------------------------------------------------------------------------------" \
                  "\n vous recevez cet email, car vous avez choisi de suivre les articles (en cliquant sur la cloche) sur le site https://uppm66.herokuapp.com/forum/articles/"
        emails = [suiv.email for suiv in followers(suivi) if instance.auteur != suiv and (instance.estPublic or suiv.is_membre_collectif)]
        try:
            send_mass_mail([(titre, message, "siteuppm66@gmail.com", emails), ])
        except:
            pass


class Commentaire(models.Model):
    auteur_comm = models.ForeignKey(Profil, on_delete=models.CASCADE)
    commentaire = models.TextField()
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.__str__()

    def __str__(self):
        return "(" + str(self.id) + ") "+ str(self.auteur_comm) + ": " + str(self.article)

    @property
    def get_edit_url(self):
        return reverse('blog:modifierCommentaireArticle',  kwargs={'id':self.id})


@receiver(post_save,  sender=Article)
def on_save_article(instance, **kwargs):
    titre = "UPPM - Article actualisé"
    message = "L'article '" +  instance.titre + "' a été modifié (ou quelqu'un l'a commenté)" +\
              "\n Vous pouvez y accéder en suivant ce lien : http://uppm66.herokuapp.com" + instance.get_absolute_url() + \
              "\n\n------------------------------------------------------------------------------" \
              "\n vous recevez cet email, car vous avez choisi de suivre ce projet sur le site https://uppm66.herokuapp.com/forum/articles/"
   # emails = [(titre, message, "asso@perma.cat", (suiv.email, )) for suiv in followers(instance)]
    emails = [suiv.email for suiv in followers(instance)  if instance.auteur != suiv  and (instance.estPublic or suiv.is_membre_collectif)]
    try:
        send_mass_mail([(titre, message, "siteuppm66@gmail.com", emails), ])
    except:
        pass



class Evenement(models.Model):
    titre = models.CharField(verbose_name="Titre de l'événement (si laissé vide, ce sera le titre de l'article)",max_length=100, null=True, blank=True, default="")
    article = models.ForeignKey(Article, on_delete=models.CASCADE, help_text="L'événement doit être associé à un article existant (sinon créez un article avec une date)" )
    start_time = models.DateTimeField(verbose_name="Date", null=False,blank=False, help_text="jj/mm/année" , default=timezone.now)
    end_time = models.DateTimeField(verbose_name="Date de fin (optionnel pour un evenement sur plusieurs jours)",  null=True,blank=True, help_text="jj/mm/année")

    class Meta:
        unique_together = ('article', 'start_time',)

    def get_absolute_url(self):
        return self.article.get_absolute_url()


    @property
    def gettitre(self):
        if not self.titre:
            return self.article.titre
        return self.titre

    @property
    def estPublic(self):
        return self.article.estPublic