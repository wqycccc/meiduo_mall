# Create your views here.
import base64
import json
import pickle

from django import http
from django.views import View
from django_redis import get_redis_connection

from apps.goods.models import SKU
from apps.views import logger
from utils.response_code import RETCODE


class CartsView(View):
    """
       添加购物车的思路

           需求:
               当用户点击加入购物车的时候,需要让前端收集  sku_id,count,selected(可以不提交默认是True)
               因为请求的时候会携带用户信息(如果用户登陆)
           后端:

               # 1.后端接收数据
               # 2.验证数据
               # 3.判断用户登陆状态
               # 4.登陆用户保存在redis
               #     4.1 连接redis
               #     4.2 hash
               #         set
               #     4.3 返回
               # 5.未登录用户保存在cookie中
               #     5.1 组织数据
               #     5.2 加密
               #     5.3 设置cookie
               #     5.4 返回相应

           路由和请求方式
               POST        carts
       """
    def post(self,request):
        # 1.后端接收数据
        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')
        count = data.get('count')
        selected = data.get('selected',True)
        # 2.验证数据
        if not all([sku_id,count]):
            return http.JsonResponse({'code':RETCODE.PARAMERR,'errmsg':'参数不全'})
        try:
            # 2.2 判断商品是否存在
            SKU.objects.get(pk=sku_id)
        except SKU.DoesNotExist:
            return http.JsonResponse({'code':RETCODE.NODATAERR,'errmsg':'没有此商品'})
        # 2.3 判断商品的个数是否为整形
        try:
            count = int(count)
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code':RETCODE.PARAMERR,'errmsg':'参数不全'})
        # 2.4 判断选中状态是否为bool值
        if not isinstance(selected,bool):
            return http.JsonResponse({'code':RETCODE.PARAMERR,'errmsg':'参数不全'})
        # 3.判断用户登陆状态
        user = request.user
        # 4.登陆用户保存在redis
        if user.is_authenticated:
            #     4.1 连接redis
            #     4.2 hash
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipline()
            pl.hincrby('cars_%s'%user.id,sku_id,count)
        #         set
            pl.sadd('selected_%s'%user.id,sku_id)
        #     执行
            pl.execute()
        #     4.3 返回
            return http.JsonResponse({'code':RETCODE.OK,'errmsg':'OK'})
        # 5.未登录用户保存在cookie中
        else:
        #     5.1 组织数据
            cart_str = request.COOKIES.get('carts')
        #     5.2 加密
            if cart_str:
                # 将cart_str转成bytes,再将bytes转成base64的bytes,最后将bytes转字典
                decode = base64.b64decode(cart_str)
                cookie_cart = pickle.loads(decode)
            else:
                cookie_cart = {}
        #         判断要加入购物车的商品是否已经在购物车中,如果相同就进行累加.
        if sku_id in cookie_cart:
            # 先把原数据获取到
            orginal_count = cookie_cart[sku_id]['count']
            # 再累加
            # count=count+orginal_count
            count += orginal_count

            # 再更新数据
        cookie_cart[sku_id] = {
            'count': count,
            'selected': selected
        }
        #     5.2 加密
        # 5.2.1 将字典转换为 bytes类型
        dumps = pickle.dumps(cookie_cart)
        # 5.2.2 将bytes类型进行base64加密
        cookie_data = base64.b64encode(dumps)
        #     5.3 设置cookie
        response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})

        response.set_cookie('carts', cookie_data.decode(), max_age=3600)
        #     5.4 返回相应

        return response

"""
    前端根据用户的状态,登陆就传递用户信息,不登陆就不传用户信息

    1.判断用户是否登陆
    2.登陆用户到redis中获取数据
        2.1 连接redis
        2.2 获取数据 hash   carts_userid: {sku_id:count}
                    set     selected: [sku_id,]
        2.3 获取所有的商品id
        2.4 根据商品id查询商品的详细信息 [sku,sku,sku]
        2.5 将对象转换为字典
    3.未登录用户到cookie中获取数据
        3.1 获取cookie中carts数据,同时进行判断
        3.2 carts: {sku_id:{count:xxx,selected:xxx}}
        3.3 获取所有商品的id
        3.4 根据商品id查询商品的详细信息 [sku,sku,sku]
        3.5 将对象转换为字典


    1.判断用户是否登陆
    2.登陆用户到redis中获取数据
        2.1 连接redis
        2.2 获取数据 hash   carts_userid: {sku_id:count}
                    set     selected: [sku_id,]

    3.未登录用户到cookie中获取数据
        3.1 获取cookie中carts数据,同时进行判断
        3.2 carts: {sku_id:{count:xxx,selected:xxx}}


    4 获取所有商品的id
    5 根据商品id查询商品的详细信息 [sku,sku,sku]
    6 将对象转换为字典
    7 返回相应
"""


