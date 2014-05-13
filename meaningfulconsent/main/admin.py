from django.contrib import admin
from meaningfulconsent.main.models import UserProfile, Clinic
from pagetree.models import Hierarchy, UserLocation, UserPageVisit

admin.site.register(Clinic)
admin.site.register(Hierarchy)
admin.site.register(UserLocation)
admin.site.register(UserPageVisit)


class UserProfileAdmin(admin.ModelAdmin):
    class Meta:
        model = UserProfile

    search_fields = ("user__username",)
    list_display = ("user", "clinic", "language", "created")

admin.site.register(UserProfile, UserProfileAdmin)
