# portfolio_tracker_demo/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio.settings')

app = Celery('portfolio')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


app.conf.beat_schedule = {
    "update-coin-prices-every-10-minutes": {
        "task": "tracker.utils.update_coin_prices",  # path to your task
        "schedule": 600.0,  # 600 seconds = 10 minutes
    },
}


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')