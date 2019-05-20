
import json
import re
from django import http
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
import logging
from django_redis import get_redis_connection

from apps.users.utils import generic_verify_email_url, check_veryfy_email_token
from utils.response_code import RETCODE
from utils.views import LoginRequiredJSONMixin
from .models import User, Address

logger = logging.getLogger('django')
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
class RegisterView(View):
    # 提供注册界面
    def get(self,request):
        return render(request,'register.html')
    # 实现用户注册
    def post(self,request):
        # ①接收数据 request.POST
        data = request.POST
        # ②分别获取数据 username,password
        username = data.get('username')
        password = data.get('password')
        password2 = data.get('password2')
        mobile = data.get('mobile')
        allow = data.get('allow')
        sms_code_client = data.get('sms_code')

        # ③判断要求的数据是否齐全 [少参数就没有必要继续验证了]
        if not all([username, password, password2, mobile, allow]):
            return http.HttpResponseBadRequest('资料填写不完整')
        # ④验证用户名
        if not re.match(r'^[0-9a-zA-Z_-]{5,20}$',username):
            return http.HttpResponseBadRequest('用户名格式不对哦')
        # ⑤验证密码
        if not re.match(r'^[0-9a-zA-Z]{8,20}',password):
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
        # 判断用户提交的短信验证码是否与redis中的一致
        # 连接redis数据库
        redis_conn = get_redis_connection('code')
        # 获取redis中的短信验证码
        sms_code_server = redis_conn.get('sms_%s'%mobile)
        # 判断库中的短信验证码是否过期
        if sms_code_server is None:
            return http.HttpResponseBadRequest('短信验证码已经过期了')
        # 比对是否一致
        if sms_code_server.decode() != sms_code_client:
            return http.HttpResponseBadRequest('短信验证码不一致哦')
        # ⑨保存数据
        try:
            user = User.objects.create_user(username=username,
                                            password=password,
                                            mobile=mobile)
        except Exception as e:
            logger.error(e)
            return render(request, 'register.html', context={'register_errmsg': '创建用户失败'})

        """
            注册: 不同的产品需求是不一样的
                有的是 跳转到首页 v  默认登陆  应该有session信息
                有的是 跳转到登陆页面
            """

        # 设置登陆信息(session)
        from django.contrib.auth import login
        login(request,user)


        # ⑩跳转首页,返回相应
        return redirect(reverse('contents:index'))
        # return http.HttpResponse('ok')

    """
        1. 需求:
            当用户输入在输入用户名之后,光标失去焦点之后,前端应该发送一个ajax请求
            这个ajax请求 需要包含一个参数 username
        2.后台
            ① 确定请求方式和路由
                提取URL的特定部分，如/weather/beijing/2018，可以在服务器端的路由中用正则表达式截取；
                查询字符串（query string)，形如key1=value1&key2=value2

                GET  路由   usernames/(?P<username>[a-zA-Z0-9_]{5,20})/
                            register/count/?username=username
            ② 大体步骤写下来
                一.参数校验(已经在路由中做过了)
                二.根据用户名进行查询
                三.返回相应
        """
class RegisterUsernameCountView(View):
    # 判断用户名是否重复注册
    def get(self,request,username):
        # 一.参数校验(已经在路由中做过了)
        # if not re.match(r'')
        # 二.根据用户名进行查询
        # filter() 返回的是一个列表
        # User.objects.filter(username__exact=username)
        count = User.objects.filter(username=username).count()
        # 三.返回相应
        return http.JsonResponse({'count':count})
class RegisterMobileCountView(View):
        # 判断手机号是否重复注册
    def get(self,request, mobile):

        count = User.objects.filter(mobile = mobile).count()

        return http.JsonResponse({ 'count': count})

