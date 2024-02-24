from dotenv import load_dotenv
import os, requests
import qrcode
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings

from .forms import UserForm, MedicalDetailsForm
from .models import User, MedicalDetails, Medications, Appointments
from doctor.models import Doctor

from pangea.config import PangeaConfig
from pangea.services import Audit, UserIntel, Embargo, FileScan, DomainIntel
from pangea.services.intel import HashType
from pangea.tools import logger_set_pangea_config
from pangea.utils import get_prefix, hash_sha256
from pangea.services.vault.vault import Vault
import pangea.exceptions as pe

from celery import shared_task
from datetime import datetime
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

# Load environment variables from .env file
dotenv_path = '.env'
load_dotenv(dotenv_path)

# Access environment variables
config = PangeaConfig(domain=os.getenv("PANGEA_DOMAIN"))  
audit = Audit(os.getenv("PANGEA_AUDIT_TOKEN"), config=config) 

def user_exist(username,password):
    user = User.objects.filter(username=username, password=password)
    if user:
        return True
    else:
        return False


def valid_username(credential):
    username = credential.cleaned_data.get("username")
    user = User.objects.filter(username=username)
    if user:
        return False
    else:
        return True

def get_public_ip():
    try:
        # Use a public IP address API service
        response = requests.get('https://api64.ipify.org?format=json')
        if response.status_code == 200:
            data = response.json()
            return data['ip']
        else:
            return "Failed to retrieve IP address."
    except Exception as e:
        return str(e)
    
def login_page(request):
    ip_addr=get_public_ip()
    sanction_msg=''

    token = os.getenv("PANGEA_TOKEN")
    domain = os.getenv("PANGEA_DOMAIN")
    config = PangeaConfig(domain=domain)
    embargo = Embargo(token, config=config, logger_name="embargo")
    logger_set_pangea_config(logger_name=embargo.logger.name)

    try:
        embargo_response = embargo.ip_check(ip=ip_addr)
        print(f"Response: {embargo_response.result}")
        audit.log(f"A user with ip addresss {ip_addr} has tried to login")
        sanctions_count= embargo_response.result.count
        if sanctions_count>=1:
                sanction_msg=embargo_response.result.summary
    except pe.PangeaAPIException as err:
        print(f"Embargo Request Error: {err.response.summary}")
        for er in err.errors:
            print(f"\t{er.detail} \n")
    
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            if user_exist(request.POST.get('username', ''),request.POST.get('password', '')):
                    audit.log(f"Valid user login in")
                    messages.add_message(request, messages.INFO, 'Logged in!')
                    return redirect('/')
    else:
         form = UserForm()

    sanction_msg=''
    context = {
        'form': form,
        'sanction_msg':sanction_msg
    }
    return render(request, 'user/login.html', context)


def check_password_breach(intel,password):
            breach_message=''
            hash = hash_sha256(password)
            hash_prefix = get_prefix(hash)

            try:
                response = intel.password_breached(
                    # should setup right hash_type here, sha256 or sha1
                    hash_prefix=hash_prefix,
                    hash_type=HashType.SHA256,
                    provider="spycloud",
                    verbose=True,
                    raw=True,
                )
                # This auxiliary function analyze service provider raw data to search for full hash in their registers
                status = UserIntel.is_password_breached(response, hash)
                audit.log(f"Password breach status is {status}")
                
                if status == UserIntel.PasswordStatus.BREACHED:
                    print(f"Password: '{password}' has been breached")
                    breach_message=f"Password: '{password}' has been breached"
                # elif status == UserIntel.PasswordStatus.INCONCLUSIVE:
                #     print(f"Not enough information to confirm if password '{password}' has been or has not been breached.")
                #     breach_message=f"Not enough information to confirm if password '{password}' has been or has not been breached."
                else:
                    print(f"Unknown status: {status}")

            except pe.PangeaAPIException as e:
                print(f"Request Error: {e.response.summary}")
                for err in e.errors:
                    print(f"\t{err.detail} \n")
            return breach_message

def check_email_breach(intel,email):
    try:
        response = intel.user_breached(email=email, provider="spycloud", verbose=True, raw=True)
        print(f"Found in breach: {response.result.data.found_in_breach}")
        print(f"Breach count: {response.result.data.breach_count}")
        status=response.result.data.found_in_breach
        audit.log(f"Email breach status is {status}")
        return status
    except pe.PangeaAPIException as e:
        print(f"Request Error: {e.response.summary}")
        for err in e.errors:
            print(f"\t{err.detail} \n")
        return ''

def check_phone_breach(intel,phone):
    try:
        response = intel.user_breached(phone_number=phone, provider="spycloud", verbose=True, raw=True)
        print(f"Found in breach: {response.result.data.found_in_breach}")
        print(f"Breach count: {response.result.data.breach_count}")
        status=response.result.data.found_in_breach
        audit.log(f"Email breach status is {status}")
        return status
    except pe.PangeaAPIException as e:
        print(f"Request Error: {e.response.summary}")
        for err in e.errors:
            print(f"\t{err.detail} \n")

def domain_intel(email):
    try:
        intel = DomainIntel(os.getenv("PANGEA_TOKEN"), config=config)
        response = intel.reputation(domain=email, provider="domaintools", verbose=True, raw=True)
        print(f"Response: {response.result}")
        return response.result
    except pe.PangeaAPIException as e:
        print(f"Request Error: {e.response.summary}")
        for err in e.errors:
            print(f"\t{err.detail} \n")

