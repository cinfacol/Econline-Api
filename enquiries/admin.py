from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Enquiry


class EnquiryAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "phone_number", "message"]
    output = _(list_display)


admin.site.register(Enquiry, EnquiryAdmin)
