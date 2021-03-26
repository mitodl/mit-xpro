"""mitxpro utilities"""
import csv
import datetime
from enum import auto, Flag
import json
import logging
import itertools
from urllib.parse import urlparse, urlunparse, ParseResult

from django.conf import settings
from django.core.serializers import serialize
from django.db import models
from django.http import HttpRequest
from django.http.response import HttpResponse
from django.templatetags.static import static
import pytz
from rest_framework import status
import requests

log = logging.getLogger(__name__)


class FeatureFlag(Flag):
    """
    FeatureFlag enum

    Members should have values of increasing powers of 2 (1, 2, 4, 8, ...)

    """

    EXAMPLE_FEATURE = auto()


def ensure_trailing_slash(url):
    """ensure a url has a trailing slash"""
    return url if url.endswith("/") else url + "/"


def public_path(request):
    """
    Return the correct public_path for Webpack to use
    """
    if settings.USE_WEBPACK_DEV_SERVER:
        return ensure_trailing_slash(webpack_dev_server_url(request))
    else:
        return ensure_trailing_slash(static("bundles/"))


def webpack_dev_server_host(request):
    """
    Get the correct webpack dev server host
    """
    return settings.WEBPACK_DEV_SERVER_HOST or request.get_host().split(":")[0]


def webpack_dev_server_url(request):
    """
    Get the full URL where the webpack dev server should be running
    """
    return "http://{}:{}".format(
        webpack_dev_server_host(request), settings.WEBPACK_DEV_SERVER_PORT
    )


def is_near_now(time):
    """
    Returns true if time is within five seconds or so of now
    Args:
        time (datetime.datetime):
            The time to test
    Returns:
        bool:
            True if near now, false otherwise
    """
    now = datetime.datetime.now(tz=pytz.UTC)
    five_seconds = datetime.timedelta(0, 5)
    return now - five_seconds < time < now + five_seconds


def now_in_utc():
    """
    Get the current time in UTC
    Returns:
        datetime.datetime: A datetime object for the current time
    """
    return datetime.datetime.now(tz=pytz.UTC)


def format_datetime_for_filename(datetime_object, include_time=False, include_ms=False):
    """
    Formats a datetime object for use as part of a filename

    Args:
        datetime_object (datetime.datetime):
        include_time (bool): True if the formatted string should include the time (hours, minutes, seconds)
        include_ms (bool): True if the formatted string should include the microseconds

    Returns:
        str: Formatted datetime
    """
    format_parts = ["%Y%m%d"]
    if include_time or include_ms:
        format_parts.append("%H%M%S")
    if include_ms:
        format_parts.append("%f")
    return datetime_object.strftime("_".join(format_parts))


def case_insensitive_equal(str1, str2):
    """
    Compares two strings to determine if they are case-insensitively equal

    Args:
        str1 (str):
        str2 (str):

    Returns:
        bool: True if the strings are equal, ignoring case
    """
    return str1.lower() == str2.lower()


def dict_without_keys(d, *omitkeys):
    """
    Returns a copy of a dict without the specified keys

    Args:
        d (dict): A dict that to omit keys from
        *omitkeys: Variable length list of keys to omit

    Returns:
        dict: A dict with omitted keys
    """
    return {key: d[key] for key in d.keys() if key not in omitkeys}


def filter_dict_by_key_set(dict_to_filter, key_set):
    """Takes a dictionary and returns a copy with only the keys that exist in the given set"""
    return {key: dict_to_filter[key] for key in dict_to_filter.keys() if key in key_set}


def serialize_model_object(obj):
    """
    Serialize model into a dict representable as JSON
    Args:
        obj (django.db.models.Model): An instantiated Django model
    Returns:
        dict:
            A representation of the model
    """
    # serialize works on iterables so we need to wrap object in a list, then unwrap it
    data = json.loads(serialize("json", [obj]))[0]
    serialized = data["fields"]
    serialized["id"] = data["pk"]
    return serialized


def get_field_names(model):
    """
    Get field names which aren't autogenerated

    Args:
        model (class extending django.db.models.Model): A Django model class
    Returns:
        list of str:
            A list of field names
    """
    return [
        field.name
        for field in model._meta.get_fields()
        if not field.auto_created  # pylint: disable=protected-access
    ]


def first_matching_item(iterable, predicate):
    """
    Gets the first item in an iterable that matches a predicate (or None if nothing matches)

    Returns:
        Matching item or None
    """
    return next(filter(predicate, iterable), None)


def matching_item_index(iterable, value_to_match):
    """
    Returns the index of the given value in the iterable

    Args:
        iterable (Iterable): The iterable to search
        value_to_match (Any): The value to match

    Returns:
        int: The index of the matching value

    Raises:
        StopIteration: Raised if the value is not found in the iterable
    """
    return next(i for i, value in enumerate(iterable) if value == value_to_match)


