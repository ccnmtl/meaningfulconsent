from django import template
from django.contrib.contenttypes.models import ContentType
from pagetree.models import PageBlock
from quizblock.models import Response, Quiz, Submission

register = template.Library()


class GetTopicRatings(template.Node):
    def __init__(self, user, quiz_class, var_name):
        self.user = user
        self.quiz_class = quiz_class
        self.var_name = var_name

    def render(self, context):
        u = context[self.user]
        cls = context[self.quiz_class]

        quiz_type = ContentType.objects.get_for_model(Quiz)
        blocks = PageBlock.objects.filter(css_extra=cls,
                                          content_type=quiz_type)

        ratings = []
        for b in blocks:
            # assumption: each of these quiz types has one question
            question = b.content_object.question_set.first()
            values = []

            submissions = Submission.objects.filter(
                quiz=b.content_object, user=u).order_by(
                "-submitted")

            if submissions.count() > 0:
                # most recent submission
                responses = Response.objects.filter(submission=submissions[0])
                for r in responses:
                    answer = r.question.answer_set.get(value=r.value)
                    values.append(answer.label)

            ratings.append((question.intro_text, values))

        context[self.var_name] = ratings
        return ''


@register.tag('get_quiz_summary')
def quizsummary(parser, token):
    user = token.split_contents()[1:][0]
    quiz_class = token.split_contents()[1:][1]
    var_name = token.split_contents()[1:][3]
    return GetTopicRatings(user, quiz_class, var_name)
