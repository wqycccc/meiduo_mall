from django.conf.urls import url
from . import views


urlpatterns = [
    # 注册
    url(r'^register/$',views.RegisterView.as_view(),name='register'),
    # 判断用户名是否重复注册
    url(r'^usernames/(?P<username>[a-zA-Z0-9_]{5,20})/$',views.RegisterUsernameCountView.as_view(),name='usernamecount'),
    # 判断手机号是否重复注册
    url(r'^mobile/(?P<mobile>1[3-9]\d{9})/$',views.RegisterMobileCountView.as_view(),name='mobilecount'),
    # 登录
    url(r'^login/$',views.LoginView.as_view(),name='login'),
    # 退出登录
    url(r'^logout/$',views.LogoutView.as_view(),name='logout'),
    # 判断用户是否登录
    url(r'^info/$',views.UserInfoView.as_view(),name='info'),
    #添加邮箱
    url(r'^emails/$',views.EmailView.as_view(),name='email'),
    # 解密邮件
    url(r'^emails/verification/$',views.EmailVerifyView.as_view(),name='emailverify'),
    # 收件地址视图
    url(r'^address/$',views.AddressView.as_view(),name='address'),
    #新增地址
    url(r'^addresses/create/$',views.CreateAddressView.as_view(),name='createaddress'),
#     修改地址
    url(r'^addresses/(?P<address_id>\d+)/$',views.UpdateDestroyAddressView.as_view(),name='updateaddress'),
    # 设置默认地址
    url(r'^addresses/(?P<address_id>\d+)/default/$',views.DefaultAddressView.as_view(),name='defaultaddress'),
    # 修改地址标题
    url(r'^addresses/(?P<address_id>\d+)/title/$',views.UpdateTitleAddressView.as_view(),name='titleaddress'),

]