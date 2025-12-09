from rest_framework.exceptions import APIException
from rest_framework import status

class ValidationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Parâmetros inválidos para a requisicão'
    default_code = 'validation_error'