def register_page(request):
    breach_message=''
    phone_breach_message=''
    password_breach_message=''
    email_breach_message=''
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid() and valid_username(form):
            token = os.getenv("PANGEA_TOKEN")
            domain = os.getenv("PANGEA_DOMAIN")
            config = PangeaConfig(domain=domain)
            intel = UserIntel(token, config=config, logger_name="intel")
            logger_set_pangea_config(logger_name=intel.logger.name)
            domain_intel(request.POST.get('email'))
            # password_breach_message=check_password_breach(intel,form.cleaned_data.get("password"))
            # email_breach_message=check_email_breach(intel,form.cleaned_data.get("password"))
            # phone_breach_message=check_phone_breach(intel,form.cleaned_data.get("phone"))
            breach_message=password_breach_message+'\n'+email_breach_message+'\n'+phone_breach_message
            if len(breach_message)==1:
                form.save()
                return redirect('/login')
    else:
        form = UserForm()
    context = {
        'form': form,
        "breach_message":breach_message

    }
    return render(request, 'user/register.html', context)


def landingpage(request):
    username=request.user
    audit.log(f"{request.user} has accessed the landing page")
    onGoingMedicines=Medications.objects.filter(patientid=request.user.id)
    appointments=Appointments.objects.filter(patientid=request.user.id).order_by('datetime')
    context = {
        'username':username,
        'medications': onGoingMedicines,
        'appointments':appointments
    }
    return render(request, 'user/dashboard.html',context)


def list_doctors(request):
    data = Doctor.objects.filter()
    context = {
        'doctor_info': data,
    }
    audit.log(f" doctor_info {data}")
    return render(request, 'user/list_doctor.html', context)


def create_qrcode(data,user):
            audit.log(f"Creating a new QR for the data {data}")
            # Create a QR code instance
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L, 
                box_size=10, 
                border=4,  
            )
            qr.add_data(data)
            qr.make(fit=True)

            # Create an image from the QR code
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(f"./media/qrcodes/{user}1.png")
            img.show()

 
def file_intel(path):
    client = FileScan(os.getenv("PANGEA_TOKEN", config=config, logger_name="pangea"))
    try:
        with open(path, "rb") as f:
            response = client.file_scan(file=f, verbose=True, provider="crowdstrike")
            print(f"Response: {response.result}")
            return response.result
    except pe.PangeaAPIException as e:
        print(f"Request Error: {e.response.summary}")
        for err in e.errors:
            print(f"\t{err.detail} \n")
     
def create_medical_details(request):
    if request.method == 'POST':
            form = MedicalDetailsForm(request.POST,request.FILES)
            audit.log(f"Made a POST request to create medical details {form}")
            path='MedicalReport.pdf'
            if form.is_valid():
                # Save the form data to create a new instance of your model
                instance = form.save(commit=False) 
                instance.userID = request.user.id
                instance.save()
                data=MedicalDetails.objects.filter(userID=request.user.id).last()
                report_path=request.POST.get('medicalReportpdf')
                if report_path:
                     path=report_path
                     
                file_intel(path)
                medical_info=(f"Blood Group: {data.bloodGroup} \n\nChronic disease: {data.chronicDisease} \n\nKnown allergies: {data.knownAllergies} \n\nFamily history: {data.familyHistory} \n\n ")
               
                create_qrcode(medical_info,request.user )
                return redirect("/") 
            else:
                 print("Form errors:", form.errors)
    else:   
            audit.log(f"Made a GET request to create medical details")
            form = MedicalDetailsForm()
    return render(request, 'user/medical_details.html', {'form': form})    

def show_medical_details(request):
    audit.log(f"Made a GET request to show medical details")
    medicalDetails = MedicalDetails.objects.filter(userID=request.user.id)[0]
    return render(request, 'user/show_medical_details.html', {'medicalDetails': medicalDetails})    

def show_medical_card(request):
    audit.log(f"Made a GET request to show medical card")
    return render(request, 'user/show_medical_card.html', {'medicalDetails': "medicalDetails"})    

@shared_task
def check_medicine_schedule():
    now = datetime.now().time()
    medicines_to_take = Medications.objects.filter(schedule_time=now)

    for medicine in medicines_to_take:
        make_twilio_call(medicine)

def make_twilio_call(medicine):
    audit.log(f"Making a twilio call")
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    vault = Vault( os.getenv("PANGEA_TOKEN"), config=config)
    # Temporarily commenting out the code

    # account_sid_vault_response = vault.get(
    #     id=os.getenv("TWILIO_AUTH_VAULT_ID"),
    #     version=1,
    #     verbose=True,
    # )
    # account_sid=account_sid_vault_response.result.current_version.secret
    # auth_token_vault_response = vault.get(
    #     id=os.getenv("TWILIO_AUTH__VAULT_ID"),
    #     version=1,
    #     verbose=True,
    # )
    # auth_token=auth_token_vault_response.result.current_version.secret
    twilio_phone_number = '+15178782860'

    client = Client(account_sid, auth_token)
    response = VoiceResponse()
    response.say(f"It's time to take your {medicine.name} medication. Please take {medicine.dosage}.")
    response.hangup()

    client.calls.create(
        to=os.getenv("RECIPIENT_PHONE_NUMBER") ,
        from_=twilio_phone_number,
        twiml=str(response)
    )