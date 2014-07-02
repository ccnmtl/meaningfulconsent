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
        idx = 0
        for row in self.report.metadata([self.hierarchy_en]):
            if idx == 0:
                header = ['hierarchy', 'itemIdentifier', 'exercise type',
                          'itemType', 'itemText', 'answerIdentifier',
                          'answerText']
                self.assertEquals(row, header)
            elif idx == 1:
                self.assertEquals(row, "")
            elif idx == 2:
                # participant id
                self.assertEquals(row, ['', 'participant_id', 'profile',
                                        'string', 'Randomized Participant Id'])
            elif idx == 3:
                # en percent complete
                self.assertEquals(row, ['', 'english_percent_complete',
                                        'profile',
                                        'percent', '% of hierarchy completed'])
            elif idx == 4:
                # e2 percent complete
                self.assertEquals(row, ['', 'spanish_percent_complete',
                                        'profile',
                                        'percent', '% of hierarchy completed'])
            elif idx == 5:
                youtube_metadata = [u'en', u'avideo', 'YouTube Video',
                                    'percent viewed', u'Title']
                self.assertEquals(row, youtube_metadata)
            else:
                self.assertTrue(idx < 6, "too many rows")
            idx += 1

    def test_values(self):
        idx = 0
        for row in self.report.values([self.hierarchy_en]):
            if idx == 0:
                header = ['participant_id', 'english_percent_complete',
                          'spanish_percent_complete', 'avideo']
                self.assertEquals(row, header)
            elif idx == 1:
                self.assertEquals(row,
                                  [self.participant.username, 50, 0, 25.0])
            elif idx == 2:
                self.assertEquals(row, [self.participant2.username, 0, 0, 0])
            elif idx == 3:
                self.assertTrue(idx < 3, "too many rows")
            idx += 1
