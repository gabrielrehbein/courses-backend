from django.apps import AppConfig
import stripe
from decouple import config


class CoursesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'courses'

    def ready(self):
        stripe.api_key = config("STRIPE_SECRET_KEY")
