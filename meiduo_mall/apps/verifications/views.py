from django.shortcuts import render
from django import http
from django.views import View
# Create your views here.
from django_redis import get_redis_connection

from libs.captcha.captcha import captcha
from libs.yuntongxun.sms import CCP


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

class SMSCodeView(View):
     # 短信验证码
    def get(self,request, mobile):
        # 后端接收数据
        parame = request.GET
        # 图片验证码的uuid
        uuid = parame.get('image_code_id')
        # 用户输入的图片验证码内容
        text_client = parame.get('image_code')
        # 链接redis
        redis_conn = get_redis_connection('code')
        # 根据uuid获取redis中验证码的数据
        text_server = redis_conn.get('img_%s'%uuid)
        # 如果验证码过期
        if text_server is None:
            return http.HttpResponseBadRequest('图片验证码过期了')
        # 对比数据库中的图片验证码
        if text_server != text_client:
            return http.HttpResponseBadRequest('图片验证码不一致')

        from random import randint
        # 生成短信验证码
        sms_code = '%06d'%randint(0,999999)
        # 保存短信验证码
        redis_conn.setex('sms_%s'%mobile, 500, sms_code)
        # 发送短信验证码
        CCP().send_template_sms(mobile,[sms_code,5],1)
        return http.JsonResponse({ 'code':200 })


        pass

