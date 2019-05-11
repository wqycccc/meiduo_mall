
#导入cercly
from celery import Celery
import os

"""
Celery 将三者串联起来

生成者
    1.需要单独创建一个任务包sms,任务包中的py文件必须以 tasks.py作为我们的文件名
    2.生成者/任务 其本质就是 函数
    3.这个函数必须要经过 celery的实例对象的task装饰器装饰
    4.这个任务需要让celery自动检测
消息队列

消费者
    语法:celery -A proj worker -l info
    语法:celery -A celery实例对象的文件 worker -l info
    需要在虚拟环境中执行: celery -A celery_tasks.main
"""

# 让celery去加载可能用到的django的配置文件
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_mall.settings")
# 创建celery实例对象
# Celery(第一个参数main,习惯性将工程名作为他的参数,确保唯一性就可以)
app = Celery('celery_tasks')
# 在config.py配置文件
# 加载配置文件   config_from_object后面直接写配置文件的路径
app.config_from_object('celery_tasks.config')

# 让celery自动检测任务
app.autodiscover_tasks(['celery_tasks.sms'])


