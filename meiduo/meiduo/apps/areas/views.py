from django.shortcuts import render
from django.views import View
from django import http
from meiduo.utils.response_code import RETCODE
from meiduo.utils.views import LoginRequiredMixin
from .models import Areas
from django.db import DatabaseError
# Create your views here.
from django.core.cache import cache

"""
class AreasView(View):
    # this.host + '/areas/';
    def get(self, request):
        # user = request.user
        area_id = request.GET.get('area_id')
        if area_id is None:
        # 查询所有省级，得到是query_set
            try:
                provinces_qs = Areas.objects.filter(parent__isnull=True)
                # 前段目前是要求一个一个列表province_list
                # 将qs转换成列表
                province_list = []
                for province in provinces_qs:
                    # html中vue渲染指定key名
                    province_dict = {
                        'id': province.id,
                        'name': province.name,
                    }
                    province_list.append(province_dict)
                return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'province_list': province_list})
            except DatabaseError:
                return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '无法访问数据'})
        #  城市和行政区共用一个逻辑
        try:
            # 获取指定省/市 的所有的市/区一级
            cities_districts_qs = Areas.objects.filter(parent_id=area_id)
            # parent_area = Areas.objects.get(id=area_id)
            # cities_districts_qs = parent_area.subs.all()

            # 转化成列表
            subs = []
            for cities_districts in cities_districts_qs:
                cities_districts_dict = {
                    'id': cities_districts.id,
                    'name': cities_districts.name,
                }
                subs.append(cities_districts_dict)
            sub_data = {
                        # 'id':parent_area.id,
                        'id': Areas.objects.get(id=area_id).id,
                        'name':Areas.objects.get(id=area_id).name,
                        'subs': subs,
            }
        except DatabaseError as e:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '无法访问数据'})    
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'sub_data': sub_data})
"""

# 优化数据库访问过于频繁的问题
class AreasView(View):
    # this.host + '/areas/';
    def get(self, request):
        # user = request.user
        area_id = request.GET.get('area_id')
        if area_id is None:
            province_list = cache.get('province_list')
            if province_list is None:
                # 避免数据库异常无法返回数据给前端
                try:
                    # 查询所有省级，得到是query_set
                    provinces_qs = Areas.objects.filter(parent__isnull=True)
                    # 前段目前是要求一个一个列表province_list
                    # 将qs转换成列表
                    province_list = []
                    for province in provinces_qs:
                        # html中vue渲染指定key名
                        province_list.append({'id': province.id, 'name': province.name})
                        cache.set('province_list', province_list, 3600)
                except DatabaseError:
                    return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '无法访问数据'})
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'province_list': province_list})

        #  城市和行政区共用一个逻辑
        sub_data = cache.get('cities_districts%s' % area_id)
        if not sub_data:
            try:
            # 获取指定省/市 的所有的市/区一级
            # cities_districts_qs = Areas.objects.filter(parent_id=area_id)   # 最直接可取，但是后面需要用到的id、name属性
                parent_area = Areas.objects.get(id=area_id)   # 优化后面的拼接列表
                cities_districts_qs = parent_area.subs.all()
            # 优化读取：
            # 由于不确定要访问的市还是行政区的数据
            # 转化成列表
                subs = []
                for cities_districts in cities_districts_qs:
                    subs.append({'id': cities_districts.id, 'name': cities_districts.name})
                sub_data = {
                            'id': parent_area.id,
                            # 'id': Areas.objects.get(id=area_id).id,    # 前端也没有用到的地方
                            'name': parent_area.name,
                            # 'name':Areas.objects.get(id=area_id).name,
                            'subs': subs,
                }
                cache.set('cities_districts%s' % area_id, sub_data, 3600)
            except DatabaseError as e:
                return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '无法访问数据'})
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'sub_data': sub_data})