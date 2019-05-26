import re
from django import http
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.http import JsonResponse
from django_redis import get_redis_connection

from apps.carts.utils import merge_cart_cookie_to_redis
from apps.oauth.models import OAuthQQUser
from apps.oauth.utils import generic_openid_token, check_openid_token
from apps.users.models import User
from apps.users.views import logger
from meiduo_mall import settings
from utils.response_code import RETCODE
from QQLoginTool.QQtool import OAuthQQ
#
class QQAuthURLView(View):

    def get(self,request):
        # 创建实例 (QQLoginTool)
        state = request.GET.get('next')
        qq = OAuthQQ(
            client_id= settings.QQ_CLIENT_ID,
            redirect_uri=settings.QQ_REDIRECT_URI,
            client_secret=settings.QQ_CLIENT_SECRET,
            state= state
        )
        # 调用实例方法
        login_url = qq.get_qq_url()
        # login_url = 'https://graph.qq.com/oauth2.0/show?which=Login&display=pc&response_type=code&client_id=101518219&redirect_uri=http://www.meiduo.site:8000/oauth_callback&state=test'

        return JsonResponse({'code':RETCODE.OK,'errmsg':'ok','login_url':login_url})
class QQAuthUserView(View):
    def get(self,request):
        #  1.获取code(是用户同意登陆之后,qq服务器返回给我们的)
        # 2.通过code换取token(我们需要把code以及我们创建应用的serect 一并给qq服务器,qq服务器会认证
        #                     认证没有问题会返回给我们token)
        # 1.获取code
        code = request.GET.get('code')
        if code is None:
            return http.HttpResponseBadRequest('参数有误')
        # 2.通过code换取token
        qq = OAuthQQ(
            client_id= settings.QQ_CLIENT_ID,
            redirect_uri=settings.QQ_REDIRECT_URI,
            client_secret=settings.QQ_CLIENT_SECRET,)
        token = qq.get_access_token(code)
        # '3C78606DA09521FBE58A0AB2FB6F5D45'
        # 3.根据token换取openid
        openid = qq.get_open_id(token)
        # callback({"client_id": "101518219", "openid": "549CF9E63A6A29C65580E4B630878B14"});
        # https://graph.qq.com/oauth2.0/me?access_token=3C78606DA09521FBE58A0AB2FB6F5D45
        # 4.判断openid所对应的user信息是否存在
        try:
            qquser = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 5.如果不存在就进行绑定(相当于没绑定)
            openid_token = generic_openid_token(openid)
            return render(request,'oauth_callback.html',context={'openid':openid_token})
        else:
            # 6.如果存在就进行登录跳转
            user =qquser.user
            #保持登录状态
            login(request,user)
            # next的设置
            next = request.GET.get('state')
            if next:
                response = redirect(next)
            else:
                response= redirect(reverse('contents:index'))
            response.set_cookie('username',user.username,max_age=14*24*3600)
            # 跳转
            return response
        return render(request, 'oauth_callback.html')

    def post(self,request):
        """
            需求:
             当用户点击保存的时候,需要让前端将 openid_token,mobile,password,sms_code 提交给后端
             后端:
             大体步骤:
             1.接收数据
             2.验证数据
                手机号
                密码
                短信验证码
                openid_token
            3.绑定信息
                openid      是通过对oepnid_token的解密来获取
                user        需要根据 手机号进行判断
                                如果手机号注册,已经有user信息
                                如果没有注册,我们就创建一个user用户
            4.登陆状态保持
            5.cookie
            6.返回相应
        """
        #1.接受数据
        data = request.POST
        mobile = data.get('mobile')
        password = data.get('password')
        sms_code_client = data.get('sms_code')
        openid_token = data.get('openid')
        if not all([mobile,password,sms_code_client,openid_token]):
            return http.HttpResponseBadRequest('缺少必传的参数哦')
        # 2.1判断手机号是否符合规则
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return http.HttpResponseBadRequest('手机号不满足条件')
        # 2.2验证密码是否符合规则
        if not re.match(r'^[0-9A-Za-z]{8,20}$',password):
            return http.HttpResponseBadRequest('密码格式不正确')
        # 连接redis数据库
        # redis_conn = get_redis_connection('code')
        # # 获取redis中的短信验证码
        # sms_code_server = redis_conn.get('sms_%s' % mobile)
        # 判断库中的短信验证码是否过期
        redis_conn = get_redis_connection('code')
        sms_code_server = redis_conn.get('sms_%s'%mobile)
        if sms_code_server is None:
            return http.HttpResponseBadRequest('短信验证码已经过期了')
        # 比对是否一致
        if sms_code_server.decode() != sms_code_client:
            return http.HttpResponseBadRequest('短信验证码不一致哦')
        # 对openid进行解密
        openid = check_openid_token(openid_token)
        # 如果返回一个none,给出错误信息
        if openid is None:
            return http.HttpResponseBadRequest('openid错误')

        # 3.绑定信息(绑定openid和用户信息user)
        try:
            user =User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 用户不存在的话,新建用户
            user = User.objects._create_user(username=mobile,
                                             password=password,
                                             mobile=mobile)
        else:
            # 如果用户存在,再次检查用户密码
            if not user.check_password(password):
                return http.HttpResponseBadRequest('密码错误')
#             将用户绑定openid
        try:
            OAuthQQUser.objects.create(openid=openid,
                                       user=user)
        except Exception as e:
            logger.error(e)
            return http.HttpResponseBadRequest('数据库错误')
#       4.登录状态保持
        login(request,user)
#        5.设置cooking
        response=redirect(reverse('contents:index'))
        response.set_cookie('username',user.username,max_age=14*24*3600)
#         在这里合并
        response = merge_cart_cookie_to_redis(request=request, user=user, response=response)
#         6.返回响应
        return response




