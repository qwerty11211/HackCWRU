from django.shortcuts import render, redirect
from .models import Doctor
from .forms import DoctorForm
from user.models import  Appointments
from pangea.config import PangeaConfig
from pangea.services import Redact, Audit
import os
import openai
import datetime
import speech_recognition as sr

config = PangeaConfig(domain=os.getenv("PANGEA_DOMAIN"))  
audit = Audit(os.getenv("PANGEA_AUDIT_TOKEN"), config=config) 

def user_exist(credential):
    username = credential.cleaned_data.get("username")
    password = credential.cleaned_data.get("password")
    user = Doctor.objects.filter(username=username, password=password)
    if user:
        return True
    else:
        return False


def valid_username(credential):
    username = credential.cleaned_data.get("username")
    user = Doctor.objects.filter(username=username)
    if user:
        return False
    else:
        return True


def login_page(request):
    
    if request.method == 'POST':
        audit.log(f"Made a POST request to doctor login page")
        form = DoctorForm(request.POST)
        if form.is_valid():
            if user_exist(form):
            
                return redirect('/doctor/1')
    else:
        form = DoctorForm()
        audit.log(f"Made a GET request to doctor login page")
    context = {
        'form': form
    }
    return render(request, 'doctor/login.html', context)


def register_page(request):
    
    if request.method == 'POST':
        form = DoctorForm(request.POST)
        if form.is_valid() and valid_username(form):
            form.save()
            return redirect('/doctor/login')
    else:
        form = DoctorForm()
        audit.log(f"Made a GET request to doctor register page")
    context = {
        'form': form
    }
    return render(request, 'doctor/register.html', context)


def dashboard(request):
    doctor_id=request.user.id
    audit.log(f"{request.user} has accessed the doctor landing page")
    doctor_details = Doctor.objects.get(id=doctor_id)
    appointments = Appointments.objects.filter(doctorid=doctor_id).order_by('datetime')
    context = {
        'appointments': appointments,
        'doctor': doctor_details,
        'todays_date': datetime.datetime.now().date().strftime('%d-%m-%Y'),

    }
    return render(request, 'doctor/dashboard.html', context)


def doctor_details(request, doctor_id):
    doctor_details = Doctor.objects.get(id=doctor_id)
    audit.log(f"Displaying the doctor info of {doctor_details}")
    context = {
        'doctor': doctor_details,
    }

    return render(request, 'user/doctor-details.html', context)


def book_appointment(request, doctor_id):
    doctor_details = Doctor.objects.get(id=doctor_id)
    return render(request, 'user/book_appointment.html', {
        'doctor': doctor_details,
    })


def checkout(request, doctor_id):
    doctor_details = Doctor.objects.get(id=doctor_id)
    return render(request, 'user/checkout.html', {
        'doctor': doctor_details,
    })





def make_openapi_call(prompt):
    openai.api_key=os.getenv("OPENAI_KEY")
    # openai_response = vault.get(
    #     id=os.getenv("OPENAI_VAULT_ID"),
    #     version=1,
    #     verbose=True,
    # )
    # openai.api_key=openai_response.result.current_version.secret
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=2048
    )
    result=response["choices"][0]["text"]
    print(result)
    return result



def add_prescription(request, doctor_id):
    doctor_details = Doctor.objects.get(id=doctor_id)
    r = sr.Recognizer()
    print("initiating")

    with sr.Microphone() as source:
        print("listening")
        audio = r.listen(source)
    text = r.recognize_google(audio)
    config = PangeaConfig(domain=os.getenv("PANGEA_DOMAIN"))  
    redact = Redact(os.getenv("PANGEA_TOKEN"), config=config) 
    response = redact.redact(
        text=text
        )
    redacted_text=response.result.redacted_text

    diseases=make_openapi_call(f"List as points without explanation the top 2 names of disease that is likely given the following   : {', '.join(redacted_text)}")
    medicine=''

    for disease in diseases.split("\n"):
        medicine+=make_openapi_call(f"What are the  medication for {disease}")

    text=f"Disease: {diseases} \n\n\n Prescription {medicine}"
    return render(request, 'doctor/prescription.html', {
        'doctor': doctor_details, 'text':text,
    })
