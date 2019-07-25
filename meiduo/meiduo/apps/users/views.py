import json
from django.contrib.auth import login
from django.contrib.auth import logout
from django.core.paginator import Paginator, EmptyPage
from django.db import DatabaseError
from django.shortcuts import render, redirect
from django import http
from django.urls import reverse
from django_redis import get_redis_connection
# Create your views here.
import re
from .models import User
from meiduo.utils.response_code import RETCODE
from django.views.generic.base import View
from django.contrib.auth import authenticate    # 已经被ManyUser继承
from .utils import ManyUser, generate_verify_url, check_verify_url, generate_access_token, check_access_token
from django.conf import settings
from meiduo.utils.views import LoginRequiredView
from celery_tasks.email.tasks import send_verify_email
from .models import Addresses
from carts.utils import merge_cart_cookie_to_redis
from django.db.models import Q
import random
from .constants import Constants
from celery_tasks.sms.tasks import sms_code_send
from orders.models import OrderInfo, OrderGoods
from goods.models import SKU
from django.db import transaction


class RegisterView(View):
    def get(self, request):
        '''提供注册界面'''
        return render(request, 'register.html')

    def post(self, request):
        """注册逻辑"""
        # 接收请求体数据
        query_dict = request.POST
        username = query_dict.get('username', '')
        password = query_dict.get('password', '')
        password2 = query_dict.get('password2', '')
        telephone = query_dict.get('mobile', '')
        #  图形验证码只是用来防止恶意大量注册使用,
        #  逻辑是填完校验码后点击获取手机验证码时将填的校验码发到后端进行比较,
        #  确认一致才发送短信(短信收费),所以不需要作为个人信息进行校验和保险到数据库
        # image_code = query_dict.get('image_code', '')
        sms_code = query_dict.get('sms_code', '')
        allow = query_dict.get('allow', '')

        # 校验有无选项为空,checkbox标签在提交时默认提供None/on, 或用value属性指定提交的信息
        # 此处register.html使用默认,以下all可判断是否勾选,无需进行其他校验.
        if not all(query_dict.dict().values()):
            return http.HttpResponseForbidden('非法注册,部分为空')
        # if not all([username, password, password2, telephone, sms_code, allow]):
        #     return http.HttpResponseForbidden('非法注册,部分为空')
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('非法注册,用户名不符合规范')
        if not re.match(r'^[[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('非法注册,密码不符合规范')
        if  password != password2:
            return http.HttpResponseForbidden('非法注册,密码两次输入不一致')
        if not re.match(r'^1[345789]\d{9}$', telephone):
            return http.HttpResponseForbidden('非法注册,手机号不符合规范')

        # 后边补全手机验证码校验
        redis_conn = get_redis_connection('verifications')
        redis_sms_code = redis_conn.get('sms_code_%s' % telephone)
        # 保证每个手机验证码只能使用一次
        # 且前端无防护此项
        redis_conn.delete(redis_sms_code)
        if redis_sms_code is None:
            return http.HttpResponseForbidden('验证码已过期')     # 正常逻辑是json局部刷新,但此为form请求,暂时用
        if redis_sms_code.decode() != sms_code:
            return http.HttpResponseForbidden('手机验证码不正确')   # 前端给的是form表单请求,不能返回json

        user = User.objects.create_user(username=username, password=password, telephone=telephone)
        login(request, user)

        # 设置cookie，主页的用户信息更新（vue.js会接受，然后渲染页面）
        # 注册成功后，重新定向到首页
        response = redirect(reverse('contents:index'))
        response.set_cookie('username', username, max_age=settings.SESSION_COOKIE_AGE)
        return response


class UsernamecountView(View):
    """判断用户名是否重复注册"""
    def get(self, request, username):
        username = username
        count = User.objects.filter(username=username).count()
        return http.JsonResponse({'code': RETCODE.OK, 'err_msg': 'OK', 'count': count})


class telephonecountView(View):
    """判断手机是否重复注册"""
    def get(self, request, mobile):
        telephone = mobile
        count = User.objects.filter(telephone=telephone).count()
        return http.JsonResponse({'code': RETCODE.OK, 'err_msg': 'OK', 'count': count})


class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        #  目的：获取用户的登陆信息， 分析：前端是用form表单发送，post请求，需要返回的是http response
        # input 标签表单的name属性就是这个标签的key， value属性是值
        query_dict = request.POST
        username = query_dict.get('username')
        password = query_dict.get('password')
        remembered = query_dict.get('remembered')

        if not all([username, password]):
            return http.HttpResponseForbidden('账号或密码不全')

        # 校验，如果不正确，再次返回登陆页面，并提示错误信息
        # filter不行，得到的是queryset，不能进行check_password方法
        # user = User.objects.filter(username=username)
        # if user.check_password(password):
        #     return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})
        # return render(request, 'index.html')

        # try:
        #     user = User.objects.get(username=username)
        # except User.DoesnotExist:
        #     return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})
        #
        # if not user.check_password(password):
        #     return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})

        # 比较繁琐，django有做好该认证工作
        # user = authenticate(username=username, password=password)
        # 但是只能满足账号的username，手机号bu满足
        # 改善2  看源代码，将校验的内容根据输入动态的从username改为mobile
        user = ManyUser.authenticate(request, username=username, password=password)

        if not user:
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})

        # 优花1
        # 保持用户状态  默认会保持14天
        # 浏览器关闭后还会存在14天（cookie存在14天，服务器上的session信息保存14天）
        # 如果要修改，本质是要修改保存的session保存时间,login中的session保存時間用的是全局設置中（global。setting中）的SESSION_COOKIE_AVG設置
        login(request, user)

        # 如果用户选择不记录，则是需要关闭浏览器后就没有session信息
        if remembered != 'on':
            request.session.set_expiry(0)
        # 设置cookie，是主页的用户信息更新（vue.js会接受，然后渲染页面）
        response = redirect(request.GET.get('next') or reverse('users:center'))
        # 设置cooike带回username （不管以验证是么信息登录的都是显示用户名）
        response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE if remembered else None)
        """合并购物车"""
        merge_cart_cookie_to_redis(request, response)
        return response


