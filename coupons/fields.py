from django.db import models


class UpperCaseCharField(models.CharField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        value = super().to_python(value)
        if value is not None:
            return value.upper()
        return value
