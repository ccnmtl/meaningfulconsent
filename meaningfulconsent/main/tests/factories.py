from django.contrib.auth.models import User
from django.test.client import Client
from django.test.testcases import TestCase
from meaningfulconsent.main.auth import generate_password
from meaningfulconsent.main.models import Clinic
from pagetree.models import Hierarchy, Section
import factory
import simplejson


class ClinicFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Clinic
    name = "Test"


class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = User
    username = factory.Sequence(lambda n: "user%03d" % n)
    password = factory.PostGenerationMethodCall('set_password', 'test')


class ParticipantFactory(factory.DjangoModelFactory):
    FACTORY_FOR = User
    username = 'MC1234567'
    is_active = False
    password = factory.PostGenerationMethodCall('set_password',
                                                generate_password('MC1234567'))


class HierarchyFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Hierarchy
    name = "main"
    base_url = ""


class RootSectionFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Section
    hierarchy = factory.SubFactory(HierarchyFactory)
    label = "Root"
    slug = ""


class ModuleFactory(object):
    def __init__(self, hname, base_url):
        hierarchy = HierarchyFactory(name=hname, base_url=base_url)
        root = hierarchy.get_root()
        root.add_child_section_from_dict(
            {'label': "One", 'slug': "one",
             'children': [{'label': "Three", 'slug': "introduction"}]})
        root.add_child_section_from_dict({'label': "Two", 'slug': "two"})
        self.root = root


class ParticipantTestCase(TestCase):
    def setUp(self):
        Clinic.objects.create(name="pilot")
        self.user = UserFactory()

        self.client = Client()

        # create a "real" participant to work with
        self.client.login(username=self.user.username, password="test")
        response = self.client.post('/participant/create/',
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        the_json = simplejson.loads(response.content)
        self.participant = User.objects.get(
            username=the_json['user']['username'])
        self.client.logout()

        ModuleFactory("en", "/pages/en/")
        ModuleFactory("es", "/pages/es/")

        self.hierarchy_en = Hierarchy.objects.get(name='en')
        self.hierarchy_es = Hierarchy.objects.get(name='es')

    def login_participant(self):
        # login as facilitator
        self.assertTrue(self.client.login(
            username=self.user.username, password="test"))

        # manually login client
        response = self.client.post('/participant/login/',
                                    {'username': self.participant.username},
                                    follow=True)
        self.assertEquals(response.status_code, 200)