# 直接推出
class LogoutView(View):
    def get(self, request):
        print('aaa')
        # 逻辑是这样，但是存储的不仅仅是kyy名
        # redis_conn = get_redis_connection('session')
        # redis_conn.delete(request.COOKIE['sessionid'])
        logout(request)

        response = redirect('users:login')
        response.delete_cookie('username')
        return response


# class UserCenterInfoView(View):
#     def get(self, request):
#         # 一个是经验的看request.user,此为一类对象，导包无效，可以转字符串
#         # print(request.user)
#         # if str(request.user) == 'AnonymousUser':
#         #     print(request.user)
#         #     return redirect(reverse('users:login'))
#
#         # django提供了快速的验证方法, 返回True/False
#         if request.user.is_authenticated:
#             return render(request, 'user_center_info.html')
#         else:
#             # 加入此项是为了回到来时的用户中心
#             url = reverse('users:login') + '?next=/info/'
#             return redirect(url)

class UserCenterInfoView(LoginRequiredView):
    def get(self, request):
        return render(request, 'user_center_info.html')


class UserCenterEmailView(LoginRequiredView):
    def put(self, request):
        # 接收数据：email
        json_dict = json.loads(request.body.decode())
        email = json_dict.get('email')
        # 校验
        # 1、非空
        if not email:
            return http.HttpResponseForbidden('缺少必传参数email')
        # 2、匹配格式
        if re.match('r[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('邮箱格式不正确')
        # 业务逻辑
        # 1、获取对象,request的user属性封装着真正的一个模型类对象
        user = request.user
        # 2、更新数据库的字段
        # 此类更新会更新数据库中的最近一次修改时间， 但是前段代码有问题，会随着重新发送邮箱时重复设置邮箱
        # user.email = email
        # user.save()
        # 此类更新不会更新数据表中的最近一次修改时间
        # 邮箱只要设置成功了，此代码都是无效的修改, email 不会为空
        User.objects.filter(id=user.id, email='').update(email=email)
        
        # from django.core.mail import send_mail
        # # send_mail(subject='主题', message='邮件普通正文，是纯文本', from_email='发件人', recipient_list=[email], html_message='超文本的邮件内容')
        # html_message='<li><a href="/info/" class="active">· 个人信息</a></li>'
        # send_mail(subject='defult', message='hello, welcome', from_email=settings.EMAIL_HOST_USER, recipient_list=[email], html_message=html_message)
        # 必须要重新获取一下
        user = User.objects.get(id=user.id)
        verify_url = generate_verify_url(user)
        send_verify_email.delay(email, verify_url)
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '已发送邮件'})


