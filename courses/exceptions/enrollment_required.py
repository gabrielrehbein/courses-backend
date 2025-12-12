from rest_framework.exceptions import APIException
from rest_framework import status


class EnrollmentRequired(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Você precisa estar inscrito no curso."
