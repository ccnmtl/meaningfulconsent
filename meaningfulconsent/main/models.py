from django import forms
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.fields import CharField
from django.db.models.fields.related import OneToOneField
from django.db.models.signals import post_save
from django.contrib.contenttypes import generic
from pagetree.models import Hierarchy, UserPageVisit, PageBlock
from rest_framework import serializers, viewsets

USERNAME_LENGTH = 9
USERNAME_PREFIX = 'MC'

LANGUAGES = (
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
    language = models.CharField(max_length=2, default="en", choices=LANGUAGES)
    creator = models.ForeignKey(User, null=True, blank=True,
                                related_name='creator')
    archived = models.BooleanField(default=False)
    notes = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    def is_participant(self):
        return (not self.user.is_active and
                self.user.username.startswith(USERNAME_PREFIX))

    def default_location(self):
        hierarchy = Hierarchy.get_hierarchy(self.language)
        return hierarchy.get_root()

    def last_access(self):
        hierarchy = Hierarchy.get_hierarchy(self.language)
        upv = UserPageVisit.objects.filter(
            user=self.user, section__hierarchy=hierarchy).order_by(
            "-last_visit")
        if len(upv) < 1:
            return self.created
        else:
            return upv[0].last_visit

    def last_location_url(self):
        if self.percent_complete() == 0:
            return reverse('participant-language')
        else:
            return self.last_location().get_absolute_url()

    def last_location(self):
        hierarchy = Hierarchy.get_hierarchy(self.language)
        upv = UserPageVisit.objects.filter(
            user=self.user, section__hierarchy=hierarchy).order_by(
            "-last_visit")
        if len(upv) < 1:
            return hierarchy.get_root()
        else:
            return upv[0].section

    def percent_complete(self):
        hierarchy = Hierarchy.get_hierarchy(self.language)
        pages = len(hierarchy.get_root().get_descendants())
        visits = UserPageVisit.objects.filter(user=self.user,
                                              section__hierarchy=hierarchy)
        if pages:
            return int(len(visits) / float(pages) * 100)
        else:
            return 0


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        clinics = Clinic.objects.all()
        if len(clinics) < 1:
            clinic = Clinic.objects.create(name='Pilot')
        else:
            clinic = clinics[0]
        UserProfile.objects.get_or_create(user=instance, clinic=clinic)

post_save.connect(create_user_profile, sender=User)


class UserVideoView(models.Model):
    user = models.ForeignKey(User)
    video_url = models.CharField(max_length=512)
    video_duration = models.IntegerField(default=0)
    seconds_viewed = models.IntegerField(default=0)

    def percent_viewed(self):
        rv = float(self.seconds_viewed) / self.video_duration * 100
        return rv

    class Meta:
        unique_together = (('user', 'video_url'),)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username',)


class ParticipantSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSerializer(many=False, read_only=True)
    percent_complete = serializers.Field(source='percent_complete')
    last_access = serializers.Field()

    class Meta:
        model = UserProfile
        fields = ('user', 'percent_complete', 'notes', 'last_access')


class ParticipantViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.filter(
        archived=False,
        user__username__startswith=USERNAME_PREFIX,
        user__is_active=False).order_by('-modified')

    model = UserProfile
    serializer_class = ParticipantSerializer


class QuizSummaryBlock(models.Model):
    pageblocks = generic.GenericRelation(
        PageBlock, related_name="quiz_summary")
    template_file = "main/quiz_summary_block.html"
    display_name = "Quiz Summary Block"
    quiz_class = models.CharField(max_length=50)

    def pageblock(self):
        return self.pageblocks.all()[0]

    def __unicode__(self):
        return unicode(self.pageblock())

    @classmethod
    def add_form(self):
        return QuizSummaryForm()

    def edit_form(self):
        return QuizSummaryForm(instance=self)

    @classmethod
    def create(self, request):
        form = QuizSummaryForm(request.POST)
        return form.save()

    def edit(self, vals, files):
        form = QuizSummaryForm(data=vals, files=files, instance=self)
        if form.is_valid():
            form.save()

    def needs_submit(self):
        return False

    def unlocked(self, user):
        return True


class QuizSummaryForm(forms.ModelForm):
    class Meta:
        model = QuizSummaryBlock
