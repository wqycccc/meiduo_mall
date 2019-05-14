from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from meiduo_mall import settings
from apps.oauth import constants

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
    return token