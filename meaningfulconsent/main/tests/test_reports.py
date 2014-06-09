from django.test.testcases import TestCase
from meaningfulconsent.main.models import YouTubeBlock, UserVideoView
from meaningfulconsent.main.reports import VideoViewColumn, \
    PagetreeReportColumn, MeaningfulConsentReport, clean_header, \
    QuestionColumn, PagetreeReport
from meaningfulconsent.main.tests.factories import ParticipantTestCase, \
    UserFactory, ClinicFactory
from pagetree.models import UserPageVisit
from quizblock.models import Quiz, Question, Answer, Submission, Response


class CleanHeaderTestCase(TestCase):

    def test_empty(self):
        self.assertEqual(clean_header(''), '')

    def test_markup(self):
        self.assertEqual(clean_header('<<<<foo>>>>'), 'foo')


class PagetreeReportColumnTest(ParticipantTestCase):

    def setUp(self):
        super(PagetreeReportColumnTest, self).setUp()

        self.column = PagetreeReportColumn(self.hierarchy_en,
                                           "username", 'profile',
                                           'string', 'Username',
                                           lambda x: x.username)

    def test_identifier(self):
        self.assertEquals(self.column.identifier(),
                          "%s_username" % self.hierarchy_en.id)

    def test_key_row(self):
        key_row = ['%s_username' % self.hierarchy_en.id,
                   'en', 'profile', 'string', 'Username']
        self.assertEquals(self.column.key_row(), key_row)

    def test_user_value(self):
        user = UserFactory()
        self.assertEquals(self.column.user_value(user), user.username)