def find_object_with_matching_attr(iterable, attr_name, value):
    """
    Finds the first item in an iterable that has an attribute with the given name and value. Returns
    None otherwise.

    Returns:
        Matching item or None
    """
    for item in iterable:
        try:
            if getattr(item, attr_name) == value:
                return item
        except AttributeError:
            pass
    return None


def has_equal_properties(obj, property_dict):
    """
    Returns True if the given object has the properties indicated by the keys of the given dict, and the values
    of those properties match the values of the dict
    """
    for field, value in property_dict.items():
        try:
            if getattr(obj, field) != value:
                return False
        except AttributeError:
            return False
    return True


def first_or_none(iterable):
    """
    Returns the first item in an iterable, or None if the iterable is empty

    Args:
        iterable (iterable): Some iterable
    Returns:
        first item or None
    """
    return next((x for x in iterable), None)


def max_or_none(iterable):
    """
    Returns the max of some iterable, or None if the iterable has no items

    Args:
        iterable (iterable): Some iterable
    Returns:
        max item or None
    """
    try:
        return max(iterable)
    except ValueError:
        return None


def partition(items, predicate=bool):
    """
    Partitions an iterable into two different iterables - the first does not match the given condition, and the second
    does match the given condition.

    Args:
        items (iterable): An iterable of items to partition
        predicate (function): A function that takes each item and returns True or False
    Returns:
        tuple of iterables: An iterable of non-matching items, paired with an iterable of matching items
    """
    a, b = itertools.tee((predicate(item), item) for item in items)
    return (item for pred, item in a if not pred), (item for pred, item in b if pred)


def partition_to_lists(items, predicate=bool):
    """
    Partitions an iterable into two different lists - the first does not match the given condition, and the second
    does match the given condition.

    Args:
        items (iterable): An iterable of items to partition
        predicate (function): A function that takes each item and returns True or False
    Returns:
        tuple of lists: A list of non-matching items, paired with a list of matching items
    """
    a, b = partition(items, predicate=predicate)
    return list(a), list(b)


def unique(iterable):
    """
    Returns a generator containing all unique items in an iterable

    Args:
        iterable (iterable): An iterable of any hashable items
    Returns:
        generator: Unique items in the given iterable
    """
    seen = set()
    return (x for x in iterable if x not in seen and not seen.add(x))


def unique_ignore_case(strings):
    """
    Returns a generator containing all unique strings (coerced to lowercase) in a given iterable

    Args:
        strings (iterable of str): An iterable of strings
    Returns:
        generator: Unique lowercase strings in the given iterable
    """
    seen = set()
    return (s for s in map(str.lower, strings) if s not in seen and not seen.add(s))


def item_at_index_or_none(indexable, index):
    """
    Returns the item at a certain index, or None if that index doesn't exist

    Args:
        indexable (list or tuple):
        index (int): The index in the list or tuple

    Returns:
        The item at the given index, or None
    """
    try:
        return indexable[index]
    except IndexError:
        return None


def item_at_index_or_blank(indexable, index):
    """
    Returns the item at a certain index, or a blank string if that index doesn't exist

    Args:
        indexable (List[str]): A list of strings
        index (int): The index in the list or tuple

    Returns:
        str: The item at the given index, or a blank string
    """
    return item_at_index_or_none(indexable, index) or ""


def all_equal(*args):
    """
    Returns True if all of the provided args are equal to each other

    Args:
        *args (hashable): Arguments of any hashable type

    Returns:
        bool: True if all of the provided args are equal, or if the args are empty
    """
    return len(set(args)) <= 1


def all_unique(iterable):
    """
    Returns True if all of the provided args are equal to each other

    Args:
        iterable: An iterable of hashable items

    Returns:
        bool: True if all of the provided args are equal
    """
    return len(set(iterable)) == len(iterable)


def has_all_keys(dict_to_scan, keys):
    """
    Returns True if the given dict has all of the given keys

    Args:
        dict_to_scan (dict):
        keys (iterable of str): Iterable of keys to check for

    Returns:
        bool: True if the given dict has all of the given keys
    """
    return all(key in dict_to_scan for key in keys)


def group_into_dict(items, key_fn):
    """
    Groups items into a dictionary based on a key generated by a given function

    Examples:
        items = [
            Car(make="Honda", model="Civic"),
            Car(make="Honda", model="Accord"),
            Car(make="Ford", model="F150"),
            Car(make="Ford", model="Focus"),
        ]
        group_into_dict(items, lambda car: car.make) == {
            "Honda": [Car(make="Honda", model="Civic"), Car(make="Honda", model="Accord")],
            "Ford": [Car(make="Ford", model="F150"), Car(make="Ford", model="Focus")],
        }

    Args:
        items (Iterable[T]): An iterable of objects to group into a dictionary
        key_fn (Callable[[T], Any]): A function that will take an individual item and produce a dict key

    Returns:
        Dict[Any, T]: A dictionary with keys produced by the key function paired with a list of all the given
            items that produced that key.
    """
    sorted_items = sorted(items, key=key_fn)
    return {
        key: list(values_iter)
        for key, values_iter in itertools.groupby(sorted_items, key=key_fn)
    }


