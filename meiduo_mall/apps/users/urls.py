from django.conf.urls import url
from . import views


urlpatterns = [
    # 注册
    url(r'^register/$',views.RegisterView.as_view(),name='register'),
    url(r'^usernames/(?P<username>[a-zA-Z0-9_]{5,20})/$',views.RegisterUsernameCountView.as_view(),name='usernamecount'),
    url(r'^mobile/(?P<mobile>1[3-9]\d{9})/$',views.RegisterMobileCountView.as_view(),name='mobilecount'),

]