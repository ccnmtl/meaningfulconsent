from django.conf import settings
from django.contrib.auth.models import User
from meaningfulconsent.main.models import USERNAME_PREFIX, USERNAME_LENGTH
import base64
import hashlib
import hmac
import re


def generate_random_username():
    random_number = User.objects.make_random_password(
        length=7, allowed_chars='123456789')

    while User.objects.filter(username=random_number):
        random_number = User.objects.make_random_password(
            length=7, allowed_chars='123456789')

    return "%s%s" % (USERNAME_PREFIX, random_number)


def generate_password(username):
    digest = hmac.new(settings.PARTICIPANT_SECRET,
                      msg=username, digestmod=hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


class ParticipantBackend(object):

    def match(self, username):
        pattern = 'MC\d{7}'
        prog = re.compile(pattern)
        result = prog.match(username)

        return (result is not None and
                result.start() == 0 and
                result.end() == USERNAME_LENGTH and
                len(username) == USERNAME_LENGTH)

    def authenticate(self, username=None, password=None):
        try:
            if self.match(username):
                user = User.objects.get(username=username)
                if not user.is_active:
                    if user.check_password(password):
                        return user
        except User.DoesNotExist:
            pass  # just return None below

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
