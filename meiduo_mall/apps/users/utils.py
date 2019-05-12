import re
from django.contrib.auth.backends import ModelBackend

from apps.users.models import User

"""
django库中没有手机号登录,所以需要自定义一个方法,并且继承库中的方法
1. 我们需要的需求是 用户名或手机号登陆,系统默认提供的是 用户名登陆
    当系统的类/方法 不能我们我们需求的时候,我们就继承重写
2. 代码的抽取/封装(思想)

    ① 为什么要抽取代码
        减低代码的耦合度
        代码的复用(多个地方使用,如果有需求的变更,我们只该一个地方)
    ② 我什么时候抽取代码
        某些行(1,n行)代码实现了一个小的功能
        当你复制重复(第二个复制的)代码的时候就要考虑是否抽取
    ③ 如何实现呢?
        先定义一个函数(方法),函数名无所谓,也不用关系参数
        将要抽取的代码拷贝到这个函数中,哪里有问题改哪里,没有的变量以参数的形式传递
        验证,验证没有问题之后,再将原代码删除
"""
def get_user_by_account(account):
    try:
        if re.match('^1[3-9]\d{9}$',account):
            user = User.objects.get(mobile=account)
        else:
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    else:
        return user


    pass

class UsernameMobileAuthBackend(ModelBackend):
    # 自定义用户认证后端(手机号登录)
    def authenticate(self, request, username=None, password=None, **kwargs):

        user = get_user_by_account(username)
        if user and user.check_password(password):
            return user