"""
Page models for the CMS
"""
from django.db import models
from django.utils.text import slugify

from wagtail.admin.edit_handlers import (
    FieldPanel,
    MultiFieldPanel,
    StreamFieldPanel,
    InlinePanel,
)
from wagtail.core import blocks
from wagtail.core.models import Orderable, Page
from wagtail.core.fields import RichTextField, StreamField
from wagtail.core.blocks import RawHTMLBlock
from wagtail.images.models import Image
from wagtail.images.blocks import ImageChooserBlock

from modelcluster.fields import ParentalKey

from mitxpro.views import get_js_settings_context
from .blocks import LearningTechniqueBlock, ResourceBlock


class CourseProgramChildPage(Page):
    """
    Abstract page representing a child of Course/Program Page
    """

    class Meta:
        abstract = True

    parent_page_types = ["CoursePage", "ProgramPage"]

    # disable promote panels, no need for slug entry, it will be autogenerated
    promote_panels = []

    @classmethod
    def can_create_at(cls, parent):
        # You can only create one of these page under course / program.
        return (
            super(CourseProgramChildPage, cls).can_create_at(parent)
            and parent.get_children().type(cls).count() == 0
        )

    def save(self, *args, **kwargs):
        # autogenerate a unique slug so we don't hit a ValidationError
        self.title = self.__class__._meta.verbose_name.title()
        self.slug = slugify("{}-{}".format(self.get_parent().id, self.title))
        super().save(*args, **kwargs)


class LearningOutcomesPage(CourseProgramChildPage):
    """
    Learning outcomes page for learning benefits.
    """

    subpage_types = []
    heading = models.CharField(
        max_length=250,
        blank=False,
        help_text="Heading highlighting the learning outcomes generally.",
    )
    sub_heading = models.CharField(
        max_length=250,
        null=True,
        blank=False,
        help_text="Sub heading for learning outcomes.",
    )

    outcome_items = StreamField(
        [("outcome", blocks.TextBlock(icon="plus"))],
        blank=False,
        help_text="Detail about What you'll learn as learning outcome.",
    )

    content_panels = [
        FieldPanel("heading"),
        FieldPanel("sub_heading"),
        StreamFieldPanel("outcome_items"),
    ]


class LearningTechniquesPage(CourseProgramChildPage):
    """
    Teaching techniques page for learning.
    """

    subpage_types = []
    technique_items = StreamField(
        [("techniques", LearningTechniqueBlock())],
        blank=False,
        help_text="Enter detail about how you'll learn.",
    )

    content_panels = [StreamFieldPanel("technique_items")]


class ForTeamsPage(CourseProgramChildPage):
    """
    CMS Page representing a "For Teams" section in a course/program page
    """

    content = RichTextField(help_text="The content shown in the section")
    action_title = models.CharField(
        max_length=255, help_text="The text to show on the call to action button"
    )
    switch_layout = models.BooleanField(
        blank=True,
        default=False,
        help_text="When checked, switches the position of the image and content, i.e. image on left and content on right.",
    )
    image = models.ForeignKey(
        Image,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Image size must be at least 750x505 pixels.",
    )
    content_panels = [
        FieldPanel("content"),
        FieldPanel("action_title"),
        FieldPanel("switch_layout"),
        FieldPanel("image"),
    ]


class WhoShouldEnrollPage(CourseProgramChildPage):
    """
    Who should enroll child page for "Who Should Enroll" section.
    """

    subpage_types = []

    image = models.ForeignKey(
        Image,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Image size must be at least 870x500 pixels.",
    )
    content = StreamField(
        [
            (
                "item",
                blocks.RichTextBlock(
                    icon="plus", features=["bold", "italic", "ol", "ul"]
                ),
            )
        ],
        blank=False,
        help_text='Contents of the "Who Should Enroll" section.',
    )
    switch_layout = models.BooleanField(
        blank=True,
        default=False,
        help_text="Switch image to the left and content to the right",
    )

    content_panels = [
        StreamFieldPanel("content"),
        FieldPanel("image"),
        FieldPanel("switch_layout"),
    ]


class CoursesInProgramPage(CourseProgramChildPage):
    """
    CMS Page representing a "Courses in Program" section in a program
    """

    # We need this to be only under a program page
    parent_page_types = ["ProgramPage"]

    heading = models.CharField(
        max_length=255, help_text="The heading to show in this section"
    )
    body = RichTextField(
        help_text="The content to show above course carousel",
        features=["bold", "italic", "ol", "ul", "h2", "h3", "h4"],
    )

    content_panels = [FieldPanel("heading"), FieldPanel("body")]


