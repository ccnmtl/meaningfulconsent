from django.contrib.auth.models import User
from django.test import TestCase
from meaningfulconsent.main.auth import ParticipantBackend, \
    generate_random_username, generate_password


class ParticipantAuthTest(TestCase):

    def setUp(self):
        self.backend = ParticipantBackend()

    def test_match(self):
        self.assertFalse(self.backend.match(''))
        self.assertFalse(self.backend.match('foo'))
        self.assertFalse(self.backend.match('MC'))
        self.assertFalse(self.backend.match('123456789'))
        self.assertFalse(self.backend.match('MC123'))
        self.assertFalse(self.backend.match('MC123456789'))
        self.assertTrue(self.backend.match('MC1234567'))

    def test_generate_random_username(self):
        username = generate_random_username()
        self.assertTrue(self.backend.match(username))

    def test_authenticate_invalid_username(self):
        self.assertEquals(self.backend.authenticate("foobar"), None)

    def test_authenticate_user_does_not_exist(self):
        self.assertEquals(self.backend.authenticate("MC1234567"), None)

    def test_authenticate_user_is_active(self):
        user = User.objects.create(username='MC1234567')
        user.set_password('test')
        user.save()
        self.assertEquals(self.backend.authenticate("MC1234567"), None)

    def test_authenticate_user_invalid_password(self):
        user = User.objects.create(username='MC1234567', is_active=False)
        user.set_password('test')
        user.save()

        self.assertEquals(self.backend.authenticate("MC1234567"), None)

    def test_authenticate_user_success(self):
        unm = generate_random_username()
        pwd = generate_password(unm)

        user = User(username=unm, is_active=False)
        user.set_password(pwd)
        user.save()

        self.assertEquals(self.backend.authenticate(username=unm), user)

    def test_get_user(self):
        unm = generate_random_username()
        pwd = generate_password(unm)
        user = User.objects.create(username=unm, password=pwd, is_active=False)

        self.assertIsNone(self.backend.get_user(1234))
        self.assertEquals(self.backend.get_user(user.id), user)