class UserEmailActiveView(View):
    def get(self, request):
        # 获取数据
        token = request.GET.get('token')
        print(token)
        # 校验数据
        if token is None:
            return http.HttpResponseForbidden('缺少token')
        user = check_verify_url(token)
        print(type(user))
        if user is None:
            return http.HttpResponseForbidden('token无效')
        user.email_active = True
        user.save()
        return redirect(reverse('users:center'))


class UserCenterAreasView(LoginRequiredView):
    def get(self, request):

        addresses = request.user.addresses.filter(is_deleted=False)
        address_dict_list = []
        for address in addresses:
            address_dict = {
                'id': address.id,
                'title': address.title,
                'receiver': address.receiver,
                'province_id': address.province_id,
                'province': address.province.name,
                'city_id': address.city_id,
                'city': address.city.name,
                'district_id': address.district_id,
                'district': address.district.name,
                'place': address.place,
                'mobile': address.mobile,
                'tel': address.tel,
                'email': address.email,
            }
            address_dict_list.append(address_dict)
        context = {
            'default_address_id': request.user.default_address_id,
            'addresses': address_dict_list,
        }
        return render(request, 'user_center_site.html', context)


class UserAreasCreateView(LoginRequiredView):
    def post(self, request):
        # 先判断数量小于20,
        user = request.user
        # count = user.addresses.all().filter(is_deleted=False).count()
        count = request.user.addresses.count()
        if count >= 20:
            return http.JsonResponse({'code':RETCODE.ADDRESSLIMIT,'errmsg': '收货地址数量超上限'})
        # 获取数据
        data = request.body.decode()   # from_data 是个字典
        data_dict = json.loads(data)
        title = data_dict.get('title')
        receiver = data_dict.get('receiver')
        province_id = data_dict.get('province_id')
        city_id = data_dict.get('city_id')
        district_id = data_dict.get('district_id')
        place = data_dict.get('place')
        mobile = data_dict.get('mobile')
        tel = data_dict.get('tel')
        email = data_dict.get('email')

        # 校验数据
        if not all([title, receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseForbidden('参数不全')
        # 省市区有外建在，不可能是错的
        # 一下都是前段校验过一遍的，报错直接禁止
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('电话格式不正确')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('固定电话格式不正确')
        if email:
            if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('邮箱格式不正确')

        # 保存数据  # 必须是继承认证类才可以这么获取用户
        # user = request.user
        try:
            address = Addresses.objects.create(user=user, title=title, receiver=receiver, province_id=province_id, city_id=city_id,
                                               district_id=district_id,place=place, mobile=mobile, tel=tel, email=email)
            # 设置默认地址
            if user.default_address is None:
                user.default_address = address
                user.save()
        except:
            return http.HttpResponseForbidden('添加失败')

        # 把新增的address模型对象转换成字典,并响应给前端
        address_dict = {
            'id': address.id,   # 该项前端用不着，为后续的修改做铺垫，知道是哪条地址要修改
            'title': address.title,
            'receiver': address.receiver,
            'province_id': address.province_id,
            'province': address.province.name,
            'city_id': address.city_id,
            'city': address.city.name,
            'district_id': address.district_id,
            'district': address.district.name,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.tel,
            'email': address.email,
        }
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'address': address_dict})


