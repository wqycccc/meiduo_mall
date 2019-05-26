

"""
合并购物车
登陆后将cookie中的数据合并到redis
"""
import base64
import pickle

from django_redis import get_redis_connection


def merge_cart_cookie_to_redis(request,user,response):
    # 获取cookie中的购物车数据
    cookie_cart_str = request.COOKIES.get('carts')
    if cookie_cart_str is not None:
        cookie_cart_dict = pickle.loads(base64.b64decode(cookie_cart_str.encode()))
        new_cart_dict = {}
        new_cart_selected_add = []
        new_cart_selected_remove = []
        for sku_id,cookie_dict in cookie_cart_dict.items():
            new_cart_dict[sku_id] = cookie_dict['count']
            if cookie_dict['selected']:
                new_cart_selected_add.append(sku_id)
            else:
                new_cart_selected_remove.append(sku_id)
        # 将new_cart_dict写入到Redis数据库
        redis_conn = get_redis_connection('carts')
        pl = redis_conn.pipeline()
        pl.hmset('carts_%s' % user.id, new_cart_dict)
        # 将勾选状态同步到Redis数据库
        if new_cart_selected_add:
            pl.sadd('selected_%s' % user.id, *new_cart_selected_add)
        if new_cart_selected_remove:
            pl.srem('selected_%s' % user.id, *new_cart_selected_remove)
        pl.execute()

        # 清除cookie
        response.delete_cookie('carts')

        return response
    return response


# 将抽象的问题具体化
#
# 需求:
#     当用户登陆的时候,需要将cookie数据合并到reids中
#
#     1.用户登陆的时候
#     2.合并数据
#
#     将cookie数据合并到reids中
#     1.获取到cookie数据
#     2.遍历cookie数据
#     3.当前是以cookie为主,所以我们直接将cookie数据转换为hash, set(记录选中的和未选中的)
#
#     4.连接redis 更新redis数据
#     5.将cookie数据删除
