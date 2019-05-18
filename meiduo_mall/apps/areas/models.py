from django.db import models

class Area(models.Model):
    # on_delete
    # 外键的级联操作
    # 1个省 n个市
    #  同步操作
    #  set null  主表信息为null,从表信息存在
    #  拒绝操作

    # 1个黑帮老大    n个小弟
    # 要执行枪决     殉葬
    #               小弟自己过
    #               劫狱


    # related_name 默认的名字为: 关联模型类名小写_set
    """省市区"""
    name = models.CharField(max_length=20, verbose_name='名称')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='subs', null=True, blank=True, verbose_name='上级行政区划')

    class Meta:
        db_table = 'tb_areas'
        verbose_name = '省市区'
        verbose_name_plural = '省市区'

    def __str__(self):
        return self.name