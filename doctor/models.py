from django.db import models


class Doctor(models.Model):
    username = models.CharField(max_length=100)
    password= models.CharField(max_length=100, default='')
    photo = models.ImageField(upload_to='doctors', default='')
    qualification = models.CharField(max_length=100, default='')
    details = models.TextField(default='')
    tags = models.CharField(max_length=100, default='')
    rating = models.IntegerField(default=3)
    price_range = models.CharField(max_length=30, default='')
    location = models.CharField(max_length=30, default='')

    def __str__(self):
        return self.username
