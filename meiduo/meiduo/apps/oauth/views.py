import re

from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from QQLoginTool.QQtool import OAuthQQ
from django import http
from meiduo.utils.response_code import RETCODE
from .models import OAuthUser
from users.models import User
from . import settings
from random import randint
import logging
from .utils import check_openid_singnature, generate_openid_encrypt
from django_redis import get_redis_connection
# Create your views here.
# 获取终端的显示日志
logger = logging.getLogger('django')


class OAuthQQURL(View):
    '''获取QQ登录code'''
    def get(self, request):
        # 获取查询参数中的next参数提取来源
        next = request.GET.get('next', '/')
        # 创建OAuthQQ对象
        oauth = OAuthQQ(
            # 应用appid
            client_id=settings.client_id,
            # 应用app秘钥
            client_secret=settings.client_secret,
            # 回调地址
            redirect_uri=settings.redirect_uri,
            # 记录来源， 防止csrf攻击
            state=next
        )
        # OAuthQQ返回一个给用户扫码的url
        login_url = oauth.get_qq_url()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'login_url': login_url})



class OAuthUserView(View):
    '''QQ认证回调处理'''
    def get(self, request):
        # 获取查询字符串中的code
        code = request.GET.get('code')
        # 判断code是否获取到
        print(code)
        if code is None:
            # 默认状态码是403
            return http.HttpResponseForbidden('QQ登录失败')
            # 状态码默认是200
            # return http.HttpResponse('QQ登录失败')
            # return redirect(reverse('contents:index'))
        oauth = OAuthQQ(
            client_id=settings.client_id,
            client_secret=settings.client_secret,
            redirect_uri=settings.redirect_uri,
            # state = next    # 此处next是值内置next方法
        )
        # 作用就是分清楚是SDK报错还是我们的代码
        try:
            # 获取access token
            access_token = oauth.get_access_token(code=code)
            print(access_token)
            # 获取openid
            openid = oauth.get_open_id(access_token=access_token)
            # 判断open_id 跟某个美多商城用户有无绑定
            print(openid)
            # 判断用户的是否有绑定过
        except Exception as er:
            logger.error(er)
            # 服务器代码的报错， 状态码是500
            return http.HttpResponseServerError('QQ登录失败')
        try:
            # 说明已绑定用户，直接登录即可
            oauth = OAuthUser.objects.get(openid=openid)
        except OAuthUser.DoesNotExist:
            # 直接创建一个用户，
            # num = randint(0, 100000000)
            # username = 'oauth_qq_%d' % num
            # password = randint(0, 100000000)
            # mobile = "qq_num%d" % d
            # user = User.objects.create_user(username=username, password=password, telephone=mobile)
            # OAuthUser.objects.create(user=user, openid=openid)
            # 未绑定用户， 要去绑定用户，此时openid必须先保存着，为避免占用服务器资源，传到前端保存,为防止信息泄露， 要进行加密处理
            openid = generate_openid_encrypt(openid)
            response = render(request, 'oauth_callback.html', {'openid': openid})
            # 若要利用openid防止crsf攻击
            # response.set_cookie('openid', openid)
            return response
        else:
            user = oauth.user
            login(request, user)
            url = request.GET.get('next') or reverse('contents:index')
            # 使网页展示美多账号的用户名
            response = redirect(url)
            response.set_cookie('username', oauth.user.username, max_age=3600 * 24 * 7)
            return response

    def post(self, request):    # from 表单为用action属性指明提交的地址， 默认向本网页路由发送请求
        # 防止csrf攻击  {{input csrf}}也有，所以这可以不用，但是必须改进的一点是openid直接暴露在前端
        # 前端传回来的openid是经过加密的，需要解密
        openid = request.POST.get('openid')
        # 为了防止校验不过进行无用功，可以挪到后边需要用到再解码
        # openid = check_openid_singnature(openid)

        # openids = request.COOKIES['openid']
        # if openid != openids:
        #     return http.HttpResponseForbidden('csrf攻击')
        # 获取请求头内容
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        sms_code_client = request.POST.get('sms_code')

        if not all([openid, mobile, password, sms_code_client]):
            return http.HttpResponseForbidden('缺少参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号码')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入正确的手机号码')
        redis_conn = get_redis_connection(alias='verifications')
        sms_code_server = redis_conn.get('sms_code_%s' % mobile)
        redis_conn.delete('sms_code_%s' % mobile)
        if sms_code_server is None:
            return http.HttpResponseForbidden('短信验证码已过期')
        if sms_code_server.decode() != sms_code_client:
            return http.HttpResponseForbidden('短信验证码输入有无')

        # 解码openid
        openid = check_openid_singnature(openid)
        if openid is None:
            return http.HttpResponseForbidden('openid无效，重新扫码')
        # 判断手机号是否有注册过
        try:
            # 该手机号已注册过
            user = User.objects.get(telephone=mobile)
            # 判断密码正确
            if not user.check_password(password):
                # 重置密码
                user.set_password = password
                user.save()
            # 新建一个OAthUser对象，保存数据库
            oauth = OAuthUser.objects.create(user=user, openid=openid)
            # 密码不正确， 重置密码
        except User.DoesNotExist:
            # 创建User新用户, 绑定外建，
            username = 'oauth_qq_%s' % mobile
            user = User.objects.create_user(username=username, password=password, telephone=mobile)
            # 创建OauthUser用户
            oauth = OAuthUser.objects.create(user=user, openid=openid)
        # 共有的必须步走
        # 登录到首页或来源
        login(request, user)
        url = request.GET.get('state') or reverse('contents:index')
        # 使网页展示美多账号的用户名
        response = redirect(url)
        response.set_cookie('username', oauth.user.username)
        return response







