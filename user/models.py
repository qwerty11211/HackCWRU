from django.db import models


class User(models.Model):
    username = models.CharField(max_length=100)
    email= models.CharField(max_length=100,default='')
    phone=models.IntegerField()
    password = models.CharField(max_length=200)


    def __str__(self):
        return self.username


class Appointments(models.Model):
    patientid = models.IntegerField()
    patientname = models.CharField(max_length=120)
    doctorid = models.IntegerField()
    doctorname = models.CharField(max_length=120)
    datetime = models.DateTimeField()
    type = models.CharField(max_length=80)
    amount = models.IntegerField()

    def __str__(self):
        return "patient "+str(self.patientid)+" doctor "+str(self.doctorid)


class Medications(models.Model):
    patientid = models.IntegerField()
    doctorid = models.IntegerField()
    doctorname = models.CharField(max_length=80)
    medicinename = models.CharField(max_length=80)
    quantity = models.CharField(max_length=80)
    days = models.CharField(max_length=80)
    time = models.CharField(max_length=80)

    def __str__(self):
        return self.medicinename


class MedicalDetails(models.Model):
    userID = models.IntegerField()
    bloodGroup = models.CharField(max_length=20)
    onGoingMedication = models.TextField(max_length=2000)
    chronicDisease = models.TextField(max_length=2000)
    knownAllergies = models.TextField(max_length=2000)
    familyHistory= models.TextField(max_length=2000)
    medicalReportpdf = models.FileField(upload_to='medical_reports/', blank=True, null=True)
    
