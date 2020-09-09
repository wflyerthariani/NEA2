from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from libraryaccess.models import Student

class AccountAdmin(UserAdmin):
    list_display = ('email', 'username', 'forename', 'surname')
    search_fields = ('email', 'forename', 'surname')
    readonly_fields = ('date_joined', 'last_login')

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

admin.site.register(Student, AccountAdmin)
