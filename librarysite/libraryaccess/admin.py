from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from libraryaccess.models import Student, Book, Author, Genre, StudentRegister

class AccountAdmin(UserAdmin):
    list_display = ('email', 'username', 'forename', 'surname')
    search_fields = ('email', 'forename', 'surname')
    readonly_fields = ('date_joined', 'last_login')

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

class StudentRegisterAdmin(admin.ModelAdmin):
    list_display = ('ID', 'signinTime', 'signoutTime')
    list_filter = ('ID__surname', 'ID__forename', 'signinTime')
    search_fields = ['ID__forename']

admin.site.register(Student, AccountAdmin)
admin.site.register(Book)
admin.site.register(Author)
admin.site.register(Genre)
admin.site.register(StudentRegister, StudentRegisterAdmin)
