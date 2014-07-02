from django.contrib.auth.models import User
from django.test.client import Client
from django.test.testcases import TestCase
from meaningfulconsent.main.auth import generate_password
from meaningfulconsent.main.models import Clinic
from pagetree.models import Hierarchy
from pagetree.tests.factories import UserFactory, ModuleFactory
import factory
import simplejson


class ClinicFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Clinic


class ParticipantFactory(factory.DjangoModelFactory):
    FACTORY_FOR = User
    username = 'MC1234567'
    is_active = False
    password = factory.PostGenerationMethodCall('set_password',
                                                generate_password('MC1234567'))


class ParticipantTestCase(TestCase):
    def setUp(self):
        super(ParticipantTestCase, self).setUp()

        self.clinic = Clinic.objects.create(name="pilot")
        self.user = UserFactory()

        self.client = Client()
        self.participant = self.create_participant()

        ModuleFactory("en", "/pages/en/")
        ModuleFactory("es", "/pages/es/")

        self.hierarchy_en = Hierarchy.objects.get(name='en')
        self.hierarchy_es = Hierarchy.objects.get(name='es')

    def create_participant(self):
        # create a "real" participant to work with
        self.client.login(username=self.user.username, password="test")
        response = self.client.post('/participant/create/',
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        the_json = simplejson.loads(response.content)
        participant = User.objects.get(username=the_json['user']['username'])
        self.client.logout()
        return participant

    def login_participant(self):
        # login as facilitator
        self.assertTrue(self.client.login(
            username=self.user.username, password="test"))

        # manually login client
        response = self.client.post('/participant/login/',
                                    {'username': self.participant.username},
                                    follow=True)
        self.assertEquals(response.status_code, 200)


class PagetreeTestCase(TestCase):
    def setUp(self):
        super(PagetreeTestCase, self).setUp()

        ModuleFactory("en", "/pages/en/")
        ModuleFactory("es", "/pages/es/")

        self.hierarchy_en = Hierarchy.objects.get(name='en')
        self.hierarchy_es = Hierarchy.objects.get(name='es')
