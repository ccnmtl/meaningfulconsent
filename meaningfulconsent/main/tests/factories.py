from django.contrib.auth.models import User
from meaningfulconsent.main.auth import generate_password
from meaningfulconsent.main.models import Clinic
from pagetree.models import Hierarchy, Section
import factory


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