class ProductPage(Page):
    """
    Abstract product page
    """

    class Meta:
        abstract = True

    description = RichTextField(
        blank=True, help_text="The description shown on the program page"
    )
    subhead = models.CharField(
        max_length=255,
        help_text="A short subheading to appear below the title on the program/course page",
    )
    video_title = RichTextField(
        blank=True, help_text="The title to be displayed for the program/course video"
    )
    video_url = models.URLField(
        null=True,
        blank=True,
        help_text="URL to the video to be displayed for this program/course",
    )
    duration = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="A short description indicating how long it takes to complete (e.g. '4 weeks')",
    )
    background_image = models.ForeignKey(
        Image,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Background image size must be at least 1900x650 pixels.",
    )
    time_commitment = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="A short description indicating about the time commitments.",
    )
    thumbnail_image = models.ForeignKey(
        Image,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Thumbnail size must be at least 690x530 pixels.",
    )
    content = StreamField(
        [
            ("heading", blocks.CharBlock(classname="full title")),
            ("paragraph", blocks.RichTextBlock()),
            ("image", ImageChooserBlock()),
            ("raw_html", RawHTMLBlock()),
        ],
        blank=True,
        help_text="The content of this tab on the program page",
    )

    content_panels = Page.content_panels + [
        FieldPanel("subhead"),
        FieldPanel("video_title"),
        FieldPanel("video_url"),
        FieldPanel("duration"),
        FieldPanel("time_commitment"),
        FieldPanel("description", classname="full"),
        FieldPanel("background_image"),
        FieldPanel("thumbnail_image"),
        StreamFieldPanel("content"),
    ]

    subpage_types = [
        "LearningOutcomesPage",
        "LearningTechniquesPage",
        "FrequentlyAskedQuestionPage",
        "ForTeamsPage",
        "WhoShouldEnrollPage",
        "CoursesInProgramPage",
    ]

    def get_context(self, request, *args, **kwargs):
        context = super(ProductPage, self).get_context(request)
        context["title"] = self.title
        return context


class ProgramPage(ProductPage):
    """
    CMS page representing the a Program
    """

    template = "cms/product_page.html"

    program = models.OneToOneField(
        "courses.Program",
        null=True,
        on_delete=models.SET_NULL,
        help_text="The program for this page",
    )

    content_panels = [FieldPanel("program")] + ProductPage.content_panels


class CoursePage(ProductPage):
    """
    CMS page representing a Course
    """

    template = "cms/product_page.html"

    course = models.OneToOneField(
        "courses.Course",
        null=True,
        on_delete=models.SET_NULL,
        help_text="The course for this page",
    )

    content_panels = [FieldPanel("course")] + ProductPage.content_panels


class FrequentlyAskedQuestionPage(CourseProgramChildPage):
    """
    FAQs page for program/course
    """

    content_panels = [InlinePanel("faqs", label="Frequently Asked Questions")]

    def save(self, *args, **kwargs):
        # autogenerate a unique slug so we don't hit a ValidationError
        self.title = "Frequently Asked Questions"
        self.slug = slugify("{}-{}".format(self.get_parent().id, self.title))
        super().save(*args, **kwargs)


class FrequentlyAskedQuestion(Orderable):
    """
    FAQs for the program/course page
    """

    faqs_page = ParentalKey(FrequentlyAskedQuestionPage, related_name="faqs", null=True)
    question = models.TextField()
    answer = RichTextField()

    content_panels = [
        MultiFieldPanel(
            [FieldPanel("question"), FieldPanel("answer")],
            heading="Frequently Asked Questions",
            classname="collapsible",
        )
    ]


class ResourcePage(Page):
    """
    Basic resource page for all resource page.
    """

    template = "../../mitxpro/templates/resource_template.html"

    # disable promote panels, no need for slug entry, it will be autogenerated
    promote_panels = []

    sub_heading = models.CharField(
        max_length=250,
        null=True,
        blank=False,
        help_text="Sub heading of the resource page.",
    )

    content = StreamField(
        [("content", ResourceBlock())],
        blank=False,
        help_text="Enter detail of content.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("sub_heading"),
        StreamFieldPanel("content"),
    ]

    unique_together = ["title", "sub_heading"]

    def get_context(self, request, *args, **kwargs):
        context = super(ResourcePage, self).get_context(request)
        context.update(**get_js_settings_context(request))

        return context

    def save(self, *args, **kwargs):
        # autogenerate a unique slug so we don't hit a ValidationError
        self.slug = slugify("{}-{}".format(self.title, self.sub_heading))
        super().save(*args, **kwargs)
