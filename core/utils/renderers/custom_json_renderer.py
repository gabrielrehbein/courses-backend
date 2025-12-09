from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework import status


class CustomJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response_data = {}

        response:Response = renderer_context.get("response", None)

        success = True
        if response is not None and response.status_code >= status.HTTP_400_BAD_REQUEST:
            success = False
        
        response_data = {
            "success": success,
            "data": data if data is not None else {},
        }

        if "detail" in data:
            response_data["detail"] = data["detail"]
            del data["detail"]
        
        if "success" in data:
            del data["success"]

        return super().render(response_data, accepted_media_type, renderer_context)