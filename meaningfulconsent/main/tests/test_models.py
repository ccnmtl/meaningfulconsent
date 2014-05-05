from django.test import TestCase
from meaningfulconsent.main.tests.factories import UserFactory, \
    UserProfileFactory, ModuleFactory
from pagetree.models import Hierarchy, UserPageVisit


class UserProfileTest(TestCase):

    def setUp(self):
        self.user = UserFactory()
        UserProfileFactory(user=self.user,
                           language='en',
                           is_participant=False)

        ModuleFactory("en", "/pages/en/")
        ModuleFactory("es", "/pages/es/")

        self.hierarchy_en = Hierarchy.objects.get(name='en')
        self.hierarchy_es = Hierarchy.objects.get(name='es')

    def test_default_location(self):
        self.assertEquals(self.user.profile.default_location(),
                          self.hierarchy_en.get_root())

        self.user.profile.language = "es"
        self.user.profile.save()
        self.assertEquals(self.user.profile.default_location(),
                          self.hierarchy_es.get_root())

    def test_last_location_no_visits(self):
        self.assertEquals(self.user.profile.last_location().get_absolute_url(),
                          "/pages/en//")

        self.user.profile.language = "es"
        self.user.profile.save()
        self.assertEquals(self.user.profile.last_location().get_absolute_url(),
                          "/pages/es//")

    def test_last_location_with_visits(self):
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
