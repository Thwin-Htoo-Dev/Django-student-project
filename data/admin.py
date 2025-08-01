from django.contrib import admin
from .models import Student
from import_export import resources
from import_export.admin import ImportExportModelAdmin

class StudentResource(resources.ModelResource):
    class Meta:
        model = Student
class StudentAdmin(ImportExportModelAdmin):
    resource_class = StudentResource
    list_display = ('studentid', 'name','fathername','phone', 'email', 'nrc', 'state', 'major')
    search_fields = ('name', 'email', 'nrc')
    list_filter = ('state', 'major')

admin.site.register(Student,StudentAdmin)

