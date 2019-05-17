from django import http
from django.contrib.auth.mixins import LoginRequiredMixin
# 重写handle_no_permission方法 ,让他返回一个JSON数据
from utils.response_code import RETCODE


class LoginRequiredJSONMixin(LoginRequiredMixin):
    def handle_no_permission(self):
        return http.JsonResponse({'code':RETCODE.SESSIONERR,"errmsg":'未登录'})
