# Create your views here.
import base64
import json
import pickle

from django import http
from django.shortcuts import render
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
            pl = redis_conn.pipeline()
            pl.hincrby('carts_%s'%user.id,sku_id,count)
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
    def get(self,request):
        # 1.判断用户是否登陆
        user = request.user
        if user.is_authenticated:
        # 2.登陆用户到redis中获取数据
        #     2.1 连接redis
            redis_conn = get_redis_connection('carts')
            #     2.2 获取数据 hash   carts_userid: {sku_id:count}
            sku_id_count = redis_conn.hgetall('carts_%s'%user.id)
            #                 set     selected: [sku_id,]
            selected_id = redis_conn.smembers('selected_%s'%user.id)
        #     将redis中的数据构造成和cookie中的格式一致,方便合并查询
            cookie_cart = {}
            for sku_id, count in sku_id_count.items():
                if sku_id in selected_id:
                    selected = True
                else:
                    selected = False
                cookie_cart[int(sku_id)] = {
                    'count':int(count),
                    'selected':selected
                }

        else:
        # 3.未登录用户到cookie中获取数据
            carts = request.COOKIES.get('carts')
            # 3.1 获取cookie中carts数据,同时进行判断
            if carts is not None:
            #     有数据
                decode = base64.b64decode(carts)
                cookie_cart = pickle.loads(decode)
            else:
                cookie_cart = {}
        #     3.2 carts: {sku_id:{count:xxx,selected:xxx}}
        ids = cookie_cart.keys()
        # 4 获取所有商品的id
        skus = []
        for id in ids:
            sku = SKU.objects.get(pk=id)
            # 5 根据商品id查询商品的详细信息 [sku,sku,sku]
            # 6 将对象转换为字典
            skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': cookie_cart.get(sku.id).get('count'),
                'selected': str(cookie_cart.get(sku.id).get('selected')),  # 将True，转'True'，方便json解析
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),  # 从Decimal('10.2')中取出'10.2'，方便json解析 (货比类型)
                'amount': str(sku.price * cookie_cart.get(sku.id).get('count')),
            })
        # 7 返回相应
        context = {
            'cart_skus': skus,
        }

        # 渲染购物车页面
        return render(request, 'cart.html', context)


    def put(self,request):
        # 1.接受数据
        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')
        count = data.get('count')
        selected = data.get('selected')
        # 2.验证数据
        # 2.1验证商品id 数量是否齐全
        if not all([sku_id,count,selected]):
            return http.JsonResponse({'code':RETCODE.PARAMERR,'errmsg':'参数不全'})
        # 2.2判断商品是否存在
        try:
            sku = SKU.objects.get(pk = sku_id)
        except SKU.DoesNotExist:
            return http.JsonResponse({'code':RETCODE.NODATAERR,'errmsg':'没有此商品'})
        # 判断数量是否为整数
        try:
            count = int(count)
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code':RETCODE.PARAMERR,'errmsg':'参数错误'})
        # 判断是否为选中状态
        if not isinstance(selected,bool):
            return http.JsonResponse({'code':RETCODE.PARAMERR,'errmsg':'参数错误'})
        # 判断用户登录状态
        user = request.user
        if user.is_authenticated:
            # 登录用户保存在redis
            redis_conn = get_redis_connection('carts')
        #     跟新数据hash
            redis_conn.hset('carts_%s'%user.id,sku_id,count)
        # set
            if selected:
                redis_conn.sadd('selected_%s'%user.id,sku_id)
            else:
                redis_conn.srem('selected_%s'%user.id,sku_id)
            cart_sku = {
                'id': sku_id,
                'count': count,
                'selected': selected,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': sku.price * count,
            }
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'cart_sku': cart_sku})
        else:
            # 为登录用户保存在cookie
            carts = request.COOKIES.get('carts')
        #     判断数据是否存在
            if carts is not None:
        #         存在,然后进行解密
                cookie_cart = pickle.loads(base64.b64decode(carts))
            else:
                cookie_cart = {}
        #         跟新数据
            if sku_id in cookie_cart:
                cookie_cart[sku_id] = {
                    'count':count,
                    'selected':selected
                }
                # 加密
                cookie_data = base64.b64encode(pickle.dumps(cookie_cart))
            cart_sku = {
                'id': sku_id,
                'count': count,
                'selected': selected,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': sku.price * count,
            }
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'cart_sku': cart_sku})

            response.set_cookie('carts', cookie_data.decode(), 3600)

            return response


        # 对新数据进行加密
        #返回响应
            pass

    def delete(self,request):
        # 接收数据
        data =json.loads(request.body.decode())
        sku_id = data.get('sku_id')
        # 验证数据是否存在
        try:
            sku = SKU.objects.get(pk = sku_id)
        except SKU.DoesNotExist:
            return http.JsonResponse({'code':RETCODE.NODATAERR,'errmsg':'数据不存在'})
        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # redis
            redis_conn = get_redis_connection('carts')
        #     删除数据
        #     hash
            redis_conn.hdel('carts_%s'%user.id,sku_id)
        #     set
            redis_conn.srem('selected_%s'%user.id,sku_id)
            return http.JsonResponse({'code':RETCODE.OK,'errmsg':'OK'})
        else:
            # cookie
            carts = request.COOKIES.get('carts')
            if carts is not None:
        #         有数据,解码
                cookie_cart = pickle.loads(base64.b64decode(carts))
            else:
                cookie_cart= {}
            #     删除数据
            if sku_id in cookie_cart:
                del cookie_cart[sku_id]
            #     对新的数据解码
            cookie_data = base64.b64encode(pickle.dumps(cookie_cart))
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})

            response.set_cookie('carts', cookie_data, 3600)

            return response

# 全选
class CartSelectAllView(View):
    def put(self,request):
        # 接受参数
        json_dict = json.loads(request.body.decode())
        selected = json_dict.get('selected',True)
        # 校验参数
        if selected:
            if not isinstance(selected,bool):
                return http.HttpResponseBadRequest('参数有误')

        # 判断是否登录
        user = request.user
        if user.is_authenticated:
            # 用户已登录，操作redis购物车
            redis_conn = get_redis_connection('carts')
            cart = redis_conn.hgetall('carts_%s' % user.id)
            sku_id_list = cart.keys()
            if selected:
                # 全选
                redis_conn.sadd('selected_%s' % user.id, *sku_id_list)
            else:
                # 取消全选
                redis_conn.srem('selected_%s' % user.id, *sku_id_list)
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '全选购物车成功'})
        else:
            # 用户已登录，操作cookie购物车
            cart = request.COOKIES.get('carts')
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '全选购物车成功'})
            if cart is not None:
                cart = pickle.loads(base64.b64decode(cart.encode()))
                for sku_id in cart:
                    cart[sku_id]['selected'] = selected
                cookie_cart = base64.b64encode(pickle.dumps(cart)).decode()
                response.set_cookie('carts', cookie_cart, max_age=3600)

            return response



