from django import http
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from apps.goods.models import SKU
from apps.users.models import Address
from apps.views import logger


class PlaceOrderView(LoginRequiredMixin,View):

    def get(self,request):
        # 获取用户信息
        user = request.user
        # 查询地址信息
        try:
            addresses = Address.objects.filter(user =user,is_deleted=False)
        except Exception as e:
            logger.error(e)
            return http.HttpResponseBadRequest('未找到数据')
        # 链接redis
        redis_conn = get_redis_connection('carts')
        # hash
        sku_id_count = redis_conn.hgetall('carts_%s'%user.id)
        # set
        ids = redis_conn.smembers('selected_%s'%user.id)
        # 取出的商品是base类型,要进行强制转换为int类型
        selected_carts = {}
        for id in ids:
            selected_carts[int(id)] = int(sku_id_count[id])
        # 获取商品的id, 根据商品id查询商品信息[sku, sku]
        ids = selected_carts.keys()
        # pk__in 表示查询在ids中的数据
        skus = SKU.objects.filter(pk__in=ids)
        # 对象商品列表进行遍历
        total_count =  0#总数量
        # 导入货比类型
        from decimal import Decimal
        total_amount = Decimal('0')#总金额
        for sku in skus:
            # 8.遍历的过程中 对sku添加数量和对应商品的总金额
            sku.count = selected_carts[sku.id]  # 数量小计
            sku.amount = sku.count * sku.price  # 金额小计
            #     也去计算当前订单的总数量和总金额
            total_count += sku.count
            total_amount += sku.amount

            # 再添加一个运费信息
        freight = Decimal('10.00')

        context = {
            'addresses': addresses,
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
            'freight': freight,
            'payment_amount': total_amount + freight
        }

        return render(request, 'place_order.html', context=context)