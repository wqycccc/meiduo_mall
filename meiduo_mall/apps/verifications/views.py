from django.shortcuts import render
from django import http
from django.views import View
# Create your views here.
from django_redis import get_redis_connection
from apps.verifications.constant import SMS_CODE_EXPIRE_TIME,YUNTONGXUN_EXPIRE_TIME
from celery_tasks.sms.tasks import send_sms_code
from libs.captcha.captcha import captcha
from libs.yuntongxun.sms import CCP
from utils.response_code import RETCODE


class ImageCodeView(View):
    # 图片验证码
    def get(self,request, uuid):
        # 生成图片验证码
        # text是图片验证码的内容(数字)
        # image是图片验证码的二进制图片
        text, image = captcha.generate_captcha()
        # 保存图片验证码
        redis_conn = get_redis_connection('code')
        # (键,过期时间,值)
        redis_conn.setex('img_%s'% uuid,120, text)

        # 响应图片验证码
        return http.HttpResponse(image, content_type='image/jpeg')
import logging

logger = logging.getLogger('django')

class SMSCodeView(View):
     # 短信验证码
    def get(self,request, mobile):
        # 后端接收数据
        parame = request.GET
        # 图片验证码的uuid
        uuid = parame.get('image_code_id')
        # 用户输入的图片验证码内容
        text_client = parame.get('image_code')

        # 连接redis
        # 在操作外界数据时,因为不确定会发生什么,所以这类型数据都要用捕获异常
        try:
            redis_conn = get_redis_connection('code')
            # 根据uuid获取redis中验证码的数据
            text_server = redis_conn.get('img_%s'%uuid)
            # 如果验证码过期
            if text_server is None:
                return http.HttpResponseBadRequest('图片验证码过期了')
            # 对比数据库中的图片验证码
            if text_server.decode().lower() != text_client.lower():
                return http.HttpResponseBadRequest('图片验证码不一致')
            # 删除redis中已经获取的图片验证码内容
            redis_conn.delete("img%s"%uuid)
        except Exception as e:
            logger.error(e)
            return http.HttpResponseBadRequest("数据库链接问题")

        # 先看数据库中有没有获取到
        send_flag = redis_conn.get('send_flag%s'%mobile)
        if send_flag is not None:
            return http.HttpResponseBadRequest("等下在操作哦,有点太频繁了")


        from random import randint
        # 生成短信验证码
        sms_code = '%06d'%randint(0,999999)
        # .info会将生成的短信验证码显示到控制台
        logger.info(sms_code)
        # 保存短信验证码
        # redis_conn.setex('sms_%s'%mobile, SMS_CODE_EXPIRE_TIME, sms_code)
        # 通过redis连接,创建管道实例对象
        pl = redis_conn.pipeline()
        # 将redis实例放到管道中
        pl.setex('sms%s'%mobile,SMS_CODE_EXPIRE_TIME,sms_code)
        pl.setex('send_flag_%s' % mobile, 60, 1)

        # 发送短信验证码
        # CCP().send_template_sms(mobile,[sms_code,YUNTONGXUN_EXPIRE_TIME],1)
        send_sms_code.delay(mobile,sms_code)
        return http.JsonResponse({ 'code':RETCODE.OK })

