from rest_framework.exceptions import APIException


class ProductNotFound(APIException):
    status_code = 404
    deafult_detail = "The requested product does not exist"
