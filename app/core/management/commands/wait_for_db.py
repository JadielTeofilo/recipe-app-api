import time

from django.db import connections
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        db_con = None
        while not db_con:
            try:
                db_con = connections['default']
            except OperationalError:
                time.sleep(1)
