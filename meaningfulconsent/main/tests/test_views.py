from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client
from meaningfulconsent.main.auth import generate_password
from meaningfulconsent.main.models import Clinic, UserVideoView
from meaningfulconsent.main.tests.factories import ParticipantTestCase
from pagetree.helpers import get_hierarchy
from pagetree.models import UserPageVisit
import json


class BasicTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_root(self):
        response = self.client.get("/")
        self.assertEquals(response.status_code, 200)

    def test_smoketest(self):
        response = self.client.get("/smoketest/")
        self.assertEquals(response.status_code, 200)
        assert "PASS" in response.content


class PagetreeViewTestsLoggedOut(TestCase):
    def setUp(self):
        self.client = Client()
        self.hierarchy = get_hierarchy("en", "/pages/en/")
        self.root = self.hierarchy.get_root()
        self.root.add_child_section_from_dict(
            {
                'label': 'Section 1',
                'slug': 'section-1',
                'pageblocks': [],
                'children': [],
            })

    def test_page(self):
        r = self.client.get("/pages/en/section-1/")
        self.assertEqual(r.status_code, 302)

    def test_edit_page(self):
        r = self.client.get("/pages/en/edit/section-1/")
        self.assertEqual(r.status_code, 302)


class PagetreeViewTestsLoggedIn(TestCase):
    def setUp(self):
        self.client = Client()
        Clinic.objects.create(name="pilot")

        self.hierarchy = get_hierarchy("en", "/pages/en/")
        self.root = self.hierarchy.get_root()
        self.root.add_child_section_from_dict(
            {
                'label': 'Section 1',
                'slug': 'section-1',
                'pageblocks': [],
                'children': [],
            })
        self.user = User.objects.create(username="testuser")
        self.user.set_password("test")
        self.user.save()

        self.client.login(username="testuser", password="test")
        self.superuser = User.objects.create(
            username="superuser", is_superuser=True)
        self.superuser.set_password("test")
        self.superuser.save()

    def test_page(self):
        r = self.client.get("/pages/en/section-1/")
        self.assertEqual(r.status_code, 200)

    def test_edit_page(self):
        self.assertTrue(self.user.is_authenticated())

        # you must be a superuser to edit pages
        r = self.client.get("/pages/en/edit/section-1/")
        self.assertEqual(r.status_code, 302)

        self.client.login(username="superuser", password="test")
        r = self.client.get("/pages/en/edit/section-1/")
        self.assertEqual(r.status_code, 200)


class ChangePasswordTest(ParticipantTestCase):

    def test_logged_out(self):
        response = self.client.get('/accounts/password_change/')
        self.assertEquals(response.status_code, 405)

    def test_facilitator(self):
        self.assertTrue(self.client.login(
            username=self.user.username, password="test"))
        response = self.client.get('/accounts/password_change/')
        self.assertEquals(response.status_code, 200)

    def test_participant(self):
        self.login_participant()
        response = self.client.get('/accounts/password_change/')
        self.assertEquals(response.status_code, 405)


class IndexViewTest(ParticipantTestCase):

    def test_anonymous_user(self):
        response = self.client.get('/')
        self.assertTrue('Log In' in response.content)
        self.assertFalse('Log Out' in response.content)
        self.assertEquals(response.template_name[0], "main/splash.html")
        self.assertEquals(response.status_code, 200)

    def test_facilitator(self):
        self.assertTrue(self.client.login(
            username=self.user.username, password="test"))
        response = self.client.get('/')
        self.assertEquals(response.template_name[0], "main/facilitator.html")
        self.assertEquals(response.status_code, 200)
        self.assertFalse('Log In' in response.content)
        self.assertTrue('Log Out' in response.content)
        self.assertTrue('Dashboard' in response.content)

    def test_participant(self):
        self.login_participant()

        response = self.client.get('/', follow=True)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.template_name[0],
                          "main/participant_language.html")

        self.participant.profile.language = 'en'
        self.participant.profile.save()
        response = self.client.get('/', follow=True)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.redirect_chain,
                          [('http://testserver/participant/language/', 302)])


