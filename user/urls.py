from django.urls import path
from .views import login_page, register_page, landingpage,  list_doctors, show_medical_details, create_medical_details,show_medical_card

urlpatterns = [

    path('', landingpage, name='landingpage'),
    path('login/', login_page, name='user_login'),
    path('register/', register_page, name='register'),
    path('list/', list_doctors, name='list_doctors'),
    path('add/', create_medical_details, name='create_medical_details'),
    path('show/', show_medical_details, name='show_medical_details'),
    path('card/', show_medical_card, name='show_medical_card'),





]
