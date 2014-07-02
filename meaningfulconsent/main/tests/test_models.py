from django.test import TestCase
from meaningfulconsent.main.models import Clinic, UserVideoView
from meaningfulconsent.main.tests.factories import UserFactory, \
    ModuleFactory, ParticipantFactory
from pagetree.models import Hierarchy, UserPageVisit


class UserProfileTest(TestCase):

    def setUp(self):
        Clinic.objects.create(name='Test Clinic')
        self.user = UserFactory()
        self.participant = ParticipantFactory()

        ModuleFactory("en", "/pages/en/")
        ModuleFactory("es", "/pages/es/")

        self.hierarchy_en = Hierarchy.objects.get(name='en')
        self.hierarchy_es = Hierarchy.objects.get(name='es')

    def test_auto_profile_create(self):
        self.assertFalse(self.user.profile.is_participant())
        self.assertFalse(self.participant.is_active)
        self.assertTrue(self.participant.profile.is_participant())

    def test_default_location(self):
        self.assertEquals(self.user.profile.default_location(),
                          self.hierarchy_en.get_root())

        self.user.profile.language = "es"
        self.user.profile.save()
        self.assertEquals(self.user.profile.default_location(),
                          self.hierarchy_es.get_root())

    def test_last_location_no_visits(self):
        # no language
        self.assertEquals(self.user.profile.last_location(),
                          self.hierarchy_en.get_root())

        self.user.profile.language = "en"
        self.user.profile.save()

        self.assertEquals(self.user.profile.last_location().get_absolute_url(),
                          "/pages/en//")

        self.user.profile.language = "es"
        self.user.profile.save()
        self.assertEquals(self.user.profile.last_location().get_absolute_url(),
                          "/pages/es//")

    def test_last_location_with_visits(self):
        self.user.profile.language = 'en'
        self.user.profile.save()

        sections = self.hierarchy_en.get_root().get_descendants()
        UserPageVisit.objects.create(user=self.user,
                                     section=sections[0],
                                     status="complete")
        UserPageVisit.objects.create(user=self.user,
                                     section=sections[1],
                                     status="complete")
        self.assertEquals(self.user.profile.last_location().get_absolute_url(),
                          "/pages/en/one/introduction/")

        self.user.profile.language = "es"
        self.user.profile.save()
        self.assertEquals(self.user.profile.last_location().get_absolute_url(),
                          "/pages/es//")

    def test_percent_complete(self):
        self.assertEquals(self.user.profile.percent_complete(), 0)

        self.user.profile.language = 'en'
        self.user.profile.save()
        self.assertEquals(self.user.profile.percent_complete(), 0)

        sections = self.hierarchy_en.get_root().get_descendants()
        UserPageVisit.objects.create(user=self.user,
                                     section=sections[0],
                                     status="complete")
        UserPageVisit.objects.create(user=self.user,
                                     section=sections[1],
                                     status="complete")

        self.assertEquals(self.user.profile.percent_complete(), 50)

        self.user.profile.language = "es"
        self.user.profile.save()
        self.assertEquals(self.user.profile.percent_complete(), 0)


class UserVideoViewTest(TestCase):

    def setUp(self):
        Clinic.objects.create(name='Test Clinic')
        self.user = UserFactory()

    def test_percent_viewed(self):
        uvv = UserVideoView(user=self.user,
                            video_id='ABCDEFG',
                            video_duration=100)

        self.assertEquals(uvv.percent_viewed(), 0)

        uvv.seconds_viewed = 50
        self.assertEquals(uvv.percent_viewed(), 50.0)

        uvv.seconds_viewed = 200
        self.assertEquals(uvv.percent_viewed(), 200.0)
