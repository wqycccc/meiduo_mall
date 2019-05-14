from django.shortcuts import render

# Create your views here.
from django.views import View

from django.http import JsonResponse
from meiduo_mall import settings
from utils.response_code import RETCODE
from QQLoginTool.QQtool import OAuthQQ

class QQAuthURLView(View):

    def get(self,request):
        # 创建实例
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
