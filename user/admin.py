from django.contrib import admin
from .models import User, Appointments, Medications, MedicalDetails


admin.site.register(User)

admin.site.register(Appointments)
admin.site.register(Medications)
admin.site.register(MedicalDetails)