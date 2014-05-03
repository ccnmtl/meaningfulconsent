from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from meaningfulconsent.main.models import UserProfile, Clinic
from pagetree.models import Hierarchy, UserLocation, UserPageVisit


class UserProfileInline(admin.StackedInline):
    model = UserProfile


class UserProfileAdmin(UserAdmin):
    inlines = [UserProfileInline, ]


admin.site.unregister(User)
admin.site.register(User, UserProfileAdmin)

admin.site.register(Clinic)
admin.site.register(Hierarchy)
admin.site.register(UserLocation)
admin.site.register(UserPageVisit)
