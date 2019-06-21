"""Courseware tasks"""
from mitxpro.celery import app
from courseware.api import create_user
from users.api import get_user_by_id


@app.task(acks_late=True)
def create_user_from_id(user_id):
    """Loads user by id and calls the API method to create the user in edX"""
    user = get_user_by_id(user_id)
    create_user(user)


# To be removed after this has been deployed in all envs
@app.task()
def create_edx_user_from_id(user_id):
    """Backwards-compatibility for celery to forward to the new task name"""
    create_user_from_id.delay(user_id)
