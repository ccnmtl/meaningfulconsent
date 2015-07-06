from django.contrib import admin
from meaningfulconsent.main.models import UserProfile, Clinic, UserVideoView
from pagetree.models import Hierarchy, UserLocation, UserPageVisit

admin.site.register(Clinic)
admin.site.register(Hierarchy)
admin.site.register(UserLocation)
admin.site.register(UserPageVisit)


class UserVideoViewAdmin(admin.ModelAdmin):
    class Meta:
        model = UserVideoView

    search_fields = ("user__username",)
    list_display = ("user", "video_id", "video_duration", "seconds_viewed")

admin.site.register(UserVideoView, UserVideoViewAdmin)


class UserProfileAdmin(admin.ModelAdmin):
    class Meta:
        model = UserProfile

    search_fields = ("user__username",)
    list_display = ("user", "clinic", "language", "created")

admin.site.register(UserProfile, UserProfileAdmin)
