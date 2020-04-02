# -*- coding: utf-8 -*-
from .models import  Message, MessageGeneral, Conversation, InscriptionNewsletter


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import ProfilCreationForm, ProducteurChangeForm_admin
from .models import Profil
from django.utils.translation import gettext_lazy as _
from blog.models import Article, Commentaire, Evenement


class CustomUserAdmin(UserAdmin):
    add_form = ProfilCreationForm
    form = ProducteurChangeForm_admin
    model = Profil
    list_display = ['email', 'username',  'date_notifications', 'last_login', 'inscrit_newsletter', 'statut_adhesion']

    readonly_fields = ('date_registration','last_login')

    fieldsets = (
        (None, {'fields': ('username','inscrit_newsletter', 'statut_adhesion', 'date_notifications')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        )

class MyModelAdmin(admin.ModelAdmin):
    list_display = ['tag_list']

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())

class ArticleAdmin(admin.ModelAdmin):
    list_display = ('titre', 'estPublic', 'estArchive')
class ProjetAdmin(admin.ModelAdmin):
    list_display = ('titre', 'estPublic', 'estArchive')
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('nom_produit', 'categorie', 'estUneOffre', 'estPublique', 'unite_prix')

admin.site.register(Profil, CustomUserAdmin)

admin.site.register(Article)
admin.site.register(Commentaire),
admin.site.register(Evenement)
admin.site.register(Message)
admin.site.register(MessageGeneral)
admin.site.register(InscriptionNewsletter)

admin.site.register(Conversation)

