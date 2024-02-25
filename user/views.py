import qrcode
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings

from .forms import UserForm, MedicalDetailsForm
from .models import User, MedicalDetails, Medications, Appointments
from doctor.models import Doctor


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

    
def login_page(request):

    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            if user_exist(request.POST.get('username', ''),request.POST.get('password', '')):
                   
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



def register_page(request):
 
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid() and valid_username(form):
                form.save()
                return redirect('/login')
    else:
        form = UserForm()
    context = {
        'form': form,
        "breach_message":""

    }
    return render(request, 'user/register.html', context)


def landingpage(request):
    username=request.user
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
    return render(request, 'user/list_doctor.html', context)


def create_qrcode(data,user):
      
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

 
def create_medical_details(request):
    if request.method == 'POST':
            form = MedicalDetailsForm(request.POST,request.FILES)
       
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
                     
                medical_info=(f"Blood Group: {data.bloodGroup} \n\nChronic disease: {data.chronicDisease} \n\nKnown allergies: {data.knownAllergies} \n\nFamily history: {data.familyHistory} \n\n ")
               
                create_qrcode(medical_info,request.user )
                return redirect("/") 
            else:
                 print("Form errors:", form.errors)
    else:   

            form = MedicalDetailsForm()
    return render(request, 'user/medical_details.html', {'form': form})    

def show_medical_details(request):
    medicalDetails = MedicalDetails.objects.filter(userID=request.user.id)[0]
    return render(request, 'user/show_medical_details.html', {'medicalDetails': medicalDetails})    

def show_medical_card(request):
   
    return render(request, 'user/show_medical_card.html', {'medicalDetails': "medicalDetails"})    

    