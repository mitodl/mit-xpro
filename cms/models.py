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
from wagtail.core.blocks import RawHTMLBlock, PageChooserBlock
from wagtail.images.models import Image
from wagtail.images.blocks import ImageChooserBlock
from wagtail.snippets.models import register_snippet
from wagtailmetadata.models import MetadataPageMixin

from modelcluster.fields import ParentalKey

from mitxpro.views import get_js_settings_context
from cms.blocks import (
    LearningTechniqueBlock,
    ResourceBlock,
    UserTestimonialBlock,
    FacultyBlock,
)


class CourseProgramChildPage(Page):
    """
    Abstract page representing a child of Course/Program Page
    """

    class Meta:
        abstract = True

    parent_page_types = ["CoursePage", "ProgramPage", "HomePage"]

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
        if not self.title:
            self.title = self.__class__._meta.verbose_name.title()
        self.slug = slugify("{}-{}".format(self.get_parent().id, self.title))
        super().save(*args, **kwargs)


# Cannot name TestimonialPage otherwise pytest will try to pick up as a test
class UserTestimonialsPage(CourseProgramChildPage):
    """
    Page that holds testimonials for a product
    """

    heading = models.CharField(
        max_length=255, help_text="The heading to display on this section."
    )
    subhead = models.CharField(
        max_length=255, help_text="Subhead to display below the heading."
    )
    items = StreamField(
        [("testimonial", UserTestimonialBlock())],
        blank=False,
        help_text="Add testimonials to display in this section.",
    )
    content_panels = [
        FieldPanel("heading"),
        FieldPanel("subhead"),
        StreamFieldPanel("items"),
    ]

    class Meta:
        verbose_name = "Testimonials Section"


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

    class Meta:
        verbose_name = "Icon Grid"

    content_panels = [FieldPanel("title"), StreamFieldPanel("technique_items")]