class QuestionColumnTest(ParticipantTestCase):

    def setUp(self):
        super(QuestionColumnTest, self).setUp()

        quiz = Quiz()
        quiz.save()

        self.section = self.hierarchy_en.get_root().get_next()
        self.section.append_pageblock('Quiz', '', content_object=quiz)

        self.user = UserFactory()
        self.user2 = UserFactory()

        self.single_answer = Question.objects.create(
            quiz=quiz, text='single answer', question_type='single choice')
        self.single_answer_one = Answer.objects.create(
            question=self.single_answer, label="Yes", value="1")
        self.single_answer_two = Answer.objects.create(
            question=self.single_answer, label="No", value="0")

        self.multiple_answer = Question.objects.create(
            quiz=quiz, text='multiple answer', question_type='multiple choice')
        self.multiple_answer_one = Answer.objects.create(
            question=self.multiple_answer, label="Yes", value="1")
        self.multiple_answer_two = Answer.objects.create(
            question=self.multiple_answer, label="No", value="0")

        self.short_text = Question.objects.create(
            quiz=quiz, text='short text', question_type='short text')

        self.long_text = Question.objects.create(
            quiz=quiz, text='long text', question_type='long text')

        self.submission = Submission.objects.create(quiz=quiz, user=self.user)

    def test_single_answer(self):
        Response.objects.create(submission=self.submission,
                                question=self.single_answer,
                                value='0')

        column = QuestionColumn(self.hierarchy_en, self.single_answer)

        # identifier
        identifier = '%s_%s' % (self.hierarchy_en.id, self.single_answer.id)
        self.assertEquals(column.identifier(), identifier)

        # key row
        key_row = [identifier, 'en', 'Quiz', 'single choice', 'single answer']
        self.assertEquals(column.key_row(), key_row)

        # user value
        answer = self.single_answer.answer_set.get(value='0')
        self.assertEquals(column.user_value(self.user), answer.id)
        self.assertEquals(column.user_value(self.user2), '')

    def test_multiple_answer(self):
        Response.objects.create(submission=self.submission,
                                question=self.multiple_answer, value='0')
        Response.objects.create(submission=self.submission,
                                question=self.multiple_answer, value='1')

        a = self.multiple_answer.answer_set.get(value='1')
        column = QuestionColumn(self.hierarchy_en, self.multiple_answer, a)

        # identifier
        identifier = '%s_%s_%s' % (
            self.hierarchy_en.id, self.multiple_answer.id, a.id)
        self.assertEquals(column.identifier(), identifier)

        # key row
        identifier = "%s_%s" % (self.hierarchy_en.id, self.multiple_answer.id)
        key_row = [identifier, 'en', 'Quiz', 'multiple choice',
                   'multiple answer', a.id, a.label]
        self.assertEquals(column.key_row(), key_row)

        # user value
        self.assertEquals(column.user_value(self.user), a.id)
        self.assertEquals(column.user_value(self.user2), '')

    def test_short_text(self):
        Response.objects.create(submission=self.submission,
                                question=self.short_text, value='yes')

        column = QuestionColumn(self.hierarchy_en, self.short_text)

        # identifier
        identifier = "%s_%s" % (self.hierarchy_en.id, self.short_text.id)
        self.assertEquals(column.identifier(), identifier)

        # key row
        key_row = [identifier, 'en', 'Quiz', 'short text', 'short text']
        self.assertEquals(column.key_row(), key_row)

        # user value
        self.assertEquals(column.user_value(self.user), 'yes')

    def test_long_text(self):
        Response.objects.create(submission=self.submission,
                                question=self.long_text,
                                value='a longer response')

        column = QuestionColumn(self.hierarchy_en, self.long_text)

        # identifier
        identifier = "%s_%s" % (self.hierarchy_en.id, self.long_text.id)
        self.assertEquals(column.identifier(), identifier)

        # key row
        key_row = [identifier, 'en', 'Quiz', 'long text', 'long text']
        self.assertEquals(column.key_row(), key_row)

        # user value
        self.assertEquals(column.user_value(self.user), 'a longer response')

    def test_all(self):
        columns = QuestionColumn.all(self.hierarchy_en, self.section, True)
        self.assertEquals(len(columns), 6)
        self.assertEquals(columns[0].question, self.single_answer)
        self.assertEquals(columns[0].answer, self.single_answer_one)

        self.assertEquals(columns[1].question, self.single_answer)
        self.assertEquals(columns[1].answer, self.single_answer_two)

        self.assertEquals(columns[2].question, self.multiple_answer)
        self.assertEquals(columns[2].answer, self.multiple_answer_one)

        self.assertEquals(columns[3].question, self.multiple_answer)
        self.assertEquals(columns[3].answer, self.multiple_answer_two)

        self.assertEquals(columns[4].question, self.short_text)

        self.assertEquals(columns[5].question, self.long_text)

        columns = QuestionColumn.all(self.hierarchy_en, self.section, False)
        self.assertEquals(len(columns), 5)

        self.assertEquals(columns[0].question, self.single_answer)
        self.assertIsNone(columns[0].answer)

        self.assertEquals(columns[1].question, self.multiple_answer)
        self.assertEquals(columns[1].answer, self.multiple_answer_one)

        self.assertEquals(columns[2].question, self.multiple_answer)
        self.assertEquals(columns[2].answer, self.multiple_answer_two)

        self.assertEquals(columns[3].question, self.short_text)

        self.assertEquals(columns[4].question, self.long_text)


class PagetreeReportTest(ParticipantTestCase):

    def setUp(self):
        super(PagetreeReportTest, self).setUp()
        self.report = PagetreeReport(prefix='test')

    def test_report_creation(self):
        self.assertEquals(self.report.report_prefix, 'test')


