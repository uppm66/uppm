from django.apps import AppConfig

class UppmConfig(AppConfig):
    name = 'uppm'

    def ready(self):
        from actstream import registry
        from django.contrib.auth.models import Group
        from blog.models import Article, Commentaire
        registry.register(self.get_model('Profil'))
        registry.register(self.get_model('MessageGeneral'))
        registry.register(self.get_model('Conversation'))
        registry.register(self.get_model('Suivis'))
        registry.register(Article)
        registry.register(Commentaire)
        registry.register(Group)
