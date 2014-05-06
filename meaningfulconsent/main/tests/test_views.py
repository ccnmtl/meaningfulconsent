from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client
from meaningfulconsent.main.models import Clinic, UserProfile
from meaningfulconsent.main.tests.factories import UserFactory, \
    UserProfileFactory, ModuleFactory
from pagetree.helpers import get_hierarchy
from pagetree.models import Hierarchy, UserPageVisit
import simplejson


class BasicTest(TestCase):
    def setUp(self):
        self.c = Client()

    def test_root(self):
        response = self.c.get("/")
        self.assertEquals(response.status_code, 200)

    def test_smoketest(self):
        response = self.c.get("/smoketest/")
        self.assertEquals(response.status_code, 200)
        assert "PASS" in response.content


class PagetreeViewTestsLoggedOut(TestCase):
    def setUp(self):
        self.c = Client()
        self.h = get_hierarchy("en", "/pages/en/")
        self.root = self.h.get_root()
        self.root.add_child_section_from_dict(
            {
                'label': 'Section 1',
                'slug': 'section-1',
                'pageblocks': [],
                'children': [],
            })

    def test_page(self):
        r = self.c.get("/pages/en/section-1/")
        self.assertEqual(r.status_code, 302)

    def test_edit_page(self):
        r = self.c.get("/pages/en/edit/section-1/")
        self.assertEqual(r.status_code, 302)


class PagetreeViewTestsLoggedIn(TestCase):
    def setUp(self):
        self.c = Client()
        self.h = get_hierarchy("en", "/pages/en/")
        self.root = self.h.get_root()
        self.root.add_child_section_from_dict(
            {
                'label': 'Section 1',
                'slug': 'section-1',
                'pageblocks': [],
                'children': [],
            })
        self.u = User.objects.create(username="testuser")
        self.u.set_password("test")
        self.u.save()

        self.c.login(username="testuser", password="test")
        self.su = User.objects.create(username="superuser", is_superuser=True)
        self.su.set_password("test")
        self.su.save()

        clinic = Clinic.objects.create(name="pilot")
        UserProfile.objects.create(user=self.u, clinic=clinic)
        UserProfile.objects.create(user=self.su,
                                   is_participant=False, clinic=clinic)

    def test_page(self):
        r = self.c.get("/pages/en/section-1/")
        self.assertEqual(r.status_code, 200)

    def test_edit_page(self):
        self.assertTrue(self.u.is_authenticated())

        # you must be a superuser to edit pages
        r = self.c.get("/pages/en/edit/section-1/")
        self.assertEqual(r.status_code, 302)

        self.c.login(username="superuser", password="test")
        r = self.c.get("/pages/en/edit/section-1/")
        self.assertEqual(r.status_code, 200)


class IndexViewTest(TestCase):

    def setUp(self):
        self.user = UserFactory()
        UserProfileFactory(user=self.user, language='en', is_participant=False)

        self.participant = UserFactory()
        UserProfileFactory(user=self.participant, language='en')

        self.c = Client()

    def test_anonymous_user(self):
        response = self.c.get('/')
        self.assertTrue('Log in' in response.content)
        self.assertFalse('log out' in response.content)
        self.assertEquals(response.template_name[0], "main/index.html")
        self.assertEquals(response.status_code, 200)

    def test_facilitator(self):
        self.assertTrue(self.c.login(
            username=self.user.username, password="test"))
        response = self.c.get('/')
        self.assertEquals(response.template_name[0], "main/index.html")
        self.assertEquals(response.status_code, 200)
        self.assertFalse('Log in' in response.content)
        self.assertTrue('log out' in response.content)
        self.assertTrue('Dashboard' in response.content)

    def test_participant(self):
        self.assertTrue(self.c.login(
            username=self.participant.username, password="test"))
        response = self.c.get('/')
        self.assertEquals(response.template_name[0], "main/index.html")
        self.assertEquals(response.status_code, 200)
        self.assertTrue('Return to tutorial' in response.content)
        self.assertFalse('Log in' in response.content)
        self.assertFalse('log out' in response.content)


class LogoutTest(TestCase):

    def setUp(self):
        self.user = UserFactory()
        UserProfileFactory(user=self.user, language='en', is_participant=False)

        self.participant = UserFactory()
        UserProfileFactory(user=self.participant, language='en')

        self.c = Client()

    def test_logout_user(self):
        self.c.login(username=self.user.username, password="test")

        response = self.c.get('/accounts/logout/?next=/', follow=True)
        self.assertEquals(response.template_name[0], "main/index.html")
        self.assertEquals(response.status_code, 200)
        self.assertTrue('Log in' in response.content)
        self.assertFalse('log out' in response.content)

    def test_logout_particpant(self):
        self.c.login(username=self.participant.username, password="test")

        response = self.c.get('/accounts/logout/?next=/', follow=True)
        self.assertEquals(response.template_name[0], "main/index.html")
        self.assertEquals(response.status_code, 200)
        self.assertTrue('Return to tutorial' in response.content)
        self.assertFalse('Log in' in response.content)
        self.assertFalse('log out' in response.content)


