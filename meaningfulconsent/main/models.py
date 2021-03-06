from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models.fields import CharField
from django.db.models.fields.related import OneToOneField
from django.db.models.signals import post_save
from django.template.defaultfilters import slugify
from django.urls.base import reverse
from django.utils.encoding import python_2_unicode_compatible
from pagetree.models import Hierarchy, UserPageVisit, PageBlock
from pagetree.reports import PagetreeReport, ReportableInterface, \
    StandaloneReportColumn, ReportColumnInterface
from rest_framework import serializers, viewsets


USERNAME_LENGTH = 9
USERNAME_PREFIX = 'MC'

LANGUAGES = (
    ('en', 'English'),
    ('es', 'Spanish')
)


@python_2_unicode_compatible
class Clinic(models.Model):
    name = CharField(max_length=25)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = OneToOneField(User, related_name="profile",
                         on_delete=models.CASCADE)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    language = models.CharField(max_length=2, default="en", choices=LANGUAGES)
    creator = models.ForeignKey(User, null=True, blank=True,
                                related_name='creator',
                                on_delete=models.CASCADE)
    archived = models.BooleanField(default=False)
    notes = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    def is_participant(self):
        return (not self.user.is_active and
                self.user.username.startswith(USERNAME_PREFIX))

    def default_hierarchy(self):
        return Hierarchy.get_hierarchy(self.language)

    def default_location(self):
        return self.default_hierarchy().get_root()

    def last_access(self):
        return self.last_access_hierarchy(self.language) or self.created

    def last_access_formatted(self, hierarchy_name):
        dt = self.last_access_hierarchy(hierarchy_name)
        return dt.strftime("%Y-%m-%dT%H:%M:%S") if dt else ''

    def last_access_hierarchy(self, hierarchy_name):
        hierarchy = Hierarchy.get_hierarchy(hierarchy_name)

        upv = UserPageVisit.objects.filter(
            user=self.user, section__hierarchy=hierarchy).order_by(
            "-last_visit")
        if upv.count() < 1:
            return None
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
        if upv.count() < 1:
            return hierarchy.get_root()
        else:
            return upv[0].section

    def percent_complete(self):
        return self.percent_complete_hierarchy(self.language)

    def percent_complete_hierarchy(self, hierarchy_name):
        hierarchy = Hierarchy.get_hierarchy(hierarchy_name)
        pages = hierarchy.get_root().get_descendants().count()
        visits = UserPageVisit.objects.filter(
            user=self.user, section__hierarchy=hierarchy).count()
        if pages > 0:
            return int(visits / float(pages) * 100)
        else:
            return 0

    def time_spent(self, hierarchy_name):
        hierarchy = Hierarchy.get_hierarchy(hierarchy_name)
        visits = UserPageVisit.objects.filter(user=self.user,
                                              section__hierarchy=hierarchy)

        seconds = 0
        if (visits.count() > 0):
            start = visits.order_by('first_visit')[0].first_visit
            end = visits.order_by('-last_visit')[0].last_visit
            seconds = (end - start).total_seconds() / 60
        return seconds


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        clinics = Clinic.objects.all()
        if clinics.count() < 1:
            clinic = Clinic.objects.create(name='Pilot')
        else:
            clinic = clinics[0]
        UserProfile.objects.get_or_create(user=instance, clinic=clinic)


post_save.connect(create_user_profile, sender=User)


class UserVideoView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video_id = models.CharField(max_length=256)
    video_duration = models.IntegerField(default=0)
    seconds_viewed = models.IntegerField(default=0)

    def percent_viewed(self):
        rv = float(self.seconds_viewed) / self.video_duration * 100
        return rv

    class Meta:
        unique_together = (('user', 'video_id'),)

####################
# custom pageblocks


