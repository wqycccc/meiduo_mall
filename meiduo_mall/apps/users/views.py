import re
from django import http
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View

from apps.users.models import User
import logging

logger = logging.getLogger('django')

class RegisterView(View):
    # 提供注册界面
    def get(self,request):
        return render(request,'register.html')
    # 实现用户注册
    def post(self,request):
        pass
        # ①接收数据 request.POST
        data = request.POST
        # ②分别获取数据 username,password
        username = data.get('username')
        password = data.get('password')
        password2 = data.get('password2')
        mobile = data.get('mobile')
        allow = data.get('allow')

        # ③判断要求的数据是否齐全 [少参数就没有必要继续验证了]
        if not all([username, password, password2, mobile, allow]):
            return http.HttpResponseBadRequest('资料填写不完整')
        # ④验证用户名
        if re.match(r'^[0-9a-zA-Z_-]{5,20}$',username):
            return http.HttpResponseBadRequest('用户名格式不对哦')
        # ⑤验证密码
        if re.match(r'^[0-9a-zA-Z]{8,20}',password):
            return http.HttpResponseBadRequest('密码格式不对哦')
        # ⑥验证确认密码
        if password2 != password:
            return http.HttpResponseBadRequest('两次密码不一样呢')
        # ⑦验证手机号
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return http.HttpResponseBadRequest('手机号码格式不对哦')
        # ⑧验证是否同意协议
        if allow != 'on':
            return http.HttpResponseBadRequest('您还没有同意协议呢')
        # ⑨保存数据
        try:
            user = User.objects.create_user(
            username = username,
            password = password,
            mobile = mobile
            )
        except Exception as e:
            logger.error(e)
            return render(request, 'register.html', context={'register_errmsg': '创建用户失败'})

        # ⑩跳转首页,返回相应
        return redirect(reverse('contents:index'))
        # return http.HttpResponse('ok')

# Create your views here.
"""
功能点如何分析:
    1.需要依靠经验
    2.看其他网站的类似功能
注册页面的功能点:
    1.用户名:
        不能重复
        有长度限制
    2.密码:
        有长度限制
        数字和字母
    3.确认密码:
        需要和密码一致
    4.手机号
        符合要求
        不能重复
    5.图片验证码
        后台实现
        作用: 区分人和计算机的
        服务于: 短信验证码(发送短信花钱)
    6.短信验证码
        后台实现
        发送短信前先验证 图片验证码
    7.用户点击注册按钮的时候
        必须保存: 用户名,密码和手机号
        原因: 我们在登陆的时候需要使用这三个字段
    8.同意按钮
        需要点击同意

需求分析分析出来之后:
    1.先分析模型
    2.再众多功能中,找一个功能来入手,不要考虑很多的功能点(哪个简单,会哪个就先做哪个)
    3.把最难的功能放在最后
"""

"""
具体需求:
    当用户点击注册按钮的时候,需要让前端将 用户名,密码,确认密码,手机号,是否同意协议 提交给后台

后台:
    1.先确定路由和提交方式: POST      register/

        提取URL的特定部分，如/weather/beijing/2018，可以在服务器端的路由中用正则表达式截取；
        register/itcast/1234567890/1234567890/18212345678/on/

        查询字符串（query string)，形如key1=value1&key2=value2；
        register?itcast/1234567890/1234567890/18212345678/on/

        请求体（body）中发送的数据，比如表单数据、json、xml

    2.根据需求把大体步骤写下来[后端不相信前端提交的任何数据]
        ①接收数据
        ②验证数据
        ③保存数据
        ④返回相应

    3.具体实现的思路(步骤)
        ①接收数据 request.POST
        ②分别获取数据 username,password
        ③判断要求的数据是否齐全 [少参数就没有必要继续验证了]
        ④验证用户名
        ⑤验证密码
        ⑥验证确认密码
        ⑦验证手机号
        ⑧验证是否同意协议
        ⑨保存数据
        ⑩跳转首页,返回相应

    4.添加断点
        在函数的入库处,添加
     作用:
        ① 查看程序运行过程中的变量数据
        ② 一步一步的来梳理业务逻辑
        ③ 当我们验证某一行代码的时候可以添加断点
"""
