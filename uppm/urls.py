"""Pacte URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from django.conf.urls import include, url
from uppm import views
from django.views.generic import TemplateView
from .views import handler400 as h400, handler403  as h403, handler404  as h404, handler500  as h500

# On import les vues de Django, avec un nom spécifique
from django.contrib.auth.decorators import login_required

# admin.autodiscover()
from django.contrib import admin

urlpatterns = [
    url(r'^summernote/', include('django_summernote.urls')),
    url(r'^captcha/', include('captcha.urls')),
    path(r'agenda/', include('cal.urls')),
    url(r'^forum/', include('blog.urls', namespace='bourseLibre.blog')),
    url('^', include('django.contrib.auth.urls')),
    url(r'^$', views.bienvenue, name='bienvenue'),
    url(r'^bienvenue/$', views.bienvenue, name='bienvenue'),
    url(r'^faq/$', views.faq, name='faq'),
    url(r'^gallerie/$', views.gallerie, name='gallerie'),
    url(r'^notifications/$', views.notifications, name='notifications'),
    url(r'^notifications/news/$', views.notifications_news, name='notifications_news'),
    url(r'^notificationsParDate/$', views.notificationsParDate, name='notificationsParDate'),
    url(r'^notificationsLues/$', views.notificationsLues, name='notificationsLues'),
    url(r'^dernieresInfos/$', views.dernieresInfos, name='dernieresInfos'),
    url(r'^site/presentation/$', views.presentation_site, name='presentation_site'),
    url(r'^gestion/', admin.site.urls, name='admin',),
    url(r'^merci/$', views.merci, name='merci'),
    url(r'^chercher/produit/$', login_required(views.chercher), name='chercher'),
    url(r'^accounts/profil/(?P<user_id>[0-9]+)/$', login_required(views.profil), name='profil', ),
    url(r'^accounts/profil/(?P<user_username>[-\w.]+)/$', login_required(views.profil_nom), name='profil_nom', ),
    url(r'^accounts/profile/$', login_required(views.profil_courant), name='profil_courant', ),
    url(r'^accounts/profil_inconnu/$', views.profil_inconnu, name='profil_inconnu', ),
    url(r'^accounts/profil_modifier/$', login_required(views.profil_modifier.as_view()), name='profil_modifier', ),
    url(r'^accounts/profil_supprimer/$', login_required(views.profil_supprimer.as_view()), name='profil_supprimer', ),
    url(r'^accounts/profil_contact/(?P<user_id>[0-9]+)/$', login_required(views.profil_contact), name='profil_contact', ),
    url(r'^register/$', views.register, name='senregistrer', ),
    url(r'^password/change/$', views.change_password, name='change_password'),
    path('auth/', include('django.contrib.auth.urls')),

    url(r'^contact_admins/$', views.contact_admins, name='contact_admins', ),
    url(r'^cgu/$', views.cgu, name='cgu', ),
    url(r'^liens/$', views.liens, name='liens', ),
    url(r'^fairedon/$', views.fairedon, name='fairedon', ),
    #url(r'^agenda/$', views.agenda, name='agenda',),
    url(r'^cooperateurs/annuaire/$', login_required(views.annuaire), name='annuaire', ),
    url(r'^cooperateurs/listeFollowers/$', login_required(views.listeFollowers), name='listeFollowers', ),
    url(r'^cooperateurs/carte/$', login_required(views.carte), name='carte', ),

    url(r'^conversations/(?P<destinataire>[-\w.]+)$', login_required(views.lireConversation), name='agora_conversation'),
    url(r'^conversations/(?P<destinataire1>[-\w.]+)/(?P<destinataire2>[-\w.]+)$', login_required(
        views.lireConversation_2noms), name='lireConversation_2noms'),
    url(r'^conversations/$', login_required(views.ListeConversations.as_view()), name='conversations'),
    url(r'^conversations/chercher/$', login_required(views.chercherConversation), name='chercher_conversation'),
    url(r'^suivre_conversation/$', views.suivre_conversations, name='suivre_conversations'),
    url(r'^agora/$', login_required(views.agora), name='agora_general'),
    url(r'^activity/', include('actstream.urls')),
    url(r'^inscription_newsletter/$', views.inscription_newsletter, name='inscription_newsletter', ),
    url(r'^modifierMessage/(?P<id>[0-9]+)(?P<type>[-\w.]+)$', views.modifier_message, name='modifierMessage'),
]


urlpatterns += [
    url(r'^robots\.txt$', TemplateView.as_view(template_name="uppm/robots.txt", content_type='text/plain')),
]

from django.conf import settings
if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = h404
handler500 = h500
handler400 = h400
handler403 = h403

if settings.LOCALL:
    import debug_toolbar
    urlpatterns = [url(r'^__debug__/', include(debug_toolbar.urls)),] + urlpatterns
    #urlpatterns += url('',(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}))