from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser, AllowAny
from meiduo_admin.serializers.login_home_serializers import UserModelSerializer, GoodsVisitCountSerializers
from rest_framework.decorators import action
from users.models import User
from goods.models import GoodsVisitCount
from meiduo_admin.utils.localtime import cur_0_time

# Create your views here.


class Login(APIView):
    """登录后台管理"""
    # 会签发一个token，代表是超级用户

    def post(self, request):
        # 调用序列化器
        serializer = UserModelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(data={
            'username': serializer.validated_data['user'].username,
            'user_id': serializer.validated_data['user'].id,
            'token': serializer.validated_data.get('token')
        })


class IndexManageMessage(ViewSet):
    """主页的信息"""
    # permission_classes = [IsAdminUser]
    # 有token才能访问， 已证明是超级用户， 但为避免超级用户降成普通用户仍可使用token登录， 增加is_staff 为True校验

    def get_permissions(self):
        """对某些视图函数进行权限要求"""
        if self.action == 'total_count' or self.action == 'day_increment':
            return [IsAdminUser()]
        return [AllowAny()]
    # 重写函数，实现对特定接口的权限限制
    # def get_permissions(self):
    #     """
    #     处理的视图函数是totoal_count时，所用的权限检查类对象是IsAdminUser
    #     别的视图处理函数，所使用的权限检查类对象是AllowAny
    #     :return: 权限检查类对象
    #     """
    #     # if 视图方法是total_count：
    #     #     返回 [IsAdminUser()]
    #     # 返回 [AllowAny()]
    #
    #     # self.action代表的是档前请求，视图对象所采用的视图方法
    #     if self.action == "total_count" or self.action == "day_increment":
    #         return [IsAdminUser()] # 后续权限校验，会依次提取该列表中的权限检查对象，进行检查
    #     return [AllowAny()]

    @action(methods=['get'], detail=False)
    def total_count(self, request):
        # 1、计算用户数量和日期
        count = User.objects.count()
        date = timezone.now().date()
        # 2、构建响应数据
        return Response({
            "count": count,
            "date": date
        })

    @action(methods=['get'], detail=False)
    def day_increment(self, request):
        # 用户新建的日期，大于等于"当日"的"零点零分零秒"
        # 就是当日新增
        # 2、根据当日零时，过滤用户表
        count = User.objects.filter(date_joined__gte=cur_0_time).count()

        return Response({
            "count": count,
            "date": cur_0_time.date() # 2019-8-3
        })

    @action(methods=['get'], detail=False)
    def day_active(self, request):
        # 1、获取当日零点
        # 2、过滤最后登陆日期大于等于当日零点
        count = User.objects.filter(last_login__gte=cur_0_time).count()

        # 3、返回
        return Response({
            "count": count,
            "date": cur_0_time.date()
        })

    @action(methods=['get'], detail=False)
    def day_orders(self, request):
        # 统计今天下单的用户数量
        # 已知条件：今天的零点（订单的创建时间） --> 从表的已知条件
        # 目标数据：用户数量 --> 主表数据

        # 1、统计出今天下的订单
        # local_0_time = timezone.now().astimezone(tz=pytz.timezone(settings.TIME_ZONE))\
        #     .replace(hour=0, minute=0, second=0, microsecond=0)
        # cur_0_time = local_0_time

        # 从从表入手
        # 2.1、找出今天下的所有订单
        # order_queryset = OrderInfo.objects.filter(create_time__gte=local_0_time)
        # 2.2 取出每个从表对象关联的主表，并统计主表数据
        # user_list = []
        # for order in order_queryset:
            # order是单一的订单对象
            # user_list.append(order.user)
        # count = len(set(user_list))

        # 从主表入手

        user_queryset = User.objects.filter(orderinfo__create_time__gte=cur_0_time)
        count = len(set(user_queryset))

        # 3、返回
        return Response({
            "count": count,
            "date": cur_0_time.date()
        })

    @action(methods=['get'], detail=False)
    def month_increment(self, request):
        # 统计最近30天，每一天新增用户
        # 1、当天的时间点
        # 2019-8-3 0:0:0
        # cur_0_time = timezone.now().astimezone(pytz.timezone(settings.TIME_ZONE))\
        #     .replace(hour=0, second=0, minute=0, microsecond=0)
        # 2、起始时间点
        # 起始时间点 = 当天的时间点 - （统计天数 - 一天）
        begin_0_time = cur_0_time - timedelta(days=29)

        calc_list = []
        for index in range(30):
            # calc_0_time：30天中的某一天
            calc_0_time = begin_0_time + timedelta(days=index)

            count = User.objects.filter(date_joined__gte=calc_0_time,
                                        date_joined__lt=calc_0_time+timedelta(days=1)).count()


            calc_list.append({
                "count": count,
                "date": calc_0_time.date()
            })

        return Response(calc_list)


class GoodVisitCountView(ListAPIView):
    """商品种类每日访问的次数统计"""
    permission_classes = [IsAdminUser]   # isAdminUser --> is_staff 为True， 必须是超级用户才能访问该试图

    queryset = GoodsVisitCount.objects.all()
    serializer_class = GoodsVisitCountSerializers

    def get_queryset(self):
        """重写获取集合--今日的"""
        return self.queryset.filter(create_time__gte=cur_0_time)