class LoginTest(ParticipantTestCase):

    def test_login_get(self):
        response = self.client.get('/accounts/login/')
        self.assertEquals(response.status_code, 405)

    def test_login_post_noajax(self):
        response = self.client.post('/accounts/login/',
                                    {'username': self.user.username,
                                     'password': 'test'})
        self.assertEquals(response.status_code, 405)

    def test_login_post_ajax(self):
        response = self.client.post('/accounts/login/',
                                    {'username': '',
                                     'password': ''},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        the_json = json.loads(response.content)
        self.assertTrue(the_json['error'], True)

        response = self.client.post('/accounts/login/',
                                    {'username': self.user.username,
                                     'password': 'test'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        the_json = json.loads(response.content)
        self.assertTrue(the_json['next'], "/")
        self.assertTrue('error' not in the_json)

    def test_login_participant(self):
        # participants cannot login through the /accounts/login mechanism
        # as the backend authenticators kick out inactive Users
        pwd = generate_password(self.participant.username)
        response = self.client.post('/accounts/login/',
                                    {'username': self.participant.username,
                                     'password': pwd},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        the_json = json.loads(response.content)
        self.assertTrue(the_json['error'], True)


class LogoutTest(ParticipantTestCase):

    def test_logout_user(self):
        self.client.login(username=self.user.username, password="test")

        response = self.client.get('/accounts/logout/?next=/', follow=True)
        self.assertEquals(response.template_name[0], "main/splash.html")
        self.assertEquals(response.status_code, 200)
        self.assertTrue('Log In' in response.content)
        self.assertFalse('Log Out' in response.content)

    def test_logout_participant(self):
        self.client.login(username=self.user.username, password="test")

        response = self.client.post('/participant/login/',
                                    {'username': self.participant.username},
                                    follow=True)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.template_name[0],
                          "main/participant_language.html")

        response = self.client.get('/accounts/logout/?next=/', follow=True)
        self.assertEquals(response.template_name[0],
                          "main/participant_language.html")
        self.assertEquals(response.status_code, 200)


class CreateParticipantViewTest(ParticipantTestCase):

    def test_post_as_anonymous_user(self):
        response = self.client.post('/participant/create/',
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 405)

    def test_post_as_participant(self):
        self.client.login(username=self.participant.username, password="test")
        response = self.client.post('/participant/create/',
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 405)

    def test_post_as_facilitator(self):
        self.client.login(username=self.user.username, password="test")

        # non-ajax
        response = self.client.post('/participant/create/')
        self.assertEquals(response.status_code, 405)

        response = self.client.post('/participant/create/',
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)

        the_json = json.loads(response.content)
        user = User.objects.get(username=the_json['user']['username'])
        self.assertTrue(user.profile.is_participant())


class LoginParticipantViewTest(ParticipantTestCase):

    def test_post_as_anonymous_user(self):
        response = self.client.post('/participant/login/')
        self.assertEquals(response.status_code, 405)

    def test_post_as_participant(self):
        self.client.login(username=self.participant.username, password="test")
        response = self.client.post('/participant/login/')
        self.assertEquals(response.status_code, 405)

    def test_post_as_facilitator_first(self):
        self.client.login(username=self.user.username, password="test")

        response = self.client.post('/participant/login/',
                                    {'username': self.participant.username},
                                    follow=True,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.template_name[0],
                          "main/participant_language.html")

    def test_post_as_facilitator_second(self):
        self.client.login(username=self.user.username, password="test")
        self.participant.profile.language = 'en'
        self.participant.profile.save()

        sections = self.hierarchy_en.get_root().get_descendants()
        UserPageVisit.objects.create(user=self.participant,
                                     section=sections[0],
                                     status="complete")
        UserPageVisit.objects.create(user=self.participant,
                                     section=sections[1],
                                     status="complete")

        response = self.client.post('/participant/login/',
                                    {'username': self.participant.username},
                                    follow=True,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.templates[0].name, "pagetree/page.html")
        self.assertEquals(response.redirect_chain[0],
                          ('http://testserver/pages/en/one/introduction/',
                           302))


class LanguageParticipantViewTest(ParticipantTestCase):

    def test_post_as_anonymous_user(self):
        response = self.client.post('/participant/login/')
        self.assertEquals(response.status_code, 405)

    def test_post_as_user(self):
        self.client.login(username=self.user.username, password="test")
        self.assertEquals(self.user.profile.language, 'en')

        response = self.client.post('/participant/language/',
                                    {'language': 'es'},
                                    follow=True)
        self.assertEquals(response.redirect_chain[0],
                          ('http://testserver/pages/es//', 302))
        self.assertEquals(response.redirect_chain[1],
                          ('http://testserver/pages/es/one/', 302))

        sections = self.hierarchy_en.get_root().get_descendants()
        UserPageVisit.objects.create(user=self.user,
                                     section=sections[0],
                                     status="complete")
        UserPageVisit.objects.create(user=self.user,
                                     section=sections[1],
                                     status="complete")
        response = self.client.post('/participant/language/',
                                    {'language': 'en'},
                                    follow=True)
        self.assertEquals(response.redirect_chain[0],
                          ('http://testserver/pages/en/one/introduction/',
                           302))

    def test_post_as_participant(self):
        self.login_participant()
        self.assertEquals(self.participant.profile.language, 'en')

        response = self.client.get('/pages/en/', {}, follow=True)
        self.assertTrue('Pause' in response.content)

        response = self.client.post('/participant/language/',
                                    {'language': 'es'},
                                    follow=True)
        self.assertEquals(response.redirect_chain[0],
                          ('http://testserver/pages/es//', 302))
        self.assertEquals(response.redirect_chain[1],
                          ('http://testserver/pages/es/one/', 302))

        self.assertTrue('Pausa Tutorial' in response.content)


class ClearParticipantViewTest(ParticipantTestCase):

    def test_get_as_anonymous_user(self):
        response = self.client.get('/participant/clear/')
        self.assertEquals(response.status_code, 405)

    def test_get_as_participant(self):
        self.login_participant()
        response = self.client.get('/participant/clear/')
        self.assertEquals(response.status_code, 405)

    def test_get_as_facilitator(self):
        self.user.profile.language = 'en'
        self.user.profile.save()

        self.client.login(username=self.user.username, password="test")

        sections = self.hierarchy_en.get_root().get_descendants()
        UserPageVisit.objects.create(user=self.user,
                                     section=sections[0],
                                     status="complete")
        UserPageVisit.objects.create(user=self.user,
                                     section=sections[1],
                                     status="complete")

        self.assertEquals(self.user.profile.last_location().get_absolute_url(),
                          '/pages/en/one/introduction/')
        response = self.client.get('/participant/clear/', follow=True)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.redirect_chain[0],
                          ('http://testserver/pages/en//', 302))

        visits = UserPageVisit.objects.filter(user=self.user)
        self.assertEquals(len(visits), 1)


class TrackParticipantViewTest(ParticipantTestCase):

    def test_post_as_anonymous_user(self):
        response = self.client.post('/participant/track/',
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 302)

    def test_post_non_ajax(self):
        self.client.login(username=self.user.username, password="test")
        response = self.client.post('/participant/track/',
                                    {})
        self.assertEquals(response.status_code, 405)

    def test_post_invalid_parameters(self):
        self.client.login(username=self.user.username, password="test")

        response = self.client.post('/participant/track/',
                                    {},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        the_json = json.loads(response.content)
        self.assertFalse(the_json['success'])
        self.assertEquals(the_json['msg'], "Invalid video id")

        response = self.client.post('/participant/track/',
                                    {'video_id': 'ABCDEFG'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        the_json = json.loads(response.content)
        self.assertFalse(the_json['success'])
        self.assertEquals(the_json['msg'], "Invalid video duration")

        ctx = {
            'video_id': 'ABCDEFG',
            'video_duration': -100
        }
        response = self.client.post('/participant/track/', ctx,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        the_json = json.loads(response.content)
        self.assertFalse(the_json['success'])
        self.assertEquals(the_json['msg'], "Invalid video duration")

        ctx['video_duration'] = 0
        response = self.client.post('/participant/track/', ctx,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        the_json = json.loads(response.content)
        self.assertFalse(the_json['success'])
        self.assertEquals(the_json['msg'], "Invalid video duration")

    def test_post_success(self):
        self.client.login(username=self.user.username, password="test")

        # created
        response = self.client.post('/participant/track/',
                                    {'video_id': 'ABCDEFG',
                                     'video_duration': 100},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        the_json = json.loads(response.content)
        self.assertTrue(the_json['success'])

        uvv = UserVideoView.objects.get(user=self.user)
        self.assertEquals(uvv.video_id, 'ABCDEFG')
        self.assertEquals(uvv.video_duration, 100)
        self.assertEquals(uvv.seconds_viewed, 0)

        # updated
        response = self.client.post('/participant/track/',
                                    {'video_id': 'ABCDEFG',
                                     'video_duration': 100,
                                     'seconds_viewed': 50},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        the_json = json.loads(response.content)
        self.assertTrue(the_json['success'])

        uvv = UserVideoView.objects.get(user=self.user)
        self.assertEquals(uvv.video_id, 'ABCDEFG')
        self.assertEquals(uvv.video_duration, 100)
        self.assertEquals(uvv.seconds_viewed, 50)

    def test_post_success_as_participant(self):
        self.client.login(username=self.user.username, password="test")

        response = self.client.post('/participant/login/',
                                    {'username': self.participant.username},
                                    follow=True,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)

        response = self.client.post('/participant/track/',
                                    {'video_id': 'ABCDEFG',
                                     'video_duration': 200,
                                     'seconds_viewed': 200},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        the_json = json.loads(response.content)
        self.assertTrue(the_json['success'])

        uvv = UserVideoView.objects.get(user=self.participant)
        self.assertEquals(uvv.video_id, 'ABCDEFG')
        self.assertEquals(uvv.video_duration, 200)
        self.assertEquals(uvv.seconds_viewed, 200)


class ArchiveParticipantViewTest(ParticipantTestCase):

    def test_post_as_non_ajax(self):
        self.client.login(username=self.user.username, password="test")
        response = self.client.post('/participant/archive/')
        self.assertEquals(response.status_code, 405)

    def test_post_as_anonymous_user(self):
        response = self.client.post('/participant/archive/', {},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 405)

    def test_post_as_participant(self):
        self.login_participant()
        response = self.client.post('/participant/archive/', {},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 405)

    def test_post_as_facilitator_invalidparams(self):
        self.client.login(username=self.user.username, password="test")
        response = self.client.post('/participant/archive/', {},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 404)

        response = self.client.post('/participant/archive/',
                                    {'username': 'foo'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 404)

    def test_post_as_facilitator_success(self):
        self.assertFalse(self.participant.profile.archived)

        self.client.login(username=self.user.username, password="test")

        response = self.client.post('/participant/archive/',
                                    {'username': self.participant.username},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)

        user = User.objects.get(username=self.participant.username)
        self.assertTrue(user.profile.archived)


class ParticipantNoteViewTest(ParticipantTestCase):

    def test_post_as_non_ajax(self):
        self.client.login(username=self.user.username, password="test")
        response = self.client.post('/participant/note/')
        self.assertEquals(response.status_code, 405)

    def test_post_as_anonymous_user(self):
        response = self.client.post('/participant/note/', {},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 405)

    def test_post_as_participant(self):
        self.login_participant()
        response = self.client.post('/participant/note/', {},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 405)

    def test_post_as_facilitator_invalidparams(self):
        self.client.login(username=self.user.username, password="test")
        response = self.client.post('/participant/note/', {},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 404)

        response = self.client.post('/participant/note/',
                                    {'username': 'foo'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 404)

    def test_post_as_facilitator_success(self):
        self.assertFalse(self.participant.profile.archived)

        self.client.login(username=self.user.username, password="test")

        response = self.client.post('/participant/note/',
                                    {'username': self.participant.username,
                                     'notes': 'foo bar baz'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)

        user = User.objects.get(username=self.participant.username)
        self.assertEquals(user.profile.notes, 'foo bar baz')
