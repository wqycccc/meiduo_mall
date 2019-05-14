from django.shortcuts import render

# Create your views here.
from django.views import View

from django.http import JsonResponse

from utils.response_code import RETCODE


class QQAuthURLView(View):

    def get(self,request):
        login_url = 'https://graph.qq.com/oauth2.0/show?which=Login&display=pc&response_type=code&client_id=101518219&redirect_uri=http://www.meiduo.site:8000/oauth_callback&state=test'

        return JsonResponse({'code':RETCODE.OK,'errmsg':'ok','login_url':login_url})