class CreateParticipantViewTest(TestCase):

    def setUp(self):
        self.user = UserFactory()
        UserProfileFactory(user=self.user, language='en', is_participant=False)

        self.participant = UserFactory(username='MC1234567')
        UserProfileFactory(user=self.participant, language='en')

        self.c = Client()

    def test_post_as_anonymous_user(self):
        response = self.c.post('/participant/create/')
        self.assertEquals(response.status_code, 403)

    def test_post_as_participant(self):
        self.c.login(username=self.participant.username, password="test")
        response = self.c.post('/participant/create/')
        self.assertEquals(response.status_code, 403)

    def test_post_as_facilitator(self):
        self.c.login(username=self.user.username, password="test")

        response = self.c.post('/participant/create/')
        self.assertEquals(response.status_code, 200)

        the_json = simplejson.loads(response.content)
        user = User.objects.get(username=the_json['user']['username'])
        self.assertTrue(user.profile.is_participant)


class LoginParticipantViewTest(TestCase):

    def setUp(self):
        self.user = UserFactory()
        UserProfileFactory(user=self.user, language='en', is_participant=False)

        self.c = Client()

        # create a "real" participant to work with
        self.c.login(username=self.user.username, password="test")
        response = self.c.post('/participant/create/')
        the_json = simplejson.loads(response.content)
        self.participant = User.objects.get(
            username=the_json['user']['username'])
        self.c.logout()

        ModuleFactory("en", "/pages/en/")
        ModuleFactory("es", "/pages/es/")

        self.hierarchy_en = Hierarchy.objects.get(name='en')
        self.hierarchy_es = Hierarchy.objects.get(name='es')

    def test_post_as_anonymous_user(self):
        response = self.c.post('/participant/login/')
        self.assertEquals(response.status_code, 403)

    def test_post_as_participant(self):
        self.c.login(username=self.participant.username, password="test")
        response = self.c.post('/participant/login/')
        self.assertEquals(response.status_code, 403)

    def test_post_as_facilitator_first(self):
        self.c.login(username=self.user.username, password="test")

        response = self.c.post('/participant/login/',
                               {'username': self.participant.username},
                               follow=True)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.template_name[0], "main/language.html")

    def test_post_as_facilitator_second(self):
        self.c.login(username=self.user.username, password="test")

        sections = self.hierarchy_en.get_root().get_descendants()
        UserPageVisit.objects.create(user=self.participant,
                                     section=sections[0],
                                     status="complete")
        UserPageVisit.objects.create(user=self.participant,
                                     section=sections[1],
                                     status="complete")

        response = self.c.post('/participant/login/',
                               {'username': self.participant.username},
                               follow=True)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.templates[0].name, "main/page.html")
        self.assertEquals(response.redirect_chain[0],
                          ('http://testserver/pages/en/one/introduction/',
                           302))


class LanguageParticipantViewTest(TestCase):

    def setUp(self):
        self.user = UserFactory()
        UserProfileFactory(user=self.user, language='en', is_participant=False)

        self.c = Client()

        ModuleFactory("en", "/pages/en/")
        ModuleFactory("es", "/pages/es/")

        self.hierarchy_en = Hierarchy.objects.get(name='en')
        self.hierarchy_es = Hierarchy.objects.get(name='es')

    def test_post_as_anonymous_user(self):
        response = self.c.post('/participant/login/')
        self.assertEquals(response.status_code, 403)

    def test_post_as_user(self):
        self.c.login(username=self.user.username, password="test")

        self.assertEquals(self.user.profile.language, 'en')

        response = self.c.post('/participant/language/',
                               {'language': 'es'},
                               follow=True)
        self.assertEquals(response.redirect_chain[0],
                          ('http://testserver/pages/es//', 302))

        sections = self.hierarchy_en.get_root().get_descendants()
        UserPageVisit.objects.create(user=self.user,
                                     section=sections[0],
                                     status="complete")
        UserPageVisit.objects.create(user=self.user,
                                     section=sections[1],
                                     status="complete")
        response = self.c.post('/participant/language/',
                               {'language': 'en'},
                               follow=True)
        self.assertEquals(response.redirect_chain[0],
                          ('http://testserver/pages/en/one/introduction/',
                           302))


class ClearParticipantViewTest(TestCase):

    def setUp(self):
        self.user = UserFactory()
        UserProfileFactory(user=self.user, language='en', is_participant=False)

        self.participant = UserFactory(username='MC1234567')
        UserProfileFactory(user=self.participant, language='en')

        self.c = Client()
        ModuleFactory("en", "/pages/en/")
        ModuleFactory("es", "/pages/es/")

        self.hierarchy_en = Hierarchy.objects.get(name='en')
        self.hierarchy_es = Hierarchy.objects.get(name='es')

    def test_get_as_anonymous_user(self):
        response = self.c.get('/participant/clear/')
        self.assertEquals(response.status_code, 403)

    def test_get_as_participant(self):
        self.c.login(username=self.participant.username, password="test")
        response = self.c.get('/participant/clear/')
        self.assertEquals(response.status_code, 403)

    def test_get_as_facilitator(self):
        self.c.login(username=self.user.username, password="test")

        sections = self.hierarchy_en.get_root().get_descendants()
        UserPageVisit.objects.create(user=self.user,
                                     section=sections[0],
                                     status="complete")
        UserPageVisit.objects.create(user=self.user,
                                     section=sections[1],
                                     status="complete")

        self.assertEquals(self.user.profile.last_location().get_absolute_url(),
                          '/pages/en/one/introduction/')
        response = self.c.get('/participant/clear/', follow=True)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.redirect_chain[0],
                          ('http://testserver/pages/en//', 302))

        visits = UserPageVisit.objects.filter(user=self.user)
        self.assertEquals(len(visits), 1)
