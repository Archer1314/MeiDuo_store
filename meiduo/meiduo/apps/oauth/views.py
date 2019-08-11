import re
import random

from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.http import urlencode
from django.views import View
from QQLoginTool.QQtool import OAuthQQ
from django import http
from meiduo.utils.response_code import RETCODE
from .models import OAuthUser,OAuthWeiBoUser
from users.models import User
from .settings import OAuthQQBasic, OAuthWerBoBasic
from .constants import Constants
import logging
from .utils import check_openid_singnature, generate_openid_encrypt
from django_redis import get_redis_connection
from .sinaweibopy3 import APIClient
from celery_tasks.sms.tasks import sms_code_send

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
            client_id=OAuthQQBasic.client_id,
            # 应用app秘钥
            client_secret=OAuthQQBasic.client_secret,
            # 回调地址
            redirect_uri=OAuthQQBasic.redirect_uri,
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
        if code is None:
            # 默认状态码是403
            return http.HttpResponseForbidden('QQ登录失败')
            # 状态码默认是200
            # return http.HttpResponse('QQ登录失败')
            # return redirect(reverse('contents:index'))
        oauth = OAuthQQ(
            client_id=OAuthQQBasic.client_id,
            client_secret=OAuthQQBasic.client_secret,
            redirect_uri=OAuthQQBasic.redirect_uri,
            # state = next    # 此处next是值内置next方法
        )
        # 作用就是分清楚是SDK报错还是我们的代码
        try:
            # 获取openid
            openid = oauth.get_open_id(code)

        except Exception as er:
            logger.error(er)
            # 服务器代码的报错， 状态码是500
            return http.HttpResponseServerError('QQ登录失败')
        # 判断open_id 跟某个美多商城用户有无绑定
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
        # from 表单为用action属性指明提交的地址， 默认向本网页路由发送请求
        # 获取请求头内容
        openid = request.COOKIES.get('openid')
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

        access_token = check_openid_singnature(openid)
        if access_token is None:
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
            oauth = OAuthUser.objects.create(user=user, access_token=access_token)
            # 密码不正确， 重置密码
        except User.DoesNotExist:
            # 创建User新用户, 绑定外建，
            username = 'oauth_qq_%s' % mobile
            user = User.objects.create_user(username=username, password=password, telephone=mobile)
            # 创建OauthUser用户
            oauth = OAuthUser.objects.create(user=user, access_token=access_token)
        # 共有的必须步走
        # 登录到首页或来源
        login(request, user)
        url = request.GET.get('state') or reverse('contents:index')
        # 使网页展示美多账号的用户名
        response = redirect(url)
        response.set_cookie('username', user.username)
        return response


class OAuthWeiBoUrl(View):
    def get(self, request):
        # 清楚缓存的cookie信息
        next = request.GET.get('next', '/')
        # 拼接路径
        url_dict = {
            'client_id': OAuthWerBoBasic.App_Key,
            'redirect_uri': OAuthWerBoBasic.redirect_uri,
            'state': next,
            'forcelogin': True,
        }
        base_url = 'https://api.weibo.com/oauth2/authorize?'
        utl_string = urlencode(url_dict)
        login_url = base_url + utl_string
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'login_url': login_url})


