from django.db import models
from django.core.validators import RegexValidator

def generate_default_nrc():
    return '12/ABC(N)000000'

class Student(models.Model):
    STATE_CHOICES = [
        ('', '----Select Your State ----'),
        ('ML', 'Mandalay'),
        ('YG', 'Yangon'),
        ('NP', 'Naypyidaw'),
        ('MG', 'Magway'),
        ('SH', 'Shan'),
    ]

    MAJOR_CHOICES = [
        ('','---- Select Your Major ----'),
        ('CS', 'Computer Science'),
        ('IT', 'Information Technology'),
        ('BA', 'Business Administration'),
        ('EDU', 'Education'),
        ('ENG', 'Engineering'),
    ]

    nrc_validator = RegexValidator(
        regex= r'^(1[0-4]|[1-9])/[A-Za-z]{3,10}\((N|NA)\)\d{6}$',
        message='NRC must be in the format 1/AGaPa(N)224768')

    studentid = models.AutoField(primary_key=True)
    nrc = models.CharField(
        max_length=20,
        validators=[nrc_validator],
        default=generate_default_nrc,
        unique=True,null=False, blank=False)
    name = models.CharField(max_length=100, blank=False)
    fathername = models.CharField(max_length=100, default='',blank=False,null= False)
    email = models.EmailField()
    state = models.CharField(max_length=50, choices=STATE_CHOICES)
    address = models.TextField()
    dob = models.DateField(verbose_name="Date of Birth")
    phone = models.CharField(max_length=20)
    major = models.CharField(max_length=50, choices=MAJOR_CHOICES)

    def __str__(self):
        return f"{self.name} ({self.studentid})"
