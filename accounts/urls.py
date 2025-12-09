from .views import SignUpView, SignInView
from django.urls import path

urlpatterns = [
    path('accounts/signup/', SignUpView.as_view(), name="sign_up"),
    path('accounts/signin/', SignInView.as_view(), name="sign_in"),
]
