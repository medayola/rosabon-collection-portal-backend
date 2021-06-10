from django.apps import AppConfig


class MandatesConfig(AppConfig):
    name = 'mandates'

    def ready(self):
        import mandates.signals