class OAuthWeiBoView(View):
    def get(self, request):
        # 获取查询字符串中的code
        code = request.GET.get('code')
        # 判断code是否获取到
        if code is None:
            # 默认状态码取消登录者也会走这，重定向到首页
            return http.HttpResponseRedirect('/')
            # 状态码默认是200
            # return http.HttpResponse('QQ登录失败')
            # return redirect(reverse('contents:index'))

        oauth = APIClient(
            app_key=OAuthWerBoBasic.App_Key,
            app_secret=OAuthWerBoBasic.App_Secret,
            redirect_uri=OAuthWerBoBasic.redirect_uri,
        )
        try:
            access_token_dict = oauth.request_access_token(code)
            access_token = access_token_dict.get('access_token')
        except Exception:
            return http.HttpResponseServerError('微博登录失败')
        try:
            # 说明已绑定用户，直接登录即可
            oauth = OAuthWeiBoUser.objects.get(access_token=access_token)
        except OAuthWeiBoUser.DoesNotExist:
            access_token = generate_openid_encrypt(access_token)
            response = render(request, 'oauth_callback.html')
            response.set_cookie('access_token', access_token)
            return response
        else:
            user = oauth.user
            login(request, user)
            url = request.GET.get('state') or reverse('contents:index')
            # 使网页展示美多账号的用户名
            response = redirect(url)
            response.set_cookie('username', oauth.user.username, max_age=3600 * 24 * 7)
            return response

    def post(self, request):
        """新版绑定界面的"""
        # from 表单为用action属性指明提交的地址， 默认向本网页路由发送请求
        # 获取请求头内容
        access_token = request.COOKIES.get('access_token')
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        sms_code_client = request.POST.get('sms_code')

        if not all([access_token, mobile, password, sms_code_client]):
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

        access_token = check_openid_singnature(access_token)
        if access_token is None:
            return http.HttpResponseForbidden('access_token无效，重新扫码')
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
            oauth = OAuthWeiBoUser.objects.create(user=user, access_token=access_token)
            # 密码不正确， 重置密码
        except User.DoesNotExist:
            # 创建User新用户, 绑定外建，
            username = 'oauth_weibo_%s' % mobile
            user = User.objects.create_user(username=username, password=password, telephone=mobile)
            # 创建OauthUser用户
            oauth = OAuthWeiBoUser.objects.create(user=user, access_token=access_token)
        # 共有的必须步走
        # 登录到首页或来源
        login(request, user)
        url = request.GET.get('state') or reverse('contents:index')
        # 使网页展示美多账号的用户名
        response = redirect(url)
        response.set_cookie('username', oauth.user.username)
        return response


# class OAuthSendSms(View):
# #     """发短信"""
#     def get(self, request, mobile):
#         pass
#         # 获取到手机号之后
#         redis_conn = get_redis_connection('verifications')
#         count = redis_conn.get('sending_flag_%s' % mobile)
#         if count:
#             return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'err_msg': '频繁访问'})
#
#         # 1. 根据请求方式确定三个参数的获取
#         text = request.GET.get('text')
#         uuid = request.GET.get('image_code_id')
#
#         # 校验
#         if not all([text, uuid]):
#             return http.HttpResponseForbidden('缺少参数')
#         # 尝试取出之前保存的图形验证码信息
#         redis_image_code = redis_conn.get(uuid)
#         # 判断该uuid是否在redis中,排除该redis是否过期
#         if not redis_image_code:
#             return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'err_msg': '图形验证码过期'})
#         redis_conn.delete(uuid)
#         # 判断是否填对图形验证码
#         if redis_image_code.decode().lower() != text.lower():
#             return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'err_msg': '图形码输入不正确'})
#
#         # 生成验证码信息
#         sms_code = '%06d' % random.randint(0, 999999)
#         # 中断显示验证码，性能
#         print(sms_code)
#         # 保存手机验证码的和手机号
#         # 保存手机发送验证码的状态信息
#         pl = redis_conn.pipeline()
#         pl.setex('sms_code_%s' % mobile, Constants.SMS_CODE_EXPIRE_REDIS, sms_code)
#         pl.setex('sending_flag_%s' % mobile, Constants.MOBILE_REQUEST_EXPIRE_REDIS, 1)
#         pl.execute()
#
#         # 利用第三方容联云发短信 ,比较花费时间，造成后边返回前台的阻塞
#         # CCP().send_template_sms('15029014304', [sms_code, Constans.SMS_CODE_EXPIRE_REDIS//60], 1)
#
#         # 利用celery
#         sms_code_send.delay(mobile, sms_code)
#
#         return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

