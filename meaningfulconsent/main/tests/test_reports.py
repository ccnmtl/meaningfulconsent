from meaningfulconsent.main.models import MeaningfulConsentReport, \
    YouTubeBlock, YouTubeReportColumn, UserVideoView
from meaningfulconsent.main.tests.factories import ParticipantTestCase
from pagetree.models import UserPageVisit


class YouTubeReportColumnTest(ParticipantTestCase):

    def setUp(self):
        super(YouTubeReportColumnTest, self).setUp()

        self.column = YouTubeReportColumn(self.hierarchy_en, 'avideo',
                                          'atitle', 'en')

    def test_identifier(self):
        self.assertEquals(self.column.identifier(), "avideo")

    def test_metadata(self):
        keys = ['en', 'avideo', 'YouTube Video',
                'percent viewed', 'atitle']
        self.assertEquals(self.column.metadata(), keys)

    def test_user_value(self):
        self.assertEquals(self.column.user_value(self.user), 0)

        view = UserVideoView.objects.create(user=self.user,
                                            video_id='avideo',
                                            video_duration=200)
        self.assertEquals(self.column.user_value(self.user), 0)

        view.seconds_viewed = 100
        view.save()
        self.assertEquals(self.column.user_value(self.user), 50)


class MeaningfulConsentReportTest(ParticipantTestCase):

    def setUp(self):
        super(MeaningfulConsentReportTest, self).setUp()

        self.participant2 = self.create_participant()

        block = YouTubeBlock()
        block.video_id = 'avideo'
        block.language = 'en'
        block.title = 'Title'
        block.save()

        section = self.hierarchy_en.get_root().get_next()
        section.append_pageblock('Video 1', '', content_object=block)

        sections = self.hierarchy_en.get_root().get_descendants()
        UserPageVisit.objects.create(user=self.participant,
                                     section=sections[0],
                                     status="complete")
        UserPageVisit.objects.create(user=self.participant,
                                     section=sections[1],
                                     status="complete")

        UserVideoView.objects.create(user=self.participant,
                                     video_id='avideo',
                                     seconds_viewed=50,
                                     video_duration=200)

        self.report = MeaningfulConsentReport()

    def test_get_users(self):
        self.assertEquals(len(self.report.users()), 2)

    def test_metadata(self):
        rows = self.report.metadata([self.hierarchy_en])

        header = ['hierarchy', 'itemIdentifier', 'exercise type',
                  'itemType', 'itemText', 'answerIdentifier',
                  'answerText']
        self.assertEquals(rows.next(), header)

        self.assertEquals(rows.next(), "")

        # participant id
        self.assertEquals(rows.next(), ['', 'participant_id', 'profile',
                                        'string', 'Randomized Participant Id'])

        # en percent complete
        self.assertEquals(rows.next(), ['', 'english_percent_complete',
                                        'profile',
                                        'percent', '% of hierarchy completed'])

        # en last access
        self.assertEquals(rows.next(), ['', 'english_last_access',
                                        'profile', 'date string',
                                        'last access date'])

        # en time spent
        self.assertEquals(rows.next(), ['', 'english_time_spent',
                                        'profile', 'integer', 'minutes'])

        # es percent complete
        self.assertEquals(rows.next(), ['', 'spanish_percent_complete',
                                        'profile',
                                        'percent', '% of hierarchy completed'])

        # es last access
        self.assertEquals(rows.next(), ['', 'spanish_last_access',
                                        'profile', 'date string',
                                        'last access date'])

        # es time spent
        self.assertEquals(rows.next(), ['', 'spanish_time_spent',
                                        'profile', 'integer', 'minutes'])

        youtube_metadata = [u'en', u'avideo', 'YouTube Video',
                            'percent viewed', u'Title']
        self.assertEquals(rows.next(), youtube_metadata)

        try:
            rows.next()
        except StopIteration:
            pass  # expected

    def test_values(self):
        rows = self.report.values([self.hierarchy_en])
        header = ['participant_id',
                  'english_percent_complete', 'english_last_access',
                  'english_time_spent',
                  'spanish_percent_complete', 'spanish_last_access',
                  'spanish_time_spent',
                  'avideo']
        self.assertEquals(rows.next(), header)

        row = rows.next()
        self.assertEquals(row[0], self.participant.username)
        self.assertEquals(row[1], 50)
        self.assertIsNotNone(row[2])
        self.assertTrue(row[3] > 0)
        self.assertEquals(row[4], 0)
        self.assertIsNotNone(row[5])
        self.assertEquals(row[6], 0)
        self.assertEquals(row[7], 25.0)

        row = rows.next()
        self.assertEquals(row[0], self.participant2.username)
        self.assertEquals(row[1], 0)
        self.assertEquals(row[2], '')
        self.assertEquals(row[3], 0)
        self.assertEquals(row[4], 0)
        self.assertEquals(row[5], '')
        self.assertEquals(row[6], 0)
        self.assertEquals(row[7], 0)

        try:
            rows.next()
        except StopIteration:
            pass  # expected
