from django.conf.urls import url
from . import views
urlpatterns = [
    # qqurl
    url(r'^qq/login/$',views.QQAuthURLView.as_view(),name='qqurl'),
    #qquser (oauth认证)
    url(r'oauth_callback/$',views.QQAuthUserView.as_view(),name='qqusers'),
]