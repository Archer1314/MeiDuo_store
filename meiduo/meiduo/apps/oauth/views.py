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
# Create your views here.


class OAuthQQURL(View):

    def get(self, request):
        next = request.GET.get('next', '/')

        oauth = OAuthQQ(
            client_id=settings.client_id,
            client_secret=settings.client_secret,
            redirect_uri=settings.redirect_uri,
            state=next
        )
        # OAuthQQ返回一个给用户扫码的url
        login_url = oauth.get_qq_url()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'login_url': login_url})


# 回调视图
class OAuthUserView(View):
    def get(self, request):

        # 获取查询字符串中的code
        code = request.GET.get('code')
        # 判断code是否获取到
        print(code)
        if code is None:
            return http.HttpResponse('QQ登录失败')

            # return redirect(reverse('contents:index'))
        oauth = OAuthQQ(
            client_id=settings.client_id,
            client_secret=settings.client_secret,
            redirect_uri=settings.redirect_uri,
            # state = next    # 此处next是值内置next方法
        )
        # 获取access token
        access_token = oauth.get_access_token(code=code)
        print(access_token)
        # 获取openid
        openid = oauth.get_open_id(access_token=access_token)
        # 判断open_id 跟某个美多商城用户有无绑定
        print(openid)
        # 判断用户的是否有绑定过
        try:
            oauth = OAuthUser.objects.get(openid=openid)
            url = request.GET.get('next') or reverse('contents:index')
            # 使网页展示美多账号的用户名
            response = redirect(url)
            response.set_cookie('username', oauth.user.username)
            return response
        except OAuthUser.DoesNotExist:
            # 直接创建一个用户，
            # num = randint(0, 100000000)
            # username = 'oauth_qq_%d' % num
            # password = randint(0, 100000000)
            # mobile = "qq_num%d" % d
            # user = User.objects.create_user(username=username, password=password, telephone=mobile)
            # OAuthUser.objects.create(user=user, openid=openid)
            response = render(request, 'oauth_callback.html', {'openid': openid})
            response.set_cookie('openid', openid)
            return response

    def post(self, request):    # from 表单为用action属性指明提交的地址， 默认向本网页路由发送请求
        # 防止csrf攻击  {{input csrf}}也有，所以这可以不用，但是必须改进的一点是openid直接暴露在前端
        openid = request.POST.get('openid')
        openids = request.COOKIES['openid']
        if openid != openids:
            return http.HttpResponseForbidden('csrf攻击')
        # 获取请求头内容
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
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
            oauth = OAuthUser.objects.create(user=user, openid=openids)
            # 密码不正确， 重置密码
        except User.DoesNotExist:
            # 创建User新用户, 绑定外建，
            username = 'oauth_qq_%s' % mobile
            user = User.objects.create_user(username=username, password=password, telephone=mobile)
            # 创建OauthUser用户
            oauth = OAuthUser.objects.create(user=user, openid=openid)
        # 共有的必须步走
        # 登录到首页或来源
        url = request.GET.get('next') or reverse('contents:index')
        # 使网页展示美多账号的用户名
        response = redirect(url)
        response.set_cookie('username', oauth.user.username)
        return response







