from django.urls import path
from .views import dashboard, add_prescription, dashboard,register_page, login_page


urlpatterns = [
    path('login/', login_page, name='login_page'),
    path('register/', register_page, name='register_page'),
    path('', dashboard, name='dashboard'),
    path('<doctor_id>/dashboard', dashboard, name='dashboard'),

    path('<doctor_id>/add_prescription',
         add_prescription, name='add_prescription'),


]
