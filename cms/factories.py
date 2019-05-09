"""Wagtail page factories"""
import factory
from factory.django import DjangoModelFactory
import wagtail_factories

from cms.models import (
    ProgramPage,
    CoursePage,
    LearningOutcomesPage,
    LearningTechniquesPage,
    FrequentlyAskedQuestion,
    FrequentlyAskedQuestionPage,
    ForTeamsPage,
    WhoShouldEnrollPage,
    CoursesInProgramPage,
    ResourcePage,
)
from cms.blocks import LearningTechniqueBlock, ResourceBlock
from courses.factories import ProgramFactory, CourseFactory


class ProgramPageFactory(wagtail_factories.PageFactory):
    """ProgramPage factory class"""

    program = factory.SubFactory(ProgramFactory)
    subhead = factory.fuzzy.FuzzyText(prefix="Subhead ")
    thumbnail_image = factory.SubFactory(wagtail_factories.ImageFactory)
    background_image = factory.SubFactory(wagtail_factories.ImageFactory)

    class Meta:
        model = ProgramPage


class CoursePageFactory(wagtail_factories.PageFactory):
    """CoursePage factory class"""

    course = factory.SubFactory(CourseFactory)
    subhead = factory.fuzzy.FuzzyText(prefix="Subhead ")
    thumbnail_image = factory.SubFactory(wagtail_factories.ImageFactory)
    background_image = factory.SubFactory(wagtail_factories.ImageFactory)

    class Meta:
        model = CoursePage


class LearningOutcomesPageFactory(wagtail_factories.PageFactory):
    """LearningOutcomesPage factory class"""

    heading = factory.fuzzy.FuzzyText(prefix="heading ")
    sub_heading = factory.fuzzy.FuzzyText(prefix="Sub-heading ")
    outcome_items = factory.SubFactory(wagtail_factories.StreamFieldFactory)

    class Meta:
        model = LearningOutcomesPage


class LearningTechniquesItemFactory(wagtail_factories.StructBlockFactory):
    """LearningTechniquesItem factory class"""

    heading = factory.fuzzy.FuzzyText(prefix="heading ")
    sub_heading = factory.fuzzy.FuzzyText(prefix="Sub-heading ")
    image = factory.SubFactory(wagtail_factories.ImageFactory)

    class Meta:
        model = LearningTechniqueBlock


class LearningTechniquesPageFactory(wagtail_factories.PageFactory):
    """LearningTechniquesPage factory class"""

    technique_items = wagtail_factories.StreamFieldFactory(
        {"techniques": LearningTechniquesItemFactory}
    )

    class Meta:
        model = LearningTechniquesPage


class FrequentlyAskedQuestionPageFactory(wagtail_factories.PageFactory):
    """ FrequentlyAskedQuestionPage factory class"""

    class Meta:
        model = FrequentlyAskedQuestionPage


class FrequentlyAskedQuestionFactory(DjangoModelFactory):
    """FrequentlyAskedQuestion factory class"""

    faqs_page = factory.SubFactory(FrequentlyAskedQuestionPageFactory)
    question = factory.fuzzy.FuzzyText(prefix="question: ")
    answer = factory.fuzzy.FuzzyText(prefix="answer: ")

    class Meta:
        model = FrequentlyAskedQuestion


class ForTeamsPageFactory(wagtail_factories.PageFactory):
    """ForTeamsPage factory class"""

    content = factory.fuzzy.FuzzyText(prefix="Content ")
    action_title = factory.fuzzy.FuzzyText(prefix="Action title ")

    class Meta:
        model = ForTeamsPage


class WhoShouldEnrollPageFactory(wagtail_factories.PageFactory):
    """WhoShouldEnrollPage factory class"""

    image = factory.SubFactory(wagtail_factories.ImageFactory)
    content = factory.SubFactory(wagtail_factories.StreamFieldFactory)

    class Meta:
        model = WhoShouldEnrollPage


class CoursesInProgramPageFactory(wagtail_factories.PageFactory):
    """CoursesInProgramPage factory class"""

    heading = factory.fuzzy.FuzzyText(prefix="Heading ")
    body = factory.fuzzy.FuzzyText(prefix="Body ")

    class Meta:
        model = CoursesInProgramPage


class ResourceBlockFactory(wagtail_factories.StructBlockFactory):
    """ResourceBlock factory class"""

    heading = factory.fuzzy.FuzzyText(prefix="Heading ")
    detail = factory.fuzzy.FuzzyText(prefix="Detail ")

    class Meta:
        model = ResourceBlock


class ResourcePageFactory(wagtail_factories.PageFactory):
    """ResourcePage factory class"""

    sub_heading = factory.fuzzy.FuzzyText(prefix="Sub heading ")
    content = wagtail_factories.StreamFieldFactory({"content": ResourceBlockFactory})

    class Meta:
        model = ResourcePage
