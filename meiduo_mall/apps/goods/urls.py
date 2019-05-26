from  django.conf.urls import url
from apps.goods import views
urlpatterns = [
        # 商品列表
        url(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$',views.ListView.as_view(),name='list'),
        # 热销数据
        url(r'^hot/(?P<category_id>\d+)/$',views.HotView.as_view(),name='hot'),
        # 商品查询
        url(r'^detail/(?P<sku_id>\d+)/$', views.DetailView.as_view(), name='detail'),
        # 统计
        url(r'^detail/visit/(?P<category_id>\d+)/$', views.CategoryVisitView.as_view(), name='visit'),

]