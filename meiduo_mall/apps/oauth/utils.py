from itsdangerous import BadData
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from apps.views import logger
from meiduo_mall import settings
from apps.oauth import constants
# 加密
def generic_openid_token(openid):
    #1. 创建实例对象
    s=Serializer(secret_key=settings.SECRET_KEY,expires_in=constants.OPENID_TOKEN_EXPIRES_TIME)
    # 2.组织数据
    data = {
        'openid':openid
    }
    # 3.加密数据
    token = s.dumps(data)
    # 4.返回数据
    return token.decode()
# 解密
def check_openid_token(token):
    # 1.创建实例
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=constants.OPENID_TOKEN_EXPIRES_TIME)
    # 2.解密  解密的时候捕获异常
    try:
        result = s.loads(token)
    except BadData as e:
        logger.error(e)
        return None
    # 获得解密后的数据
    return result.get('openid')
