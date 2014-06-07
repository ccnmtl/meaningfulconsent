from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.http.response import HttpResponse
from django.utils.encoding import smart_str
from meaningfulconsent.main.models import UserVideoView, USERNAME_PREFIX
from pagetree.models import Hierarchy
from quizblock.models import Submission, Response
from zipfile import ZipFile
from StringIO import StringIO
import csv


def clean_header(s):
    s = s.replace('<p>', '')
    s = s.replace('</p>', '')
    s = s.replace('</div>', '')
    s = s.replace('\n', '')
    s = s.replace('\r', '')
    s = s.replace('<', '')
    s = s.replace('>', '')
    s = s.replace('\'', '')
    s = s.replace('\"', '')
    s = s.replace(',', '')
    s = s.encode('utf-8')
    return s


class QuestionColumn(object):
    def __init__(self, hierarchy, question, answer=None):
        self.hierarchy = hierarchy
        self.question = question
        self.answer = answer

        self._submission_cache = Submission.objects.filter(
            quiz=self.question.quiz)
        self._response_cache = Response.objects.filter(
            question=self.question)
        self._answer_cache = self.question.answer_set.all()

    def question_id(self):
        return "%s_%s" % (self.hierarchy.id, self.question.id)

    def question_answer_id(self):
        return "%s_%s_%s" % (self.hierarchy.id,
                             self.question.id,
                             self.answer.id)

    def identifier(self):
        if self.question and self.answer:
            return self.question_answer_id()
        else:
            return self.question_id()

    def key_row(self):
        '''itemIdentifier', 'hierarchy', 'exercise type',
        'itemType', 'itemText', 'answerIdentifier', 'answerText'''
        row = [self.question_id(),
               self.hierarchy.name,
               "Quiz",
               self.question.question_type,
               clean_header(self.question.text)]
        if self.answer:
            row.append(self.answer.id)
            row.append(clean_header(self.answer.label))
        return row

    def user_value(self, user):
        r = self._submission_cache.filter(user=user).order_by("-submitted")
        if r.count() == 0:
            # user has not submitted this form
            return ""
        submission = r[0]
        r = self._response_cache.filter(submission=submission)
        if r.count() > 0:
            if (self.question.is_short_text() or
                    self.question.is_long_text()):
                return r[0].value
            elif self.question.is_multiple_choice():
                if self.answer.value in [res.value for res in r]:
                    return self.answer.id
            else:  # single choice
                for a in self._answer_cache:
                    if a.value == r[0].value:
                        return a.id

        return ''

    @classmethod
    def all(cls, hrchy, section, key=True):
        columns = []
        ctype = ContentType.objects.get(name='quiz', app_label='quizblock')

        # quizzes
        for p in section.pageblock_set.filter(content_type=ctype):
            for q in p.block().question_set.all():
                if q.answerable() and (key or q.is_multiple_choice()):
                    # need to make a column for each answer
                    for a in q.answer_set.all():
                        columns.append(QuestionColumn(
                            hierarchy=hrchy, question=q, answer=a))
                else:
                    columns.append(QuestionColumn(hierarchy=hrchy, question=q))

        return columns


class VideoViewColumn(object):
    def __init__(self, hierarchy, video_id, title, language):
        self.hierarchy = hierarchy
        self.video_id = video_id
        self.title = title
        self.language = language

    def identifier(self):
        return self.video_id

    def key_row(self):
        '''itemIdentifier', 'hierarchy', 'exercise type',
          'item type', 'item text' '''

        return [self.identifier(), self.hierarchy.name,
                "YouTube Video", 'percent viewed',
                '%s in %s' % (self.title, self.language)]

    def user_value(self, user):
        try:
            view = UserVideoView.objects.get(user=user,
                                             video_id=self.identifier())
            return view.percent_viewed()
        except UserVideoView.DoesNotExist:
            return 0

    @classmethod
    def all(cls, hierarchy, section, key=True):
        columns = []
        ctype = ContentType.objects.get(name='you tube block')

        # quizzes
        for p in section.pageblock_set.filter(content_type=ctype):
            block = p.block()
            columns.append(VideoViewColumn(hierarchy,
                                           block.video_id,
                                           block.title,
                                           block.language))

        return columns


