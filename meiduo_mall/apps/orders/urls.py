from django.conf.urls import url

from apps.orders import views

urlpatterns=[
    url(r'^orders/settlement/$',views.PlaceOrderView.as_view(),name='placeorder'),
    url(r'^orders/commit/$',views.OrderCommitView.as_view(),name='commit'),
]