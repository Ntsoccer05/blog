from django.apps import AppConfig


class BlogappConfig(AppConfig):
    name = 'blogapp'

    def ready(self):
        # シグナルのロードをする。signals.pyを読み込むだけでOK
        from . import signals