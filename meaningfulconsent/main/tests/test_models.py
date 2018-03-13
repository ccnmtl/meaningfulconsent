from django.test import TestCase
from pagetree.models import Hierarchy, UserPageVisit, Section
from quizblock.tests.test_models import FakeReq

from meaningfulconsent.main.models import Clinic, UserVideoView, \
    QuizSummaryBlock, YouTubeBlock
from meaningfulconsent.main.tests.factories import UserFactory, \
    ModuleFactory, ParticipantFactory, QuizSummaryBlockFactory, \
    YouTubeBlockFactory, SimpleImageBlockFactory


class UserProfileTest(TestCase):

    def setUp(self):
        Clinic.objects.create(name='Test Clinic')
        self.user = UserFactory()
        self.participant = ParticipantFactory()

        ModuleFactory("en", "/pages/en/")
        ModuleFactory("es", "/pages/es/")

        self.hierarchy_en = Hierarchy.objects.get(name='en')
        self.hierarchy_es = Hierarchy.objects.get(name='es')

    def test_auto_profile_create(self):
        self.assertFalse(self.user.profile.is_participant())
        self.assertFalse(self.participant.is_active)
        self.assertTrue(self.participant.profile.is_participant())

    def test_default_location(self):
        self.assertEquals(self.user.profile.default_location(),
                          self.hierarchy_en.get_root())

        self.user.profile.language = "es"
        self.user.profile.save()
        self.assertEquals(self.user.profile.default_location(),
                          self.hierarchy_es.get_root())

    def test_last_location_no_visits(self):
        # no language
        self.assertEquals(self.user.profile.last_location(),
                          self.hierarchy_en.get_root())

        self.user.profile.language = "en"
        self.user.profile.save()

        self.assertEquals(self.user.profile.last_location().get_absolute_url(),
                          "/pages/en//")

        self.user.profile.language = "es"
        self.user.profile.save()
        self.assertEquals(self.user.profile.last_location().get_absolute_url(),
                          "/pages/es//")

    def test_last_location_with_visits(self):
        self.user.profile.language = 'en'
        self.user.profile.save()

        sections = self.hierarchy_en.get_root().get_descendants()
        UserPageVisit.objects.create(user=self.user,
                                     section=sections[0],
                                     status="complete")
        UserPageVisit.objects.create(user=self.user,
                                     section=sections[1],
                                     status="complete")
        self.assertEquals(self.user.profile.last_location().get_absolute_url(),
                          "/pages/en/one/introduction/")

        self.user.profile.language = "es"
        self.user.profile.save()
        self.assertEquals(self.user.profile.last_location().get_absolute_url(),
                          "/pages/es//")

    def test_percent_complete(self):
        self.assertEquals(self.user.profile.percent_complete(), 0)

        self.user.profile.language = 'en'
        self.user.profile.save()
        self.assertEquals(self.user.profile.percent_complete(), 0)

        sections = self.hierarchy_en.get_root().get_descendants()
        UserPageVisit.objects.create(user=self.user,
                                     section=sections[0],
                                     status="complete")
        UserPageVisit.objects.create(user=self.user,
                                     section=sections[1],
                                     status="complete")

        self.assertEquals(self.user.profile.percent_complete(), 50)

        self.user.profile.language = "es"
        self.user.profile.save()
        self.assertEquals(self.user.profile.percent_complete(), 0)

    def test_time_spent(self):
        self.user.profile.language = 'en'
        self.user.profile.save()
        self.assertEquals(self.user.profile.time_spent('en'), 0)

        sections = self.hierarchy_en.get_root().get_descendants()
        UserPageVisit.objects.create(user=self.user,
                                     section=sections[0],
                                     status="complete")
        self.assertTrue(self.user.profile.time_spent('en') > 0)

        UserPageVisit.objects.create(user=self.user,
                                     section=sections[1],
                                     status="complete")

        self.assertTrue(self.user.profile.time_spent('en') > 0)


class UserVideoViewTest(TestCase):

    def setUp(self):
        Clinic.objects.create(name='Test Clinic')
        self.user = UserFactory()

    def test_percent_viewed(self):
        uvv = UserVideoView(user=self.user,
                            video_id='ABCDEFG',
                            video_duration=100)

        self.assertEquals(uvv.percent_viewed(), 0)

        uvv.seconds_viewed = 50
        self.assertEquals(uvv.percent_viewed(), 50.0)

        uvv.seconds_viewed = 200
        self.assertEquals(uvv.percent_viewed(), 200.0)


