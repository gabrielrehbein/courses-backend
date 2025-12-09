from rest_framework.views import APIView
from .models import User
from core.utils.exceptions import ValidationError
from core.utils.formatters import format_serializer_error
from .serializers import UserSerializer
from django.contrib.auth.hashers import make_password, check_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import AuthenticationFailed
from .consts import messages

class SignInView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request):
        request_data = request.data

        email = request_data["email"]
        password = request_data["password"]


        user = User.objects.filter(email=email).first()

        if not email or not password:
            raise ValidationError()

        if not user:
            raise AuthenticationFailed(messages.AUTH_LOGIN_ERROR_MESSAGE)
        
        if not check_password(request_data["password"], user.password):
            raise AuthenticationFailed(messages.AUTH_LOGIN_ERROR_MESSAGE)

        user_data = UserSerializer(user).data
        access_token = RefreshToken.for_user(user).access_token

        return Response(
            {
                "user": user_data,
                "access_token": str(access_token)
            }
        )


class SignUpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request):

        request_data = request.data
        data = {
            "name": request_data.get("name"),
            "email": request_data.get("email"),
            "password": request_data.get("password")
        }

        serializer = UserSerializer(data=data)

        if (not serializer.is_valid()):
            raise ValidationError(format_serializer_error(serializer.errors))
        
        hashed_password = make_password(request_data.get("password"))

        user = User.objects.create(
            name=data.get("name"),
            email=data.get("email"),
            password=hashed_password,
        )

        access_token = RefreshToken.for_user(user).access_token

        return Response(
            {
                "user": UserSerializer(user).data,
                "access_token": str(access_token)
            }
        )



        

