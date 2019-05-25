from  django.conf.urls import url
from apps.carts import views
urlpatterns = [
        url(r'^carts/$',views.CartsView.as_view(),name='info'),
        url(r'^carts/selection/$',views.CartSelectAllView.as_view(),name='cartselectall')
]