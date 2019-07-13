from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin


class LoginRequiredView(LoginRequiredMixin, View):
    """判断用户登录类"""
    # 继承此类的是已经登录的用户  
    """在路由中的调用时使用了， 所以继承该类的,可以做登录验证，获取request.user肯定得到一个用户而不是匿名用户"""
    pass