from django.apps import AppConfig


class AdminPanelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin_panel'
    verbose_name = "Admin Panel"

    #
    # If you add signals.py later, just uncomment:
    #
    # def ready(self):
    #     import admin_panel.signals
