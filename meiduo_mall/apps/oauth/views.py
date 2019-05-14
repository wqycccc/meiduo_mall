from django import http
from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from meiduo_mall import settings
from utils.response_code import RETCODE
from QQLoginTool.QQtool import OAuthQQ
#
class QQAuthURLView(View):

    def get(self,request):
        # 创建实例 (QQLoginTool)
        state = 'test'
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

        return render(request,'oauth_callback.html')