class UpdateDestroyAddressView(LoginRequiredView):
    def put(self, request, address_id):
        try:
            # 直接用Address表进行查数据
            # user = request.user
            # address = Addresses.objects.get(id=address_id, user=request.user, is_deleted=False)
            # user对象通过外键访问另一张表(这是一访问多) request.user.addresses是一个query_set
            address = request.user.addresses.get(id=address_id, user=request.user, is_deleted=False)
            # 此时已有的防异常条件： 认证用户、address_id 有， 此判断有无必要
            if address is None:
                return http.HttpResponseForbidden('非正常请求')
        except DatabaseError:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '数据异常'})
        #  获取参数
        data = request.body.decode()  # from_data 是个字典
        data_dict = json.loads(data)
        title = data_dict.get('title')
        receiver = data_dict.get('receiver')
        province_id = data_dict.get('province_id')
        city_id = data_dict.get('city_id')
        district_id = data_dict.get('district_id')
        place = data_dict.get('place')
        mobile = data_dict.get('mobile')
        tel = data_dict.get('tel')
        email = data_dict.get('email')
#         校验
        # 校验数据
        if not all([title, receiver, province_id, city_id, district_id, place, mobile]):
            return http.JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '缺少必传参数'})
        # 省市区有外建在，不可能是错的
        # 一下都是前段校验过一遍的，报错直接禁止
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'code': RETCODE.MOBILEERR, 'errmsg': '手机号错误'})
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.JsonResponse({'code': RETCODE.TELERR, 'errmsg': '固定电话错误'})
        if email:
            if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.JsonResponse({'code': RETCODE.EMAILERR, 'errmsg': '邮箱错误'})

        # 修改
        # 注意细节：若用updata 的方式更新， 注意必须重新取出这个address 返回， 否则前端展示的还是之前的久对象数据
        try:
            # address.user = user    # 地址所属对象不能修改
            address.title = title
            address.receiver = receiver
            address.province_id = province_id
            address.city_id = city_id
            address.district_id = district_id
            address.place = place
            address.mobile = mobile
            address.tel = tel
            address.email = email
            address.save()
        except DatabaseError:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '数据报错'})

        # 把新增的address模型对象转换成字典,并响应给前端
        # 注意返回的address对象是不是最新的，因为一开始有取出久的存于对象address
        address_dict = {
            'id': address.id,
            'title': address.title,
            'receiver': address.receiver,
            'province_id': address.province_id,
            'province': address.province.name,
            'city_id': address.city_id,
            'city': address.city.name,
            'district_id': address.district_id,
            'district': address.district.name,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.tel,
            'email': address.email,
        }
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'address': address_dict})

    def delete(self, request, address_id):
        try:
            # 直接用Address表进行查数据
            user = request.user
            address = Addresses.objects.get(id=address_id, user=user, is_deleted=False)
            # user对象通过外键访问另一张表(这是一访问多) request.user.addresses是一个query_set
            # address = request.user.addresses.get(id=address_id, user=request.user, is_deleted=False)
            # 此时已有的防异常条件： 认证用户、address_id 有， 此判断有无必要
            if address is None:
                return http.HttpResponseForbidden('非正常请求')
            # 逻辑删除，此种删除优于直接删除， 但是需要运维定时清理数据， save保存可以更新数据库的数据最近改动时间
            address.is_deleted = True
            address.save()
        except DatabaseError:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errms': '数据异常'})
        return http.JsonResponse({'code': RETCODE.OK, 'errms': 'OK'})


