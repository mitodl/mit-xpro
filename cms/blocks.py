"""
Wagtail custom blocks for the CMS
"""
from wagtail.core import blocks
from wagtail.images.blocks import ImageChooserBlock


class LearningTechniqueBlock(blocks.StructBlock):
    """
    A custom block for Learning techniques.
    """

    heading = blocks.CharBlock(max_length=100)
    sub_heading = blocks.CharBlock(max_length=250)
    image = ImageChooserBlock()

    class Meta:
        icon = "plus"


class ResourceBlock(blocks.StructBlock):
    """
    A custom block for resource pages.
    """

    heading = blocks.CharBlock(max_length=100)
    detail = blocks.RichTextBlock()
