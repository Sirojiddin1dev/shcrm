from django.apps import AppConfig


class PurchasesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.purchases'
    verbose_name = 'Haridlar'

    def ready(self):
        from . import signals  # noqa: F401
