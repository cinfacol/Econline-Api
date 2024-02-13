from rest_framework.exceptions import APIException


class InventoryNotFound(APIException):
    status_code = 404
    deafult_detail = "The requested inventory does not exist"
