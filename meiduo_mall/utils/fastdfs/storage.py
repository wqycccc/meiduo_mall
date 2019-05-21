from django.core.files.storage import Storage

from meiduo_mall import settings
#1.您的自定义存储系统必须是以下的子类 django.core.files.storage.Storage：
#2.Django必须能够在没有任何参数的情况下实例化您的存储系统。
# 这意味着任何设置都应该来自django.conf.settings
#3.您的存储类必须实现_open()和_save() 方法
# 以及适用于您的存储类的任何其他方法

#4.您的存储类必须是可解构的， 以便在迁移中的字段上使用时可以对其进行序列化。
# 只要您的字段具有可自行序列化的参数，就
# 可以使用 django.utils.deconstruct.deconstructible类装饰器（
# 这就是Django在FileSystemStorage上使用的）。

class MyStorage(Storage):
   def __init__(self,fdfs_url = None):
       if not fdfs_url:
           fdfs_url = settings.FDFS_URL
           self.fdfs_url =fdfs_url

   def _open(self, name, mode='rb'):
       pass

   def _save(self, name, content, max_length=None):
       pass
   def url(self, name):
       # 这个name 其实就是 file_id
       # name = group1/M00/00/01/CtM3BVrLmc-AJdVSAAEI5Wm7zaw8639396

       # http://192.168.229.148:8888/ + name
       # return 'http://192.168.229.148:8888/' + name
       # return settings.FDFS_URL + name
       return self.fdfs_url + name