from django.core.mail import send_mail

from apps.views import logger
from celery_tasks.main import app

@app.task(bind = True,default_retry_delay=3,name='send_email')
def send_verify_email(self,subject,message,from_email,recipient_list,html_message):
    try:
        send_mail(subject=subject,
                  message=message,
                  from_email=from_email,
                  recipient_list=recipient_list,
                  html_message=html_message)
    except Exception as exc:
        logger.error(exc)
        raise self.retry(exc=exc,max_retries=3)