class QuizSummaryBlockTest(TestCase):

    def test_basics(self):
        block = QuizSummaryBlockFactory()
        ModuleFactory("one", "/pages/one/")
        self.hierarchy = Hierarchy.objects.get(name='one')
        self.section_one = Section.objects.get(slug='one')

        self.section_one.append_pageblock('test', '', block)

        self.assertTrue(block.__str__().startswith('One'))
        self.assertIsNotNone(block.pageblock())
        self.assertFalse(block.needs_submit())
        self.assertTrue(block.unlocked(None))

    def test_add_form(self):
        add_form = QuizSummaryBlockFactory().add_form()
        self.assertTrue("quiz_class" in add_form.fields)

    def test_edit_form(self):
        edit_form = QuizSummaryBlockFactory().edit_form()
        self.assertTrue("quiz_class" in edit_form.fields)

    def test_create(self):
        r = FakeReq()
        r.POST = {'quiz_class': 'quiz class info here'}
        block = QuizSummaryBlock.create(r)
        self.assertEquals(block.quiz_class, 'quiz class info here')
        self.assertEquals(block.display_name, 'Quiz Summary Block')

    def test_edit(self):
        block = QuizSummaryBlockFactory()
        block.edit({'quiz_class': 'updated class'}, None)
        self.assertEquals(block.quiz_class, 'updated class')

    def test_as_dict_create_from_dict(self):
        block = QuizSummaryBlockFactory()
        d = block.as_dict()
        self.assertEquals(block.quiz_class, d['quiz_class'])

        block2 = QuizSummaryBlock.create_from_dict(d)
        self.assertEquals(block2.quiz_class, block.quiz_class)


class YouTubeBlockTest(TestCase):

    def test_basics(self):
        block = YouTubeBlockFactory()
        ModuleFactory("one", "/pages/one/")
        self.hierarchy = Hierarchy.objects.get(name='one')
        self.section_one = Section.objects.get(slug='one')

        self.section_one.append_pageblock('test', '', block)

        self.assertTrue(block.__str__().startswith('One'))
        self.assertIsNotNone(block.pageblock())
        self.assertFalse(block.needs_submit())
        self.assertTrue(block.unlocked(None))

    def test_add_form(self):
        add_form = YouTubeBlockFactory().add_form()
        self.assertTrue("video_id" in add_form.fields)
        self.assertTrue("title" in add_form.fields)
        self.assertTrue("language" in add_form.fields)

    def test_edit_form(self):
        edit_form = YouTubeBlockFactory().edit_form()
        self.assertTrue("video_id" in edit_form.fields)
        self.assertTrue("title" in edit_form.fields)
        self.assertTrue("language" in edit_form.fields)

    def test_create(self):
        r = FakeReq()
        r.POST = {'video_id': 'abcdefg', 'language': 'en', 'title': 'Sample'}
        block = YouTubeBlock.create(r)
        self.assertEquals(block.video_id, 'abcdefg')
        self.assertEquals(block.language, 'en')
        self.assertEquals(block.title, 'Sample')
        self.assertEquals(block.display_name, 'YouTube Video')

    def test_edit(self):
        block = YouTubeBlockFactory()
        block.edit({'video_id': 'xyz', 'language': 'es', 'title': 'Foo'}, None)
        self.assertEquals(block.video_id, 'xyz')
        self.assertEquals(block.language, 'es')
        self.assertEquals(block.title, 'Foo')

    def test_as_dict_create_from_dict(self):
        block = YouTubeBlockFactory()
        d = block.as_dict()
        self.assertEquals(block.video_id, d['video_id'])
        self.assertEquals(block.language, d['language'])
        self.assertEquals(block.title, d['title'])

        block2 = YouTubeBlock.create_from_dict(d)
        self.assertEquals(block2.video_id, block.video_id)
        self.assertEquals(block2.language, block.language)
        self.assertEquals(block2.title, block.title)


class SimpleImageBlockTest(TestCase):

    def test_basics(self):
        block = SimpleImageBlockFactory()
        ModuleFactory("one", "/pages/one/")
        self.hierarchy = Hierarchy.objects.get(name='one')
        self.section_one = Section.objects.get(slug='one')

        self.section_one.append_pageblock('test', '', block)

        self.assertTrue(block.__str__().startswith('One'))
        self.assertIsNotNone(block.pageblock())
        self.assertFalse(block.needs_submit())
        self.assertTrue(block.unlocked(None))
        self.assertEquals(block.display_name, 'Simple Image Block')

    def test_add_form(self):
        add_form = SimpleImageBlockFactory().add_form()
        self.assertTrue("caption" in add_form.fields)
        self.assertTrue("image" in add_form.fields)
        self.assertTrue("alt" in add_form.fields)

    def test_edit_form(self):
        edit_form = SimpleImageBlockFactory().edit_form()
        self.assertTrue("caption" in edit_form.fields)
        self.assertTrue("image" in edit_form.fields)
        self.assertTrue("alt" in edit_form.fields)

    def test_edit(self):
        block = SimpleImageBlockFactory()
        block.edit({'caption': 'xyz', 'alt': 'foo'}, None)
        self.assertEquals(block.caption, 'xyz')
        self.assertEquals(block.alt, 'foo')
