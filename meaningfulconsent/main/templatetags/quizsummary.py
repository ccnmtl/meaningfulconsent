from django import template
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from pagetree.models import PageBlock
from quizblock.models import Response, Submission, Quiz


register = template.Library()


def get_quizzes_by_css_class(hierarchy, cls):
    ctype = ContentType.objects.get_for_model(Quiz)
    blocks = PageBlock.objects.filter(content_type__pk=ctype.pk)
    blocks = blocks.filter(css_extra__contains=cls)
    blocks = blocks.filter(section__hierarchy=hierarchy)
    return blocks


class GetTopicRatings(template.Node):
    def __init__(self, user, quiz_class, var_name):
        self.user = user
        self.quiz_class = quiz_class
        self.var_name = var_name

    def render(self, context):
        u = context[self.user]
        cls = context[self.quiz_class]

        blocks = get_quizzes_by_css_class(u.profile.default_hierarchy(), cls)

        ratings = {}
        for b in blocks:
            # assumption: each of these quiz types has one question
            question = b.content_object.question_set.first()

            submissions = Submission.objects.filter(
                quiz=b.content_object, user=u).order_by("-submitted")

            if submissions.count() > 0:
                # most recent submission. pick up the one response.
                r = Response.objects.filter(
                    submission=submissions[0]).first()
                answer = r.question.answer_set.get(value=r.value)

                key = slugify(answer.label)
                if answer.label not in ratings:
                    ratings[key] = []
                ratings[key].append(question.intro_text)

        context[self.var_name] = ratings
        return ''


@register.tag('get_quiz_summary')
def quizsummary(parser, token):
    user = token.split_contents()[1:][0]
    quiz_class = token.split_contents()[1:][1]
    var_name = token.split_contents()[1:][3]
    return GetTopicRatings(user, quiz_class, var_name)
