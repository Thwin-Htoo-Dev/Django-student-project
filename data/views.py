from django.shortcuts import render,get_object_or_404,redirect
from django.http import HttpResponse
from django.db.models import Q
from .models import Student
from .forms import StudentForm
import csv
import json
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import JsonResponse
from decimal import Decimal, InvalidOperation


# Create your views here.

def student_list(request):
    query = request.GET.get('q','')
    if query:
        students = Student.objects.filter(
            Q(studentid__icontains=query) |
            Q(name__icontains=query)
        )
    else:
        students = Student.objects.all()

    total_students = Student.objects.count()

    #pagination 10 per page
    paginator =Paginator(students,10)
    page_number =request.GET.get('page')
    #get the page object
    page_obj = paginator.get_page(page_number)


    return render(request, 'students/student_list.html', {
        'students': students,
        'query': query,
        'total_students': total_students,
        'page_obj':page_obj,
    })

def student_detail(request,pk):
    student = get_object_or_404(Student, pk=pk)
    form = StudentForm(instance=student)

    for field in form.fields.values():
        field.widget.attrs['readonly'] = True
        field.widget.attrs['disabled'] = True

    return render(request, 'students/student_form.html', {'form': form, 'mode': 'detail','student':form.instance})

    

def student_create(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Student created successfully.')
            return redirect('student_list')
        else:
            return render(request, 'students/student_form.html', {
                'form': form,
                'mode':'create',
                'form_error': 'Please fill in all required fields correctly.'
        })
    else:
        form = StudentForm()
        return render (request,'students/student_form.html',{
            'form':form,'mode':'create','student':form.instance,})
    
def student_update(request,pk):
    student = get_object_or_404(Student,pk=pk)
    form = StudentForm(request.POST or None,instance=student)
    if form.is_valid():
        form.save()
        messages.success(request,"✅ Student data updated successfully.")
        return redirect ('student_list')
    return render(request,'students/student_form.html',{'form':form,'mode':'update','student':form.instance,})

def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    form = StudentForm(instance=student)

    if request.method == 'POST':
        student.delete()
      
        messages.success(request, f"Student {student.name} deleted successfully.")
        return redirect('student_list')
   

    # Disable fields in form
    for field in form.fields.values():
        field.disabled = False

    return render(request, 'students/student_form.html', {
        'form': form,
        'student':form.instance,
        'delete_mode': True,
        'mode': 'delete'
    })
def parse_date(date_str):
    formats = [
        '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y',
        '%b. %d, %Y', '%B %d, %Y'
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None

def clean_phone_number(raw_phone):
    if not raw_phone:
        return ''

    raw_phone = str(raw_phone).strip().replace(' ', '').replace('-', '')

    try:
        if 'e' in raw_phone.lower():
            raw_phone = str(Decimal(raw_phone).to_integral_value())
    except (InvalidOperation, ValueError):
        return ''

    if raw_phone.startswith('+959'):
        return raw_phone
    elif raw_phone.startswith('09'):
        return '+959' + raw_phone[2:]
    elif raw_phone.startswith('959'):
        return '+959' + raw_phone[3:]
    elif raw_phone.startswith('9'):
        return '+959' + raw_phone[1:]
    else:
        return '+959' + raw_phone.lstrip('0')

def student_import_export(request):
    if request.method == 'POST':
        file_format = request.POST.get('file-format')
        query = request.POST.get('q', '').strip()

        if 'export' in request.POST:
            students = Student.objects.all()
            if query:
                students = students.filter(
                    Q(studentid__icontains=query) |
                    Q(name__icontains=query) |
                    Q(nrc__icontains=query)
                )
                if not students.exists():
                    messages.error(request, "Student list not found in table")
                    return redirect('student_list')

            if file_format == 'csv':
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="students.csv"'
                writer = csv.writer(response)
                writer.writerow(['NRC', 'Name', 'Fathername', 'Email', 'Phone', 'State', 'Address', 'Major', 'DOB'])
                for s in students:
                    writer.writerow([
                         s.nrc, s.name, s.fathername, s.email,
                        f"'{s.phone}", s.get_state_display(), s.address,
                        s.get_major_display(), s.dob.strftime('%d-%m-%Y') if s.dob else ''
                    ])
                return response

            elif file_format == 'json':
                data = [{
                    #'studentid': s.studentid,
                    'nrc': s.nrc,
                    'name': s.name,
                    'fathername': s.fathername,
                    'email': s.email,
                    'phone': s.phone,
                    'state': s.get_state_display(),
                    'address': s.address,
                    'major': s.get_major_display(),
                    'dob': s.dob.isoformat() if s.dob else None,
                } for s in students]
                response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
                response['Content-Disposition'] = 'attachment; filename="students.json"'
                return response

        elif 'import' in request.POST:
            file = request.FILES.get('importFile')
            if not file:
                messages.error(request, "No file uploaded.")
                return redirect('student_list')

            if file_format == 'csv':
                decoded = file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded)

                for row in reader:
                    try:
                        row = {k.lower(): v.strip() for k, v in row.items()}
                        studentid = row.get('studentid')
                        email = row.get('email')
                        nrc = row.get('nrc')
                        dob_str = row.get('dob')
                        dob = parse_date(dob_str) if dob_str else None
                        phone = clean_phone_number(row.get('phone', ''))

                        if Student.objects.filter(studentid=studentid).exists():
                            messages.error(request, f"⚠️ Duplicate student ID: {studentid}")
                            continue
                        if Student.objects.filter(nrc=nrc).exists():
                            messages.error(request, f"⚠️ Duplicate NRC: {nrc}")
                            continue
                        if Student.objects.filter(email=email).exists():
                            messages.error(request, f"⚠️ Duplicate Email: {email}")
                            continue

                        if dob_str and not dob:
                            messages.error(request, f"⚠️ Invalid DOB format: {dob_str}")
                            continue

                        Student.objects.create(
                            studentid=studentid,
                            nrc=nrc,
                            name=row.get('name'),
                            fathername=row.get('fathername'),
                            email=email,
                            phone=phone,
                            state=row.get('state'),
                            address=row.get('address'),
                            major=row.get('major'),
                            dob=dob
                        )
                        messages.success(request, f"Student {studentid} imported successfully.")
                    except Exception as e:
                        messages.error(request, f"Error importing row: {e}")

            elif file_format == 'json':
                try:
                    data = json.load(file)
                    for item in data:
                        studentid = item.get('studentid')
                        email = item.get('email')
                        nrc = item.get('nrc')

                        if Student.objects.filter(studentid=studentid).exists():
                            messages.error(request, f"⚠️ Duplicate student ID: {studentid}")
                            continue
                        if Student.objects.filter(nrc=nrc).exists():
                            messages.error(request, f"⚠️ Duplicate NRC: {nrc}")
                            continue
                        if Student.objects.filter(email=email).exists():
                            messages.error(request, f"⚠️ Duplicate Email: {email}")
                            continue

                        if 'dob' in item and item['dob']:
                            parsed_dob = parse_date(item['dob'])
                            if not parsed_dob:
                                messages.error(request, f"⚠️ Invalid DOB format: {item['dob']}")
                                continue
                            item['dob'] = parsed_dob

                        item['phone'] = clean_phone_number(item.get('phone', ''))
                        Student.objects.create(**item)
                        messages.success(request, f"Student {studentid} imported successfully.")
                except Exception as e:
                    messages.error(request, f"JSON import error: {e}")

    return redirect('student_list')

def export_selected_students(request):
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_students')
        file_format = request.POST.get('file-format')

        students = Student.objects.filter(studentid__in=selected_ids)
        if not students.exists():
            messages.error(request, "⚠️ No students selected for export.")
            return redirect('student_list')

        if file_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="selected_students.csv"'
            writer = csv.writer(response)
            writer.writerow([ 'NRC', 'Name', 'Fathername', 'Email', 'Phone', 'State', 'Address', 'Major', 'DOB'])
            for s in students:
                writer.writerow([
                     s.nrc, s.name, s.fathername, s.email,
                    f"'{s.phone}", s.get_state_display(), s.address,
                    s.get_major_display(), s.dob.strftime('%d-%m-%Y') if s.dob else ''
                ])
            return response

        elif file_format == 'json':
            data = [{
                'studentid': s.studentid,
                'nrc': s.nrc,
                'name': s.name,
                'fathername': s.fathername,
                'email': s.email,
                'phone': s.phone,
                'state': s.get_state_display(),
                'address': s.address,
                'major': s.get_major_display(),
                'dob': s.dob.isoformat() if s.dob else None,
            } for s in students]
            response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
            response['Content-Disposition'] = 'attachment; filename="selected_students.json"'
            return response
"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import StudentSerializer

@api_view(['GET'])
def student_list(request):
"""