@python_2_unicode_compatible
class QuizSummaryBlock(models.Model):
    pageblocks = GenericRelation(
        PageBlock, related_query_name="quiz_summary")
    template_file = "main/quiz_summary_block.html"
    display_name = "Quiz Summary Block"
    quiz_class = models.CharField(max_length=50)

    def pageblock(self):
        return self.pageblocks.all()[0]

    def __str__(self):
        return str(self.pageblock())

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

    def as_dict(self):
        return dict(
            quiz_class=self.quiz_class
        )

    @classmethod
    def create_from_dict(cls, d):
        return cls.objects.create(
            quiz_class=d.get('quiz_class', '')
        )


class QuizSummaryForm(forms.ModelForm):
    class Meta:
        model = QuizSummaryBlock
        exclude = []


class YouTubeReportColumn(ReportColumnInterface):
    def __init__(self, hierarchy, video_id, title, language):
        self.hierarchy = hierarchy
        self.video_id = video_id
        self.title = title
        self.language = language

    def identifier(self):
        return self.video_id

    def metadata(self):
        '''hierarchy, itemIdentifier', 'group', 'item type', 'item text' '''
        return [self.hierarchy.name, self.identifier(), 'YouTube Video',
                'percent viewed', self.title]

    def user_value(self, user):
        try:
            view = UserVideoView.objects.get(user=user,
                                             video_id=self.identifier())
            return view.percent_viewed()
        except UserVideoView.DoesNotExist:
            return 0


@python_2_unicode_compatible
class YouTubeBlock(models.Model):
    pageblocks = GenericRelation(
        PageBlock, related_query_name="user_video")
    template_file = "main/youtube_video_block.html"
    display_name = "YouTube Video"

    video_id = models.CharField(max_length=256)
    language = models.CharField(max_length=2, choices=LANGUAGES)
    title = models.TextField()

    def pageblock(self):
        return self.pageblocks.all()[0]

    def __str__(self):
        return str(self.pageblock())

    @classmethod
    def add_form(self):
        return YouTubeForm()

    def edit_form(self):
        return YouTubeForm(instance=self)

    @classmethod
    def create(self, request):
        form = YouTubeForm(request.POST)
        return form.save()

    def edit(self, vals, files):
        form = YouTubeForm(data=vals, files=files, instance=self)
        if form.is_valid():
            form.save()

    def needs_submit(self):
        return False

    def unlocked(self, user):
        return True

    def report_columns(self):
        return [YouTubeReportColumn(self.pageblock().section.hierarchy,
                                    self.video_id, self.title, self.language)]

    def report_metadata(self):
        return self.report_columns()

    def report_values(self):
        return self.report_columns()

    def as_dict(self):
        return dict(
            video_id=self.video_id,
            language=self.language,
            title=self.title
        )

    @classmethod
    def create_from_dict(cls, d):
        return cls.objects.create(
            video_id=d.get('video_id', ''),
            language=d.get('language', ''),
            title=d.get('title', '')
        )


class YouTubeForm(forms.ModelForm):
    class Meta:
        model = YouTubeBlock
        widgets = {'title': forms.TextInput}
        exclude = []


ReportableInterface.register(YouTubeBlock)