class ForTeamsPage(CourseProgramChildPage):
    """
    CMS Page representing a "For Teams" section in a course/program page
    """

    content = RichTextField(help_text="The content shown in the section")
    action_title = models.CharField(
        max_length=255, help_text="The text to show on the call to action button"
    )
    action_url = models.URLField(
        null=True,
        blank=True,
        help_text="The URL to go to when the action button is clicked.",
    )
    dark_theme = models.BooleanField(
        blank=True,
        default=False,
        help_text="When checked, switches to dark theme (light text on dark background).",
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

    class Meta:
        verbose_name = "Text-Image Section"

    content_panels = [
        FieldPanel("title"),
        FieldPanel("content"),
        FieldPanel("action_title"),
        FieldPanel("action_url"),
        FieldPanel("dark_theme"),
        FieldPanel("switch_layout"),
        FieldPanel("image"),
    ]


class TextVideoSection(CourseProgramChildPage):
    """
    CMS Page representing a text-video section such as the "About MIT xPRO" section on the home page
    """

    content = RichTextField(help_text="The content shown in the section")
    action_title = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        help_text="The text to show on the call to action button",
    )
    action_url = models.URLField(
        null=True,
        blank=True,
        help_text="The URL to go to when the action button is clicked.",
    )
    dark_theme = models.BooleanField(
        blank=True,
        default=False,
        help_text="When checked, switches to dark theme (light text on dark background).",
    )
    switch_layout = models.BooleanField(
        blank=True,
        default=False,
        help_text="When checked, switches the position of the content and video, i.e. video on left and content on right.",
    )
    video_url = models.URLField(
        null=True,
        blank=True,
        help_text="The URL of the video to display. Must be an HLS video URL.",
    )

    content_panels = [
        FieldPanel("title"),
        FieldPanel("content"),
        FieldPanel("video_url"),
        FieldPanel("action_title"),
        FieldPanel("action_url"),
        FieldPanel("dark_theme"),
        FieldPanel("switch_layout"),
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

    # We need this to be only under a program page and home page
    parent_page_types = ["ProgramPage", "HomePage"]

    heading = models.CharField(
        max_length=255, help_text="The heading to show in this section"
    )
    body = RichTextField(
        help_text="The content to show above course carousel",
        features=["bold", "italic", "ol", "ul", "h2", "h3", "h4"],
        blank=True,
        null=True,
    )
    override_contents = models.BooleanField(
        blank=True,
        default=False,
        help_text="Manually select contents below. Otherwise displays all courses associated with the program.",
    )
    contents = StreamField(
        [
            (
                "item",
                PageChooserBlock(
                    required=False, target_model=["cms.CoursePage", "cms.ProgramPage"]
                ),
            )
        ],
        help_text="The courseware to display in this carousel",
        blank=True,
    )

    @property
    def content_pages(self):
        """
        Extracts all the pages out of the `contents` stream into a list
        """
        pages = []
        for block in self.contents:  # pylint: disable=not-an-iterable
            if block.value:
                pages.append(block.value.specific)
        return pages

    class Meta:
        verbose_name = "Courseware Carousel"

    content_panels = [
        FieldPanel("heading"),
        FieldPanel("body"),
        FieldPanel("override_contents"),
        StreamFieldPanel("contents"),
    ]


class FacultyMembersPage(CourseProgramChildPage):
    """
    FacultyMembersPage representing a "Your MIT Faculty" section on a product page
    """

    heading = models.CharField(
        max_length=255,
        help_text="The heading to display for this section on the product page.",
    )
    subhead = models.CharField(
        max_length=255,
        help_text="The subhead to display for this section on the product page.",
    )
    members = StreamField(
        [("member", FacultyBlock())],
        help_text="The faculty members to display on this page",
    )
    content_panels = [
        FieldPanel("heading"),
        FieldPanel("subhead"),
        StreamFieldPanel("members"),
    ]


class ImageCarouselPage(CourseProgramChildPage):
    """
    Page that holds image carousel.
    """

    images = StreamField(
        [("image", ImageChooserBlock(help_text="Choose an image to upload."))],
        blank=False,
        help_text="Add images for this section.",
    )

    content_panels = Page.content_panels + [StreamFieldPanel("images")]

    class Meta:
        verbose_name = "Image Carousel"


class HomePage(MetadataPageMixin, Page):
    """
    CMS Page representing the home/root route
    """

    subhead = models.CharField(
        max_length=255,
        help_text="The subhead to display in the hero section on the home page.",
    )
    background_image = models.ForeignKey(
        Image,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Background image size must be at least 1900x650 pixels.",
    )
    background_video_url = models.URLField(
        null=True,
        blank=True,
        help_text="Background video that should play over the hero section. Must be an HLS video URL. Will cover background image if selected.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("subhead"),
        FieldPanel("background_image"),
        FieldPanel("background_video_url"),
    ]

    subpage_types = [
        "CoursePage",
        "ProgramPage",
        "CoursesInProgramPage",
        "LearningTechniquesPage",
        "UserTestimonialsPage",
        "ForTeamsPage",
        "TextVideoSection",
        "ResourcePage",
        "ImageCarouselPage",
    ]

    def _get_child_page_of_type(self, cls):
        """Gets the first child page of the given type if it exists"""
        child = self.get_children().type(cls).first()
        return child.specific if child else None

    @property
    def learning_experience(self):
        """
        Gets the "Learning Experience" section subpage
        """
        return self._get_child_page_of_type(LearningTechniquesPage)

    @property
    def testimonials(self):
        """
        Gets the testimonials section subpage
        """
        return self._get_child_page_of_type(UserTestimonialsPage)

    @property
    def upcoming_courseware(self):
        """
        Gets the upcoming courseware section subpage
        """
        return self._get_child_page_of_type(CoursesInProgramPage)

    @property
    def inquiry_section(self):
        """
        Gets the "inquire now" section subpage
        """
        return self._get_child_page_of_type(ForTeamsPage)

    @property
    def about_mit_xpro(self):
        """
        Gets the "about mit xpro" section subpage
        """
        return self._get_child_page_of_type(TextVideoSection)

    @property
    def image_carousel_section(self):
        """
        Gets the "image carousel" section sub page.
        """
        return self._get_child_page_of_type(ImageCarouselPage)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)
        context.update(**get_js_settings_context(request))

        return context


class ProductPage(MetadataPageMixin, Page):
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
    background_video_url = models.URLField(
        null=True,
        blank=True,
        help_text="Background video that should play over the hero section. Must be an HLS video URL. Will cover background image if selected.",
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
        "UserTestimonialsPage",
        "FacultyMembersPage",
    ]

    def get_context(self, request, *args, **kwargs):
        context = super(ProductPage, self).get_context(request)
        context["title"] = self.title
        return context

    def _get_child_page_of_type(self, cls):
        """Gets the first child page of the given type if it exists"""
        child = self.get_children().type(cls).first()
        return child.specific if child else None


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

    @property
    def course_pages(self):
        """
        Gets a list of pages (CoursePage) of all the courses associated with this program
        """
        courses = self.program.courses.all()
        return CoursePage.objects.filter(course_id__in=courses)


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

    @property
    def program_page(self):
        """
        Gets the program page associated with this course, if it exists
        """
        return self.course.program.page if self.course and self.course.program else None


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

    sub_heading = models.CharField(
        max_length=250,
        null=True,
        blank=False,
        help_text="Sub heading of the resource page.",
    )

    content = StreamField(
        [("content", ResourceBlock())],
        blank=False,
        help_text="Enter details of content.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("sub_heading"),
        StreamFieldPanel("content"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super(ResourcePage, self).get_context(request)
        context.update(**get_js_settings_context(request))

        return context


@register_snippet
class SiteNotification(models.Model):
    """ Snippet model for showing site notifications. """

    message = RichTextField(
        max_length=255, features=["bold", "italic", "link", "document-link"]
    )

    panels = [FieldPanel("message")]

    def __str__(self):
        return self.message