def get_error_response_summary(response):
    """
    Returns a summary of an error raised from a failed HTTP request using the requests library

    Args:
        response (requests.models.Response): The requests library response object

    Returns:
        str: A summary of the error response
    """
    # If the response is an HTML document, include the URL in the summary but not the raw HTML
    if "text/html" in response.headers.get("Content-Type", ""):
        summary_dict = {"url": response.url, "content": "(HTML body ignored)"}
    else:
        summary_dict = {"content": response.text}
    summary_dict_str = ", ".join([f"{k}: {v}" for k, v in summary_dict.items()])
    return f"Response - code: {response.status_code}, {summary_dict_str}"


def is_json_response(response):
    """
    Returns True if the given response object is JSON-parseable

    Args:
        response (requests.models.Response): The requests library response object

    Returns:
        bool: True if this response is JSON-parseable
    """
    return response.headers.get("Content-Type") == "application/json"


class ValidateOnSaveMixin(models.Model):
    """Mixin that calls field/model validation methods before saving a model object"""

    class Meta:
        abstract = True

    def save(
        self, force_insert=False, force_update=False, **kwargs
    ):  # pylint: disable=arguments-differ
        if not (force_insert or force_update):
            self.full_clean()
        super().save(force_insert=force_insert, force_update=force_update, **kwargs)


def remove_password_from_url(url):
    """
    Remove a password from a URL

    Args:
        url (str): A URL

    Returns:
        str: A URL without a password
    """
    pieces = urlparse(url)
    netloc = pieces.netloc
    userinfo, delimiter, hostinfo = netloc.rpartition("@")
    if delimiter:
        username, _, _ = userinfo.partition(":")
        rejoined_netloc = f"{username}{delimiter}{hostinfo}"
    else:
        rejoined_netloc = netloc

    return urlunparse(
        ParseResult(
            scheme=pieces.scheme,
            netloc=rejoined_netloc,
            path=pieces.path,
            params=pieces.params,
            query=pieces.query,
            fragment=pieces.fragment,
        )
    )


def format_price(amount):
    """
    Format a price in USD

    Args:
        amount (decimal.Decimal): A decimal value

    Returns:
        str: A currency string
    """
    return f"${amount:0,.2f}"


def make_csv_http_response(*, csv_rows, filename, instructions=None):
    """
    Create a HttpResponse for a CSV file with instructions at the start of the file.

    Args:
        csv_rows (iterable of dict): An iterable of dict, to be written to the CSV file
        filename (str): The filename to suggest for download
        instructions (iterable of str): An iterable of str instructions to be written to the CSV file, one per row

    Returns:
        django.http.response.HttpResponse: A HTTP response
    """
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    if instructions:
        writer = csv.writer(response)
        for instruction in instructions:
            writer.writerow([instruction])

    csv_rows = iter(csv_rows)
    try:
        first_row = next(csv_rows)
    except StopIteration:
        # Nothing to write
        return response

    writer = csv.DictWriter(response, fieldnames=list(first_row.keys()))
    writer.writeheader()
    writer.writerow(first_row)
    for row in csv_rows:
        writer.writerow(row)
    return response


def request_get_with_timeout_retry(url, retries):
    """
    Makes a GET request, and retries if the server responds with a 504 (timeout)

    Args:
        url (str): The URL of the Mailgun API endpoint
        retries (int): The number of times to retry the request

    Returns:
        response (requests.models.Response): The requests library response object

    Raises:
        requests.exceptions.HTTPError: Raised if the response has a status code indicating an error
    """
    resp = requests.get(url)
    # If there was a timeout (504), retry before giving up
    tries = 1
    while resp.status_code == status.HTTP_504_GATEWAY_TIMEOUT and tries < retries:
        tries += 1
        log.warning(
            "GET request timed out (%s). Retrying for attempt %d...", url, tries
        )
        resp = requests.get(url)
    resp.raise_for_status()
    return resp


def get_js_settings(request: HttpRequest):
    """
    Get the set of JS settings

    Args:
        request (django.http.HttpRequest) the current request

    Returns:
        dict: the settings object
    """
    return {
        "gtmTrackingID": settings.GTM_TRACKING_ID,
        "gaTrackingID": settings.GA_TRACKING_ID,
        "environment": settings.ENVIRONMENT,
        "public_path": public_path(request),
        "release_version": settings.VERSION,
        "recaptchaKey": settings.RECAPTCHA_SITE_KEY,
        "sentry_dsn": remove_password_from_url(settings.SENTRY_DSN),
        "support_email": settings.EMAIL_SUPPORT,
        "site_name": settings.SITE_NAME,
        "zendesk_config": {
            "help_widget_enabled": settings.ZENDESK_CONFIG.get("HELP_WIDGET_ENABLED"),
            "help_widget_key": settings.ZENDESK_CONFIG.get("HELP_WIDGET_KEY"),
        },
        "digital_credentials": settings.FEATURES.get("DIGITAL_CREDENTIALS", False),
    }
