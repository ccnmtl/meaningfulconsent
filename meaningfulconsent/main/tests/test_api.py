from meaningfulconsent.main.tests.factories import ParticipantTestCase
import json


class ParticipantApiTest(ParticipantTestCase):

    def test_post_as_anonymous_user(self):
        response = self.client.get('/api/participants/',
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 403)

    def test_post_as_participant(self):
        self.login_participant()
        response = self.client.get('/api/participants/',
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 403)

    def test_post_as_non_ajax(self):
        self.client.login(username=self.user.username, password="test")
        response = self.client.get('/api/participants/')
        self.assertEquals(response.status_code, 403)

    def test_post_as_facilitator(self):
        self.client.login(username=self.user.username, password="test")
        response = self.client.get('/api/participants/',
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        the_json = json.loads(response.content)
        self.assertEquals(the_json['count'], 1)

        participants = the_json['results']
        self.assertEquals(len(participants), 1)
        self.assertEquals(participants[0]['percent_complete'], 0)
        self.assertEquals(participants[0]['user']['username'],
                          self.participant.username)