# Create your views here.
'''
用户名登录
  需求:
        当用户将用户名和密码填写完成之后,前端需要将用户名和密码发送给后端
    后台:
        请求方式和路由
            POST  login/
        大体步骤
            1.接收数据
            2.获取数据
            3.验证是否齐全(用户名和密码都要传递过来)
            4.判断用户名是否符合规则
            5.判断密码是否符合规则
            6.验证用户 用户名和密码是否正确
            7.保持会话
            8.返回相应
'''
# 用户名登录
class LoginView(View):
    def get(self,request):
        # 提供登录界面  展示
        return render(request,'login.html')
        pass
    def post(self,request):
        # 1.接收数据
        data = request.POST
        # 2.获取数据
        username = data.get('username')
        password = data.get('password')
        remembered = data.get('remembered')
        # 3.验证是否齐全(用户名和密码都要传递过来)
        if not all([username,password]):
            return http.HttpResponseBadRequest('缺少必传的参数哦')
        # 4.判断用户名是否符合规则
        if not re.match(r'^[0-9a-zA-Z_-]{5,20}$',username):
            return http.HttpResponseBadRequest('请输入正确的用户名或手机号哦')
        # 5.判断密码是否符合规则
        if not re.match(r'^[0-9a-zA-Z]{8,20}',password):
            return http.HttpResponseBadRequest('密码格式不对哦')
        # 6.验证用户
        user = authenticate(username= username,password = password)
        # 用户名和密码是否正确
        if user is None:
            return render(request,'login.html',{'login_error_message':'用户名或密码输入有误'})
        # 7.保持会话
        login(request, user)
        if remembered != 'on':
            # set_expiry 设置过期时间
            # 没有记住用户:浏览器关闭就过期
            request.session.set_expiry(0)
        else:
            # 记住用户:None默认表示两周以后过期
            request.session.set_expiry(None)
        #     next设置
        next = request.GET.get('next')
        if next:
            response = redirect(next)
        else:
            response = redirect(reverse('contents:index'))
            # 记住登录(记住密码那个按钮)/不记住登录
            #     返回响应之前设置cooking
        if remembered != 'on':
            # 获取cooking,不记住密码时
            response.set_cookie('username', user.username,)

        else:
            # 记住密码时
            response.set_cookie('username',user.username,max_age= 3600*24*14)

        # 8.返回相应
        return response
# 退出登录
from django.contrib.auth import logout
class LogoutView(View):
    def get(self,request):
        # 清理session
        logout(request)
        # 在退出登陆时,重定向到登录页/主页面都行
        response = redirect(reverse('users:login'))
#         在退出登录的时候,清除cookie中的username
        response.delete_cookie('username')

        return response


# 用户中心

# django自带了认证的一个方法，可以判断　用户是否登陆了(LoginRequiredMixin)
class UserInfoView(LoginRequiredMixin,View):
    # 提供个人信息页面
    def get(self,request):
        # 获取指定的数据组织上下文
        context = {
            'username':request.user.username,
            'mobile':request.user.mobile,
            'email':request.user.email,
            'email_active':request.user.email_active
        }
        # 跳转到用户中心界面
        return render(request,'user_center_info.html',context=context)

"""
需求(用户做了什么,我们要做什么[ 需要让前端提交什么,我们后端接收什么]):
    当用户在邮件输入框中,输入一个邮件之后,点击保存的时候,需要让前端将邮箱信息发送给后端
后端

    确定请求方式和路由:
        put         /emails/
    大体步骤:
        1.必须是登陆用户才可以更新邮箱信息
        2.接收用户提交的邮箱信息
        3.验证邮箱信息是否符合邮箱规则
        4.保存数据
        5.发送激活邮件
        6.返回相应


    GET     :       获取数据
    POST    :       新增数据
    PUT     :       更新数据/修改数据  put和post是类似的 我们的请求数据是请求的body中
    DELETE  :       删除数据
"""
# 添加邮箱
class EmailView(View):

    def put(self,request):
        # 1.必须是登陆用户才可以更新邮箱信息
        # 2.接收用户提交的邮箱信息
        # 2.1.获取body数据
        body = request.body
        # 2.2.body数据是bytes类型,进行类型转换
        body_str = body.decode()
        # 2.3.对字符串JSON,进行转换
        data = json.loads(body_str)

        email = data.get('email')
        # 3.验证邮箱信息是否符合邮箱规则
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',email):
            return http.JsonResponse({'code':RETCODE.PARAMERR,'errmsg':'参数错误'})

        # 4.更新数据(赋值)
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code':RETCODE.DBERR,"errmsg":'添加邮箱失败'})
        # 5.发送激活邮件

        from django.core.mail import send_mail
        # send_mail(subject, message, from_email, recipient_list,
        subject = '美多商城'
        message = ''
        from_email = '美多商城<13293833805@163.com>'
        recipient_list = [email]
        # html_message = "<a href='#'>hahahah</a>"
        verify_url = generic_verify_email_url(request.user.id)
        html_message ='<p>尊敬的用户您好！</p>' \
                   '<p>感谢您使用美多商城。</p>' \
                   '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                   '<p><a href="%s">%s<a></p>' % (email, verify_url, verify_url)
        # send_mail(subject=subject,
        #           message=message,
        #           from_email=from_email,
        #           recipient_list=recipient_list,
        #           html_message=html_message)
        from celery_tasks.email.tasks import send_verify_email
        send_verify_email.delay(
            subject = subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message
        )


        # 6.返回相应
        return http.JsonResponse({'code': RETCODE.OK, "errmsg": '添加邮箱成功'})
