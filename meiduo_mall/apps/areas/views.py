from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View
from django.core.cache import cache

from apps.areas.models import Area
from utils.response_code import RETCODE


class AreaView(View):
    def get(self,request):
        # 1.接受数据area_id
        area_id = request.GET.get('area_id')
        if area_id is not None:
            sub_list = cache.get('sub_area_%s'%area_id)
            if sub_list is None:
                # 2.如果有area_id ,则查询 市/区县数据
                # 2.1 根据area_id 获取市/区县信息
                areas = Area.objects.filter(parent_id=area_id)
                # 2.2 对象列表进行转换来获取字典列表
                sub_list = []
                for area in areas:
                    sub_list.append({
                        'id':area.id,
                        'name':area.name
                    })
                cache.set('sub_area_%s'%area_id, sub_list, 24 * 3600)
            return http.JsonResponse({'code':RETCODE.OK,'errmsg':'ok','sub_list':sub_list})
        else:
            # 如果没有area_id,就查询省的数据
            areas = Area.objects.filter(parent=None)
            pop_list = []
            for area in areas:
                pop_list.append({
                    'id':area.id,
                    'name':area.name
                })
                # cache(key,value)
                cache.set('pop_list',pop_list,24 * 3600)
                # 我们不能直接将对象列表 / 对象
                # 传递给JsonRespnse
                # JsonResponse 只能返回 字典数据
                # 因为省,市区数据是局部刷新,所以我们采用ajax
            return http.JsonResponse({'code':RETCODE.OK,'errmsg':'ok','provinces':pop_list})


