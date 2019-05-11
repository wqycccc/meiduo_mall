from apps.verifications.constant import YUNTONGXUN_EXPIRE_TIME
from celery_tasks.main import app
from libs.yuntongxun.sms import CCP


# 这个函数必须要经过 celery的实例对象的task装饰器装饰
@app.task
def send_sms_code(mobile,sms_code):
    CCP().send_template_sms(mobile, [sms_code, YUNTONGXUN_EXPIRE_TIME], 1)