class SetDefaultAddressView(LoginRequiredView):
    def put(self, request, address_id):
        # 需要先对要修改地址进行校验， 异常及时返回
        try:
            # 直接用Address表进行查数据
            user = request.user
            address = Addresses.objects.get(id=address_id, user=user, is_deleted=False)
            # user对象通过外键访问另一张表(这是一访问多) request.user.addresses是一个query_set
            # address = request.user.addresses.get(id=address_id, user=request.user, is_deleted=False)
            # 此时已有的防异常条件： 认证用户、address_id 有， 此判断有无必要
            if address is None:
                return http.HttpResponseForbidden('非正常请求')
        except DatabaseError:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '数据异常'})

        # 修改成默认地址 ,注意是1。要修改User表中的数据， 2.对象赋予对象，id赋予id
        user.default_address = address
        user.save()
        # user.default_address_id = address_id
        # 前段根据user 的default_address_id属性，
        # 在渲染地址是判断address 的id是否等于default_address_id进行渲染默认地址标记
        # 故无需返回其它数据（user是响应数据）
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class AddressChangeTitleView(LoginRequiredView):
    def put(self, request, address_id):
        # 校验address_id
        try:
            # 直接用Address表进行查数据
            user = request.user
            address = Addresses.objects.get(id=address_id, user=user, is_deleted=False)
            # user对象通过外键访问另一张表(这是一访问多) request.user.addresses是一个query_set
            # address = request.user.addresses.get(id=address_id, user=request.user, is_deleted=False)
            # 此时已有的防异常条件： 认证用户、address_id 有， 此判断有无必要
            if address is None:
                return http.HttpResponseForbidden('非正常请求')
            # 获取title
            json_bytes = request.body.decode()
            title = json.loads(json_bytes).get('title')
            address.title = title
            address.save()
        except DatabaseError:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '数据异常'})
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class ChangePasswordView(LoginRequiredView):
    def get(self, request):
        return render(request, 'user_center_pass.html')

    # 结合js 和html判断是post请求， 未提供请求的url， 所以是向本页面url发出请求
    def post(self, request):
        # 获取从参数
        query_dict = request.POST
        old_pwd = query_dict.get('old_pwd')
        new_pwd = query_dict.get('new_pwd')
        new_cpwd = query_dict.get('new_cpwd')

        # 检查参数
        if not all([old_pwd, new_cpwd, new_pwd]):
            return http.HttpResponseForbidden('参数不全')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_pwd):
            return http.HttpResponseForbidden('原始密码不正确')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_pwd):
            return http.HttpResponseForbidden('新密码不正确')
        if new_pwd != new_cpwd:
            return render(request, 'user_center_pass.html', {'change_pwd_errmsg': '密码不一致'})
        # 业务逻辑  （增删该查）
        try:
            user = request.user
            user.set_password(new_pwd)  # 此中设置密码会时删掉sessionid
            # user.password = new_pwd    # 此中设置密码不会删掉sessionid
            user.save()
        except DatabaseError:
            return http.HttpResponse('数据异常')

        # 删除username cookie, 避免退出后页面还渲染出名字
        # 逻辑与logout 退出相同
        # response = redirect(reverse('users:logout'))
        # logout(request)
        # response.delete_cookie('username')
        return redirect(reverse('users:logout'))


class FindPassword(View):
    """找回密码网页"""
    def get(self, request):
        return render(request, 'find_password.html')


