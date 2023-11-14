"""API for the Blog app"""
from bs4 import BeautifulSoup
from django.utils.dateformat import DateFormat
from django.utils.dateparse import parse_datetime


def transform_blog_item(item):
    """
    Makes transformation to a blog item object.
    """
    description = item["description"]
    soup = BeautifulSoup(description, "html.parser")
    item["description"] = soup.text.strip()

    image_tags = soup.find_all("img")
    item["banner_image"] = image_tags[0].get("src")

    published_date = parse_datetime(item["dc:date"])
    df = DateFormat(published_date)
    item["published_date"] = df.format("F jS, Y")

    item["categories"] = (
        item["category"] if isinstance(item["category"], list) else [item["category"]]
    )

    del item["content:encoded"]
    del item["pubDate"]
    del item["dc:date"]
    del item["author"]
    del item["guid"]
    del item["category"]