class PagetreeReportColumn():
    def __init__(self, hierarchy, name, group,
                 value_type, description, value_func):
        self.hierarchy = hierarchy
        self.name = name
        self.group = group
        self.value_type = value_type
        self.description = description
        self.value_func = value_func

    def identifier(self):
        """Unique identifier
        returns a spaceless, lower-case string
        """
        return "%s_%s" % (self.hierarchy.id, self.name)

    def key_row(self):
        """Unique identifier for this piece of information
        returns a spaceless, lower-case string
        """
        return [self.identifier(), self.hierarchy.name,
                self.group, self.value_type, self.description]

    def user_value(self, user):
        return self.value_func(user)


class PagetreeReport():
    def __init__(self, report_prefix):
        self.report_prefix = report_prefix

    def get_users(self):
        return User.objects.all()

    def initial_value_headers(self):
        return []

    def get_columns(self, key, hierarchy):
        """ return an array of PagetreeReportColumns """
        return []

    def all_results_key(self, output, hierarchies):
        """
            A "key" for all questions and answers in the system.
            * One row for short/long text questions
            * Multiple rows for single/multiple-choice questions.
            Each question/answer pair get a row
            itemIdentifier - unique system identifier,
                concatenates hierarchy id, item type string,
                page block id (if necessary) and item id
            hierarchy - first child label in the hierarchy
            section description - ['', 'Prescription Writing Exercise', 'Quiz']
            itemType - ['single choice', 'multiple choice', 'short text',
                        'bool', 'percent']
            itemText - identifying text for the item
            answerIdentifier - for single/multiple-choice questions. answer id
            answerText
        """
        writer = csv.writer(output)
        headers = ['itemIdentifier', 'hierarchy', 'exercise type',
                   'itemType', 'itemText', 'answerIdentifier', 'answerText']
        writer.writerow(headers)
        writer.writerow('')

        columns = []
        for hierarchy in hierarchies:
            columns += self.get_columns(False, hierarchy)

        for column in columns:
            writer.writerow(column.key_row())

        return writer

    def all_results(self, output, hierarchies, users):
        """
        All system results
        * One or more column for each question in system.
            ** 1 column for short/long text. label = itemIdentifier from key
            ** 1 column for single choice. label = itemIdentifier from key
            ** n columns for multiple choice: 1 column for each possible answer
               *** column labeled as itemIdentifer_answer.id

            * One row for each user in the system.
                1. username
                2 - n: answers
                    * short/long text. text value
                    * single choice. answer.id
                    * multiple choice.
                        ** answer id is listed in each question/answer
                        column the user selected
                    * Unanswered fields represented as an empty cell
        """
        writer = csv.writer(output)

        columns = []
        for hierarchy in hierarchies:
            columns += self.get_columns(False, hierarchy)

        key_column_headings = []
        for column in columns:
            key_column_headings += [column.identifier()]
        writer.writerow(key_column_headings)

        for user in users:
            row = []
            for column in columns:
                v = smart_str(column.user_value(user))
                row.append(v)
            writer.writerow(row)

        return writer

    def get_zip_file(self):
        # setup zip file for the key & value file
        response = HttpResponse(mimetype='application/zip')

        disposition = 'attachment; filename=%s.zip' % self.report_prefix
        response['Content-Disposition'] = disposition

        z = ZipFile(response, 'w')

        output = StringIO()  # temp output file

        # Key File
        hierarchies = Hierarchy.objects.all()
        self.all_results_key(output, hierarchies)
        z.writestr("meaningfulconsent_key.csv", output.getvalue())

        # Results file
        output.truncate(0)
        output.seek(0)
        self.all_results(output, hierarchies, self.get_users())
        z.writestr("meaningfulconsent_values.csv", output.getvalue())

        return response


class MeaningfulConsentReport(PagetreeReport):
    def get_users(self):
        users = User.objects.filter(is_active=False,
                                    username__startswith=USERNAME_PREFIX)

        if hasattr(self, 'clinic_id'):
            users.filter(profile__clinic__id=self.clinic_id)

        return users

    def participant_column(self, hierarchy):
        return PagetreeReportColumn(hierarchy, "participant_id", 'profile',
                                    'string', 'Randomized Participant Id',
                                    lambda x: x.username)

    def percent_complete_column(self, hierarchy):
        return PagetreeReportColumn(
            hierarchy, "percent_complete", 'profile', 'percent',
            '% of hierarchy completed',
            lambda x: x.profile.percent_complete_hierarchy(hierarchy))

    def get_columns(self, key, hierarchy):
        columns = [self.participant_column(hierarchy),
                   self.percent_complete_column(hierarchy)]

        for section in hierarchy.get_root().get_descendants():
            columns += QuestionColumn.all(hierarchy, section, key)
            columns += VideoViewColumn.all(hierarchy, section, key)
        return columns
