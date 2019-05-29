import json

from decimal import Decimal
from django import http
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from apps.goods.models import SKU
from apps.orders.models import OrderInfo, OrderGoods
from apps.users.models import Address
from apps.views import logger
from utils.response_code import RETCODE
from utils.views import LoginRequiredJSONMixin


class PlaceOrderView(LoginRequiredMixin, View):
    def get(self, request):
        # 获取用户信息
        user = request.user
        # 查询地址信息
        try:
            addresses = Address.objects.filter(user=user, is_deleted=False)
        except Exception as e:
            logger.error(e)
            return http.HttpResponseBadRequest('未找到数据')
        # 链接redis
        redis_conn = get_redis_connection('carts')
        # hash
        sku_id_count = redis_conn.hgetall('carts_%s' % user.id)
        # set
        ids = redis_conn.smembers('selected_%s' % user.id)
        # 取出的商品是base类型,要进行强制转换为int类型
        selected_carts = {}
        for id in ids:
            selected_carts[int(id)] = int(sku_id_count[id])
        # 获取商品的id, 根据商品id查询商品信息[sku, sku]
        ids = selected_carts.keys()
        # pk__in 表示查询在ids中的数据
        skus = SKU.objects.filter(pk__in=ids)
        # 对象商品列表进行遍历
        total_count = 0  # 总数量
        # 导入货比类型
        from decimal import Decimal
        total_amount = Decimal('0')  # 总金额
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


# 保存订单基本信息
class OrderCommitView(LoginRequiredJSONMixin, View):
    """
    生成订单信息需要涉及到订单基本信息和订单商品信息,因为 订单基本信息订单商品信息
    是1对n,所以先生成1(订单基本信息)的数据,再生成订单商品

    1. 生成订单基本信息
        1.1 必须是登陆用户才可以访问.获取用户信息
        1.2 获取提交的地址信息
        1.3 获取提交的支付方式
        1.4 手动生成一个订单id 年月日时分秒+9位用户id
        1.5 运费,总金额和总数量(初始化为0)
        1.6 订单状态(由支付方式决定)
    2. 生成订单商品信息
        2.1 连接redis.获取redis中的数据
        2.2 获取选中商品的id [1,2,3]
        2.3 对id进行遍历
            2.4 查询商品
            2.5 库存量的判断
            2.6 修改商品的库存和销量
            2.7 累加总数量和总金额
            2.8 保存订单商品信息
            2.9 保存订单的总数量和总金额

    """

    def post(self, request):
        # 1.生成订单基本信息
        #     1.1 必须是登陆用户才可以访问.获取用户信息
        user = request.user
        #     1.2 获取提交的地址信息
        data = json.loads(request.body.decode())
        address_id = data.get('address_id')
        try:
            address = Address.objects.get(pk=address_id)
        except Address.DoesNotExist:
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数错误'})
        # 1.3 获取提交的支付方式
        pay_method = data.get('pay_method')
        # 对支付方式进行一个判断
        # 模型类里定义了支付方式
        if not pay_method in [OrderInfo.PAY_METHODS_ENUM['CASH'], OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数错误'})
        # 1.4 手动生成一个订单id 年月日时分秒+9位用户id
        # Y 年
        # m 月
        # d 日
        # H 时
        # M 分
        # S 秒
        from django.utils import timezone
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + '%09d' % user.id
        #     1.5 运费,总金额和总数量(初始化为0)
        freight = Decimal('10.00')  # 运费
        total_amount = Decimal('0')  # 总金额
        total_count = 0
        #     1.6 订单状态(由支付方式决定)
        if pay_method == OrderInfo.PAY_METHODS_ENUM['CASH']:
            # 货到付款
            status = OrderInfo.ORDER_STATUS_ENUM['UNSEND']
        else:
            status = OrderInfo.ORDER_STATUS_ENUM['UNPAID']
        from django.db import transaction
        with transaction.atomic():

            # 1.创建事务回滚的点
            save_point = transaction.savepoint()
            #     保存订单基本信息
            order = OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                address=address,
                total_count=total_count,
                total_amount=total_amount,
                freight=freight,
                pay_method=pay_method,
                status=status
            )

            # 2. 生成订单商品信息
            #     2.1 连接redis.获取redis中的数据
            redis_conn = get_redis_connection('carts')
            id_count = redis_conn.hgetall('carts_%s' % user.id)
            selected_ids = redis_conn.smembers('selected_%s' % user.id)

            selected_carts = {}
            for id in selected_ids:
                selected_carts[int(id)] = int(id_count[id])
            # 2.2 获取选中商品的id [1,2,3]
            ids = selected_carts.keys()
            #     2.3 对id进行遍历
            for id in ids:
                #         2.4 查询商品
                sku = SKU.objects.get(pk=id)
                #         2.5 库存量的判断
                count = selected_carts[sku.id]
                if sku.stock < count:
                    # 出现问题进行回滚
                    transaction.savepoint_rollback(save_point)
                    # 说明库存不足
                    return http.JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '库存不足'})

                    # 2.6 修改商品的库存和销量
                # sku.stock -= count
                # sku.sales += count
                # sku.save()
                import time
                time.sleep(5)
                # 2.6.1  乐观锁
                # 先获取之前的库存
                old_stock = sku.stock
                new_stock = sku.stock - count  # 新库存
                new_sales = sku.sales + count  #新销量
                rect = SKU.objects.filter(id = id,stock=old_stock).update(
                    stock = new_stock,
                    sales = new_sales
                )
                if rect == 0:
                    # 下单失败
                    transaction.savepoint_rollback(save_point)
                    return http.JsonResponse({'code':RETCODE.STOCKERR,'errmsg':'下单失败'})
                else:
                    print('下单成功')
                #         2.7 累加总数量和总金额
                #         2.8 保存订单商品信息
                order = OrderGoods.objects.create(
                    order=order,
                    sku=sku,
                    count=count,
                    price=sku.price,
                )
                #      2.9 保存订单的总数量和总金额
            order.save()
            # 3.提交
            transaction.savepoint_commit(save_point)
            # 返回响应
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '下单成功', 'order': order.order_id})