@python_2_unicode_compatible
class SimpleImageBlock(models.Model):
    pageblocks = GenericRelation(PageBlock)
    image = models.ImageField(upload_to="images")
    caption = models.TextField(blank=True)
    alt = models.CharField(max_length=100, null=True, blank=True)
    template_file = "main/simpleimageblock.html"
    display_name = "Simple Image Block"

    def pageblock(self):
        return self.pageblocks.all()[0]

    def __str__(self):
        return str(self.pageblock())

    def needs_submit(self):
        return False

    def unlocked(self, user):
        return True

    def edit_form(self):
        class EditForm(forms.Form):
            image = forms.FileField(label="replace image")
            caption = forms.CharField(initial=self.caption,
                                      widget=forms.widgets.Textarea())
            alt = forms.CharField(initial=self.alt)
        return EditForm()

    @classmethod
    def add_form(cls):
        class AddForm(forms.Form):
            image = forms.FileField(label="select image")
            caption = forms.CharField(widget=forms.widgets.Textarea())
            alt = forms.CharField()
        return AddForm()

    @classmethod
    def create(cls, request):
        if 'image' in request.FILES:
            ib = cls.objects.create(
                alt=request.POST.get('alt', ''),
                caption=request.POST.get('caption', ''),
                image="")
            ib.save_image(request.FILES['image'])
            return ib
        return None

    @classmethod
    def create_from_dict(cls, d):
        # since it's coming from a dict, not a request
        # we assume that some other part is handling the writing of
        # the image file to disk and we just get a path to it
        return cls.objects.create(
            image=d.get('image', ''),
            alt=d.get('alt', ''),
            caption=d.get('caption', ''))

    def as_dict(self):
        return dict(image=self.image.name,
                    alt=self.alt,
                    caption=self.caption)

    def edit(self, vals, files):
        self.caption = vals.get('caption', '')
        self.alt = vals.get('alt', '')
        if files and 'image' in files:
            self.save_image(files['image'])
        self.save()

    def save_image(self, f):
        ext = f.name.split(".")[-1].lower()
        basename = slugify(f.name.split(".")[-2].lower())[:20]
        if ext not in ['jpg', 'jpeg', 'gif', 'png']:
            # unsupported image format
            return None
        full_filename = "%s/%s.%s" % (
            self.image.field.upload_to, basename, ext)
        fd = self.image.storage.open(
            settings.MEDIA_ROOT + "/" + full_filename, 'wb')

        for chunk in f.chunks():
            fd.write(chunk)
        fd.close()
        self.image = full_filename
        self.save()


class MeaningfulConsentReport(PagetreeReport):

    def users(self):
        users = User.objects.filter(
            is_active=False, username__startswith=USERNAME_PREFIX)
        return users.order_by('id')

    def standalone_columns(self):
        return [
            StandaloneReportColumn(
                "participant_id", 'profile', 'string',
                'Randomized Participant Id', lambda x: x.username),
            StandaloneReportColumn(
                "english_percent_complete", 'profile', 'percent',
                '% of hierarchy completed',
                lambda x: x.profile.percent_complete_hierarchy('en')),
            StandaloneReportColumn(
                "english_last_access", 'profile', 'date string',
                'last access date',
                lambda x: x.profile.last_access_formatted('en')),
            StandaloneReportColumn(
                "english_time_spent", 'profile', 'integer',
                'minutes',
                lambda x: x.profile.time_spent('en')),
            StandaloneReportColumn(
                "spanish_percent_complete", 'profile', 'percent',
                '% of hierarchy completed',
                lambda x: x.profile.percent_complete_hierarchy('es')),
            StandaloneReportColumn(
                "spanish_last_access", 'profile', 'date string',
                'last access date',
                lambda x: x.profile.last_access_formatted('es')),
            StandaloneReportColumn(
                "spanish_time_spent", 'profile', 'integer',
                'minutes',
                lambda x: x.profile.time_spent('es'))]


##################
# django-rest interfaces

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username',)


class ParticipantSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSerializer(many=False, read_only=True)
    percent_complete = serializers.ReadOnlyField()
    last_access = serializers.ReadOnlyField()

    class Meta:
        model = UserProfile
        fields = ('user', 'percent_complete', 'notes', 'last_access')


class ParticipantViewSet(viewsets.ModelViewSet):
    model = UserProfile
    serializer_class = ParticipantSerializer

    def get_queryset(self):
        queryset = UserProfile.objects.filter(
            archived=False,
            user__username__startswith=USERNAME_PREFIX,
            user__is_active=False)

        username = self.request.query_params.get('username', None)
        if username:
            queryset = queryset.filter(user__username__startswith=username)

        return sorted(queryset, key=lambda x: x.last_access(), reverse=True)