"""
需求:
    当用户点击激活连接的时候,可以展示该页面,同时,获取前端提交过来的token
后端:

    请求方式和路由:
        GET     emails/verification

    1.接收token
    2.验证token
    3.根据user_id查询用户信息
    4.改变用户信息
    5.返回相应(跳转到个人中心页面)
"""
class EmailVerifyView(View):

    def get(self,request):
        # 1.接收token
        token = request.GET.get('token')
        if token is None:
            return http.HttpResponseBadRequest('参数错误')
        # 2.验证token
        user_id = check_veryfy_email_token(token)
        if user_id is None:
            return http.HttpResponseBadRequest('参数错误')
        # 3.根据user_id查询用户信息
            # pk primary key 主键的意思
            # 如果我们不记得主键是哪个字段的时候,可以直接使用pk
            # 系统会自动使用主键
        try:
            # 4.改变用户信息
            user = User.objects.get(pk = user_id)
            if user is not None:
                user.email_active = True
                user.save()
        except User.DoesNotExist:
            return http.HttpResponseBadRequest('参数错误')
        # 5.返回响应
        return redirect(reverse('users:info'))


# 展示地址
class AddressView(LoginRequiredJSONMixin,View):
    def get(self,request):
        """提供收货地址界面"""
        """
           1.必须是登陆用户
           2.查询登陆用户的地址信息 [Address,Address]
           3.对列表数据进行转换为字典列表
           4.传递给模板
        """
        # 查询用户登录信息
        addresses = Address.objects.filter(user=request.user, is_deleted=False)

        address_dict_list = []
        for address in addresses:
            address_dict = {
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "province_id": address.province_id,
                "city": address.city.name,
                "city_id": address.city_id,
                "district": address.district.name,
                "district_id": address.district_id,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            }
            address_dict_list.append(address_dict)

        context = {
            'default_address_id': request.user.default_address_id,
            'addresses': address_dict_list,
        }

        return render(request, 'user_center_site.html', context)

# 新增地址
class CreateAddressView(LoginRequiredJSONMixin, View):
    """新增地址"""

    def post(self, request):
        """实现新增地址逻辑"""
        # 判断是否超过地址上限：最多20个
        # Address.objects.filter(user=request.user).count()
        count = Address.objects.filter(user=request.user, is_deleted=False).count()
        if count >= 20:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '超过地址数量上限'})

        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseBadRequest('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseBadRequest('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseBadRequest('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseBadRequest('参数email有误')

        # 保存地址信息
        try:
            address = Address.objects.create(
                user=request.user,
                title = receiver,
                receiver = receiver,
                province_id = province_id,
                city_id = city_id,
                district_id = district_id,
                place = place,
                mobile = mobile,
                tel = tel,
                email = email
            )

            # 设置默认地址
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '新增地址失败'})

        # 新增地址成功，将新增的地址响应给前端实现局部刷新
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应保存结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '新增地址成功', 'address':address_dict})

#     修改地址
class UpdateDestroyAddressView(LoginRequiredJSONMixin, View):
    def get(self,request):
        return render()
    """修改和删除地址"""

    def put(self, request, address_id):
        """修改地址"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseBadRequest('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseBadRequest('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseBadRequest('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseBadRequest('参数email有误')

        # 判断地址是否存在,并更新地址信息
        try:
            Address.objects.filter(id=address_id).update(
                user = request.user,
                title = receiver,
                receiver = receiver,
                province_id = province_id,
                city_id = city_id,
                district_id = district_id,
                place = place,
                mobile = mobile,
                tel = tel,
                email = email
            )
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '更新地址失败'})

        # 构造响应数据
        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应更新地址结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '更新地址成功', 'address': address_dict})

    def delete(self, request, address_id):
        """删除地址"""
        try:
            # 查询要删除的地址
            address = Address.objects.get(pk=address_id)

            # 将地址逻辑删除设置为True
            address.is_deleted = True
            address.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '删除地址失败'})

        # 响应删除地址结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除地址成功'})
#  设置默认地址
class DefaultAddressView(LoginRequiredJSONMixin, View):


    def put(self, request, address_id):
        """设置默认地址"""
        try:
            # 接收参数,查询地址
            address = Address.objects.get(id=address_id)

            # 设置地址为默认地址
            request.user.default_address = address
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置默认地址失败'})

        # 响应设置默认地址结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '设置默认地址成功'})

class UpdateTitleAddressView(LoginRequiredJSONMixin, View):
    """设置地址标题"""

    def put(self, request, address_id):
        """设置地址标题"""
        # 接收参数：地址标题
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')

        try:
            # 查询地址
            address = Address.objects.get(id=address_id)

            # 设置新的地址标题
            address.title = title
            address.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置地址标题失败'})

        # 4.响应删除地址结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '设置地址标题成功'})