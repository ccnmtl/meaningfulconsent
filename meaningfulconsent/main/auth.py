from django.contrib.auth.models import User
import re
import hmac
import hashlib
import base64
from django.conf import settings

USERNAME_LENGTH = 9
USERNAME_PREFIX = 'MC'


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

    def authenticate(self, username=None):
        pattern = 'MC\d{7}'
        prog = re.compile(pattern)
        result = prog.match(username)

        if (result is None or
                result.start() != 0 and result.end() != USERNAME_LENGTH):
            return None

        try:
            user = User.objects.get(username=username)
            password = generate_password(username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