class FindPasswordUniqueMake(View):
    """校验用户"""
    def get(self, request, username):
        # 获取请求参数
        json_dict = request.GET
        text = json_dict.get('text')
        uuid = json_dict.get('image_code_id')

        # 校验uuid 和图片内容
        if not all([text, uuid]):
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数不全'})

        redis_conn = get_redis_connection('verifications')
        redis_text = redis_conn.get(uuid)
        if not redis_text:
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'err_msg': '图形验证码过期'})
        redis_conn.delete(uuid)
        if redis_text.decode().lower() != text.lower():
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'err_msg': '图形码输入不正确'})

        # 校验及判断用户是用手机还是用户名登录
        try:
            if re.match(r'^1[3-9]\d{9}$', username):
                user = User.objects.get(telephone=username)
            else:
                user = User.objects.get(username=username)
        except User.DoesNotExist:
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '用户名或手机号有误'})
        # user = User.objects.filter(Q(username=username) | Q(telephone=username))
        # if user.count != 1:
        #     return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '用户名或手机号有误'})

        # 业务逻辑
        # 获取手机号

        # 响应
        # 生成access_token,带有用户唯一信息
        access_token = generate_access_token(user)
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'access_token': access_token, 'mobile': user.telephone})


class FindPasswordSmsCode(View):
    """发短信"""
    def get(self, request):
        # 获取access_token参数
        access_token = request.GET.get('access_token')
        # 校验参数
        if not access_token:
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数不全'})
        # 根据token获取到手机号
        user = check_access_token(access_token)
        mobile = user.telephone
        # 获取到手机号之后
        redis_conn = get_redis_connection('verifications')
        count = redis_conn.get('sending_flag_%s' % mobile)
        if count:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'err_msg': '频繁访问'})

        # 生成验证码信息
        sms_code = '%06d' % random.randint(0, 999999)
        # 中断显示验证码，性能
        print(sms_code)
        # 保存手机验证码的和手机号
        # 保存手机发送验证码的状态信息
        pl = redis_conn.pipeline()
        pl.setex('sms_code_%s' % mobile, Constants.SMS_CODE_EXPIRE_REDIS, sms_code)
        pl.setex('sending_flag_%s' % mobile, Constants.MOBILE_REQUEST_EXPIRE_REDIS, 1)
        pl.execute()

        # 利用第三方容联云发短信 ,比较花费时间，造成后边返回前台的阻塞
        # CCP().send_template_sms('15029014304', [sms_code, Constans.SMS_CODE_EXPIRE_REDIS//60], 1)

        # 利用celery
        sms_code_send.delay(mobile, sms_code)

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class FindPasswordCheckMsg(View):
    """校验手机"""
    def get(self, request, username):
        # 获取参数
        sms_code = request.GET.get('sms_code')
        if not sms_code:
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数不全'})

        # 两种登录可能
        try:
            if re.match(r'^1[3-9]\d{9}$', username):
                user = User.objects.get(telephone=username,)
            else:
                user = User.objects.get(username=username)
        except User.DoesNotExist:
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '用户名或手机号有误'})

        # 手机验证码校验
        redis_conn = get_redis_connection('verifications')
        redis_sms_code = redis_conn.get('sms_code_%s' % user.telephone)
        # 保证每个手机验证码只能使用一次
        # 且前端无防护此项
        redis_conn.delete(redis_sms_code)
        if redis_sms_code is None:
            return http.HttpResponseForbidden('验证码已过期')  # 正常逻辑是json局部刷新,但此为form请求,暂时用
        if redis_sms_code.decode() != sms_code:
            return http.HttpResponseForbidden('手机验证码不正确')  # 前端给的是form表单请求,不能返回json

        access_token = generate_access_token(user)   # 两次access_token一样， 可以修改
        user_id = user.id

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'access_token':access_token, 'user_id': user_id})


