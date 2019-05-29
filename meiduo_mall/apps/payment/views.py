from alipay import AliPay
from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View

from apps.orders.models import OrderInfo
from meiduo_mall import settings
from utils.response_code import RETCODE
from utils.views import LoginRequiredJSONMixin


class PaymentView(LoginRequiredJSONMixin, View):
    """订单支付功能"""

    def get(self,request, order_id):
        try:
            # 为了让查询的更准确,我们添加2个参数,一个是订单状态,另外一个是用户
            order=OrderInfo.objects.get(order_id=order_id,
                                        user=request.user,
                                        status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return http.JsonResponse({'code':RETCODE.NODATAERR,'errmsg':'暂无此订单'})

        # 3.创建alipay实例对象
        app_private_key_string = open(settings.APP_PRIVATE_KEY_PATH).read()
        alipay_public_key_string = open(settings.ALIPAY_PUBLIC_KEY_PATH).read()


        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug = settings.ALIPAY_DEBUG  # 默认False
        )
        # 4.生成order_string
        # 如果你是 Python 3的用户，使用默认的字符串即可
        subject = "美多商城%s"%order_id

        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount), # 需要将货币类型转换为字符串
            subject=subject,
            return_url=settings.ALIPAY_RETURN_URL
        )

        # alipay_url='https://openapi.alipaydev.com/gateway.do?'+order_string

        alipay_url=settings.ALIPAY_URL + '?' +order_string
        # 5.返回生成的url
        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'ok','alipay_url':alipay_url})