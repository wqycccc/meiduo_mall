from apps.verifications.constant import YUNTONGXUN_EXPIRE_TIME
from apps.views import logger
from celery_tasks.main import app
from libs.yuntongxun.sms import CCP

# bind=True 是表示把任务自己传递过去,这样我们就可以在任务的第一个参数中,传递self
# # 函数中的 self 就是 Task(任务)本身
# 这个函数必须要经过 celery的实例对象的task装饰器装饰
# default_retry_delay 任务重试时间
@app.task(bind = True,default_retry_delay=3,name='send_sms')
def send_sms_code( self,mobile, sms_code):
    try:
        result = CCP().send_template_sms(mobile, [sms_code, YUNTONGXUN_EXPIRE_TIME], 1)
        if result != 0:
            raise Exception('下单失败')
    except Exception as exc:
        logger.error(exc)
        raise self.retry(exc=exc,max_retries=3)