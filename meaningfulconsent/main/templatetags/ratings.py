from django import template
from django.contrib.contenttypes.models import ContentType
from pagetree.models import PageBlock
from quizblock.models import Response, Quiz

register = template.Library()


class GetTopicRatings(template.Node):
    def __init__(self, var_name):
        self.var_name = var_name

    def render(self, context):
        u = context['request'].user

        quiz_type = ContentType.objects.get_for_model(Quiz)
        blocks = PageBlock.objects.filter(css_extra='topic-rating',
                                          content_type=quiz_type)

        ratings = []
        for b in blocks:
            # assumption: each of these quiz types has one question
            question = b.content_object.question_set.first()

            responses = Response.objects.filter(
                submission__quiz=b.content_object,
                submission__user=u).order_by("-submission__submitted")

            if responses.count() > 0:
                r = responses[0]
                answer = r.question.answer_set.get(value=r.value)
                ratings.append((question.intro_text, answer.label))
            else:
                ratings.append((question.intro_text, ''))

        context[self.var_name] = ratings
        return ''


@register.tag('get_topic_ratings')
def gettopicratings(parser, token):
    var_name = token.split_contents()[1:][1]
    return GetTopicRatings(var_name)
