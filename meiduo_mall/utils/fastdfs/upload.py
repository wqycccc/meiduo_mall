#1.导入Fdfs_client
from fdfs_client.client import Fdfs_client
#2.创建Fdfs客户端,创建客户端的时候需要加载配置文件
client=Fdfs_client(conf_path='utils/fastdfs/client.conf')
#3.上传图片
# 给一个图片的绝对路径
client.upload_by_filename('/home/python/Desktop/image/20180815112433_sttyo.jpeg')