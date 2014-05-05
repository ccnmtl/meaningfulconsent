from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client
from meaningfulconsent.main.models import Clinic, UserProfile
from meaningfulconsent.main.tests.factories import UserFactory, \
    UserProfileFactory
from pagetree.helpers import get_hierarchy
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
