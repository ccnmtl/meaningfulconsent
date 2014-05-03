from django.contrib.auth.models import User
from django.db import models
from django.db.models.fields import CharField
from django.db.models.fields.related import OneToOneField
from pagetree.models import Hierarchy, UserLocation, UserPageVisit


LANGUAGE_CHOICES = (
    ('en', 'English'),
    ('es', 'Spanish')
)


class Clinic(models.Model):
    name = CharField(max_length=25)

    def __unicode__(self):
        return self.name


class UserProfile(models.Model):
    user = OneToOneField(User, related_name="profile")
    clinic = models.ForeignKey(Clinic)
    is_participant = models.BooleanField(default=True)
    language = models.CharField(max_length=2, default='en',
                                choices=LANGUAGE_CHOICES)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    def default_location(self):
        hierarchy = Hierarchy.get_hierarchy(self.language)
        return hierarchy.get_root()

    def last_location(self):
        upv = UserPageVisit.objects.filter(
            user=self.user).order_by("-last_visit")
        if len(upv) < 1:
            hierarchy = Hierarchy.get_hierarchy(self.language)
            return hierarchy.get_root()
        else:
            return upv[0].section

    def percent_complete(self):
        hierarchy = Hierarchy.get_hierarchy(self.language)
        pages = len(hierarchy.get_root().get_descendants()) + 1
        visits = UserPageVisit.objects.filter(user=self.user,
                                              section__hierarchy=hierarchy)
        if pages:
            return int(len(visits) / float(pages) * 100)
        else:
            return 0
