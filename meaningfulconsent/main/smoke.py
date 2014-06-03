from django.contrib.auth.models import User
from meaningfulconsent.main.views import get_quiz_blocks
from smoketest import SmokeTest


class DBConnectivity(SmokeTest):
    def test_retrieve(self):
        cnt = User.objects.all().count()
        # all we care about is not getting an exception
        self.assertTrue(cnt > -1)


class CustomQuizBlocks(SmokeTest):

    def test_risk_rating_quizzes(self):
        blocks = get_quiz_blocks("topic-rating")

        # Risk rating quizzes must have a single question w/intro text
        for b in blocks:
            self.assertEqual(b.content_object.question_set.count(),
                             1,
                             "Expected 1 question in %s. There are %s" %
                             (b.content_object,
                              b.content_object.question_set.count()))

            question = b.content_object.question_set.first()
            self.assertEqual(question.question_type, "single choice")
            self.assertIsNotNone(question.intro_text)
            self.assertTrue(len(question.intro_text) > 0)

    def test_discussion_quizzes(self):
        blocks = get_quiz_blocks("topic-discussion")

        # Discussion quizzes must have a single MC question w/intro text
        for b in blocks:
            self.assertEqual(b.content_object.question_set.count(),
                             1,
                             "Expected 1 question in %s. There are %s" %
                             (b.content_object,
                              b.content_object.question_set.count()))

            question = b.content_object.question_set.first()
            self.assertEqual(question.question_type, "multiple choice")
            self.assertIsNotNone(question.intro_text)
            self.assertTrue(len(question.intro_text) > 0)
