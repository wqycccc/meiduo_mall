from django import http
from django.core.paginator import Paginator
from django.shortcuts import render

# Create your views here.
from django.views import View

from apps.contents.utils import get_categories
from apps.goods.models import GoodsCategory, SKU, GoodsVisitCount
from apps.goods.utils import get_breadcrumb
from apps.views import logger
from utils.response_code import RETCODE


class ListView(View):
    """商品列表页"""

    def get(self, request, category_id, page_num):
        """提供商品列表页"""
        # 判断category_id是否正确
        try:
            category = GoodsCategory.objects.get(pk=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseBadRequest('GoodsCategory does not exist')
        # 接收sort参数：如果用户不传，就是默认的排序规则
        sort = request.GET.get('sort', 'default')

        # 查询商品频道分类
        categories = get_categories()
        # 查询面包屑导航
        breadcrumb = get_breadcrumb(category)

        # 按照排序规则查询该分类商品SKU信息
        if sort == 'price':
            # 按照价格由低到高
            sort_field = 'price'
        elif sort == 'hot':
            # 按照销量由高到低
            sort_field = '-sales'
        else:
            # 'price'和'sales'以外的所有排序方式都归为'default'
            sort = 'default'
            sort_field = 'create_time'
        skus = SKU.objects.filter(category=category, is_launched=True).order_by(sort_field)

        # 创建分页器：每页N条记录
        paginator = Paginator(skus,5)
        # 获取每页商品数据
        try:
            page_skus = paginator.page(page_num)
        except Exception as e:
            logger. error(e)
            # 如果page_num不正确，默认给用户404
            return http.HttpResponseNotFound('empty page')
        # 获取列表页总页数
        total_page = paginator.num_pages

        # 渲染页面
        context = {
            'categories': categories,   # 频道分类
            'breadcrumb': breadcrumb,   # 面包屑导航
            'sort': sort,               # 排序字段
            'category': category,       # 第三级分类
            'page_skus': page_skus,     # 分页后数据
            'total_page': total_page,   # 总页数
            'page_num': page_num,       # 当前页码
        }
        return render(request, 'list.html', context=context)

    """
    热销数据的获取

    需求:
        当用户点击了某一个分类之后,需要让前端将分类id传递给热销视图

    后端:

        1.根据分类查询数据,进行排序,排序之后获取2条数据
        2.热销数据在某一段时间内 很少变化 可以做缓存

        路由和请求方式

        GET     hot/category_id/
    """
    """
    从今天开始记一些相应状态码:
        200 成功

        300 重定向

        404 找不到页面(路由问题)
        403 Forbidden 禁止访问(权限问题/没有登陆)

        500 服务器问题(代码加断电)
    """


class HotView(View):
    """商品热销排行"""

    def get(self, request, category_id):
        """提供商品热销排行JSON数据"""
        # 根据销量倒序
        skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:2]

        # 序列化
        hot_skus = []
        for sku in skus:
            hot_skus.append({
                'id':sku.id,
                'default_image_url':sku.default_image.url,
                'name':sku.name,
                'price':sku.price
            })

        return http.JsonResponse({'code':RETCODE.OK, 'errmsg':'OK', 'hot_skus':hot_skus})


class DetailView(View):
    """商品详情页"""

    def get(self, request, sku_id):
        """提供商品详情页"""
        # 获取当前sku的信息
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return render(request, '404.html')

        # 查询商品频道分类
        categories = get_categories()
        # 查询面包屑导航
        breadcrumb = get_breadcrumb(sku.category)

        # 构建当前商品的规格键
        sku_specs = sku.specs.order_by('spec_id')
        sku_key = []
        for spec in sku_specs:
            sku_key.append(spec.option.id)
        # 获取当前商品的所有SKU
        skus = sku.spu.sku_set.all()
        # 构建不同规格参数（选项）的sku字典
        spec_sku_map = {}
        for s in skus:
            # 获取sku的规格参数
            s_specs = s.specs.order_by('spec_id')
            # 用于形成规格参数-sku字典的键
            key = []
            for spec in s_specs:
                key.append(spec.option.id)
            # 向规格参数-sku字典添加记录
            spec_sku_map[tuple(key)] = s.id
        # 获取当前商品的规格信息
        goods_specs = sku.spu.specs.order_by('id')
        # 若当前sku的规格信息不完整，则不再继续
        if len(sku_key) < len(goods_specs):
            return
        for index, spec in enumerate(goods_specs):
            # 复制当前sku的规格键
            key = sku_key[:]
            # 该规格的选项
            spec_options = spec.options.all()
            for option in spec_options:
                # 在规格参数sku字典中查找符合当前规格的sku
                key[index] = option.id
                option.sku_id = spec_sku_map.get(tuple(key))
            spec.spec_options = spec_options


        # 渲染页面
        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'sku': sku,
            'specs':goods_specs
        }
        return render(request, 'detail.html',context=context)

    """
    需求:
        当用户点击详情(列表页面)页面的时候,我们需要让前端将分类id传递给后端
        后端对当前的分类数据进行+1的统计

    后端:

        1.接收分类id
        2.查询对应的分类信息
        3.统计数据的更新
        4.返回数据

        请求方式和路由:
            post  detail/visit/(?P<category_id>\d+)/
    """

class CategoryVisitView(View):

    def post(self,request,category_id):
        # 1.接收分类id
        # 2.查询对应的分类信息
        try:
            category = GoodsCategory.objects.get(pk=category_id)
        except GoodsCategory.DoesNotExist:
            return http.JsonResponse({'code':RETCODE.NODATAERR,'errmsg':'没有此分类'})
        # 3.统计数据的更新
        from django.utils import timezone
        # 先查询对应当天和对应分类的记录
        today = timezone.localdate()
        try:
            gvc = GoodsVisitCount.objects.get(category=category,date=today)
        except GoodsVisitCount.DoesNotExist:
            # 查询不出来,创建新的记录
            gvc = GoodsVisitCount(
                category = category,
                count = 1,
                date = today
            )
            gvc.save()
        else:
            # 查询出来就进行+1
            gvc.count +=1
            gvc.save()
        # 4.返回数据
        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'ok'})