class InstandPassword(View):
    """重置密码"""
    def post(self, request, user_id):
        # 获取参数
        json_dict = json.loads(request.body.decode())
        password = json_dict.get('password')
        password2 = json_dict.get('password2')
        access_token = json_dict.get('access_token')

        # 校验参数
        if not all([password, password2, access_token]):
            return http.HttpResponseForbidden('参数不全')

        if not re.match(r'^[[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('非法注册,密码不符合规范')
        if  password != password2:
            return http.HttpResponseForbidden('非法注册,密码两次输入不一致')

        # 补上access_token校验
        user = check_access_token(access_token)
        if user is None:
            return http.HttpResponseForbidden('token无效')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return http.HttpResponseForbidden('用户不存在')
        user.set_password(password)
        user.save()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class OrderList(LoginRequiredView):
    def get(self, request, page_num):
        user = request.user
        order_query_set = user.orderinfo_set.all().order_by('-create_time')
        # 创建分页器：每页N条记录
        paginator = Paginator(order_query_set, Constants.GOODS_LIST_LIMIT)
        # 获取每页商品数据
        try:
            page_orders = paginator.page(page_num)
        except EmptyPage:
            # 如果page_num不正确，默认给用户404
            return http.HttpResponseNotFound('empty page')
        # 获取列表页总页数
        total_page = paginator.num_pages

        page_orders = []
        for order in order_query_set:
            # 添加订单进来
            pay_method_name = ('支付宝' if order.pay_method == 2 else '货到付款')
            status_name = OrderInfo.ORDER_STATUS_CHOICES[order.status-1][1]
            sku_list = []
            order_sku_list = order.skus.all()
            for order_sku in order_sku_list:
                sku_list.append({
                    'sku_id': order_sku.sku.id,
                    'default_image': order_sku.sku.default_image,
                    'name': order_sku.sku.name,
                    'price': order_sku.sku.price,
                    'count': order_sku.count,
                    'amount': (order_sku.sku.price * order_sku.count)
                })
            page_orders.append({
                'create_time': order.create_time,
                'order_id': order.order_id,
                'total_amount': order.total_amount,
                'freight': order.freight,
                'pay_method_name': pay_method_name,
                'status': order.status,
                'status_name': status_name,
                'sku_list': sku_list
            })
        context = {
            'page_orders': page_orders,  # 分页后数据
            'total_page': total_page,  # 总页数
            'page_num': page_num,  # 当前页码
        }
        return render(request, 'user_center_order.html', context)



class OrderComment(LoginRequiredView):
    def get(self, request):
        order_id = request.GET.get('order_id')
        try:
            order = OrderInfo.objects.get(order_id=order_id)
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('非法请求')
        order_sku_list = order.skus.all().order_by()
        sku_list = []
        for order_sku in order_sku_list:
            sku_list.append({
                'order_id': order_id,
                'sku_id': order_sku.sku_id,
                'default_image_url': order_sku.sku.default_image.url,
                'name': order_sku.sku.name,
                'price': str(order_sku.sku.price),
                'comment': order_sku.comment,
                'score': order_sku.count,
                'amount': str(order_sku.sku.price * order_sku.count)
            })

        return render(request, 'goods_judge.html', {'uncomment_goods_list': sku_list})

    def post(self,request):
        """保存评价"""
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        order_id = json_dict.get('order_id')
        comment = json_dict.get('comment')
        score = json_dict.get('score')
        is_anonymous = json_dict.get('is_anonymous')
        # 校验参数
        if not all([sku_id, order_id, comment, score]):
            return http.HttpResponseForbidden('参数不全')
        try:
            order = OrderInfo.objects.get(order_id=order_id)
            order_sku = OrderGoods.objects.get(order_id=order_id, sku_id=sku_id)
        except DatabaseError:
            return http.HttpResponseForbidden('非法请求')
        if not isinstance(is_anonymous, bool):
            return http.HttpResponseForbidden('非法请求')
        if len(comment) < 5:
            return http.HttpResponseForbidden('非法请求')
        if score > 5 or score < 0:
            return http.HttpResponseForbidden('非法请求')
        with transaction.atomic():
            save_point = transaction.savepoint()
            try:
                order_sku.comment = comment
                order_sku.score = score
                order_sku.is_anonymous = is_anonymous
                order_sku.is_commented = True
                order_sku.save()
                sku = order_sku.sku
                comments = sku.comments
                sku.comments = comments + 1
                sku.save()
                order.status = 5
                order.save()
            except Exception:
                transaction.savepoint_rollback(save_point)
            transaction.savepoint_commit(save_point)
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