class VideoViewColumnTest(ParticipantTestCase):

    def setUp(self):
        super(VideoViewColumnTest, self).setUp()

        block = YouTubeBlock()
        block.video_id = 'FOOBAR'
        block.language = 'en'
        block.title = "Title"
        block.save()

        block2 = YouTubeBlock()
        block2.video_id = 'BARBAZ'
        block2.language = 'es'
        block2.title = "Title2"
        block2.save()

        section = self.hierarchy_en.get_root()
        section.append_pageblock("Video 1", '', content_object=block)
        section.append_pageblock("Video 2", '', content_object=block2)

        uvv = UserVideoView(user=self.participant,
                            video_id='FOOBAR',
                            video_duration=100,
                            seconds_viewed=50)
        uvv.save()

    def test_identifier(self):
        column = VideoViewColumn(self.hierarchy_en, 'FOOBAR', 'Title', 'en')
        self.assertEquals(column.identifier(), 'FOOBAR')

    def test_key_row(self):
        column = VideoViewColumn(self.hierarchy_en, 'FOOBAR', 'Title', 'en')

        key_row = ['FOOBAR', 'en', 'YouTube Video',
                   'percent viewed', 'Title in en']
        self.assertEquals(column.key_row(), key_row)

    def test_user_value(self):
        column = VideoViewColumn(self.hierarchy_en, 'FOOBAR', 'Title', 'en')
        column2 = VideoViewColumn(self.hierarchy_en, 'BARBAZ', 'Title2', 'en')

        self.assertEquals(column.user_value(self.participant), 50)
        self.assertEquals(column2.user_value(self.participant), 0)

    def test_all(self):
        cols = VideoViewColumn.all(self.hierarchy_en,
                                   self.hierarchy_en.get_root())
        self.assertEquals(len(cols), 2)
        self.assertEquals(cols[0].video_id, 'FOOBAR')
        self.assertEquals(cols[1].video_id, 'BARBAZ')

        cols = VideoViewColumn.all(self.hierarchy_es,
                                   self.hierarchy_es.get_root())
        self.assertEquals(len(cols), 0)


class MeaningfulConsentReportTest(ParticipantTestCase):

    def setUp(self):
        super(MeaningfulConsentReportTest, self).setUp()

        self.participant2 = self.create_participant()

        clinic2 = ClinicFactory()
        self.participant2.profile.clinic = clinic2
        self.participant2.profile.save()

    def test_report_creation(self):
        report = MeaningfulConsentReport(prefix="meaningfulconsent")
        self.assertEquals(report.report_prefix, "meaningfulconsent")
        self.assertIsNone(report.clinic)

    def test_report_creation_with_clinic(self):
        report = MeaningfulConsentReport(prefix="meaningfulconsent",
                                         clinic=self.clinic)
        self.assertEquals(report.report_prefix, "meaningfulconsent")
        self.assertEquals(report.clinic, self.clinic)

    def test_get_users(self):
        report = MeaningfulConsentReport(prefix="meaningfulconsent")
        self.assertEquals(len(report.get_users()), 2)

    def test_get_users_with_clinic(self):
        report = MeaningfulConsentReport(prefix="meaningfulconsent",
                                         clinic=self.clinic)

        users = report.get_users()
        self.assertEquals(len(users), 1)
        self.assertEquals(users[0], self.participant)

    def test_participant_column(self):
        report = MeaningfulConsentReport(prefix="meaningfulconsent")
        column = report.participant_column(self.hierarchy_en)
        self.assertEquals(column.user_value(self.participant),
                          self.participant.username)

    def test_percent_complete_column(self):
        report = MeaningfulConsentReport(prefix="meaningfulconsent")
        column = report.percent_complete_column(self.hierarchy_en)
        self.assertEquals(column.user_value(self.participant), 0)

        sections = self.hierarchy_en.get_root().get_descendants()
        UserPageVisit.objects.create(user=self.participant,
                                     section=sections[0],
                                     status="complete")
        UserPageVisit.objects.create(user=self.participant,
                                     section=sections[1],
                                     status="complete")
        self.assertEquals(column.user_value(self.participant), 66)

    def test_get_columns(self):
        block = YouTubeBlock()
        block.video_id = 'FOOBAR'
        block.language = 'en'
        block.title = "Title"
        block.save()
        section = self.hierarchy_en.get_root().get_next()
        section.append_pageblock("Video 1", '', content_object=block)

        report = MeaningfulConsentReport(prefix="meaningfulconsent")
        columns = report.get_columns(True, self.hierarchy_en)
        self.assertEquals(len(columns), 3)

        self.assertTrue(isinstance(columns[0], PagetreeReportColumn))
        self.assertTrue(isinstance(columns[1], PagetreeReportColumn))
        self.assertTrue(isinstance(columns[2], VideoViewColumn))
