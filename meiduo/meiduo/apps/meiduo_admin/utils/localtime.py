from django.utils import timezone
import pytz
from django.conf import settings

cur_0_time = timezone.now().astimezone(pytz.timezone(settings.TIME_ZONE))\
            .replace(hour=0, second=0, minute=0, microsecond=0)

# 1、获取当日的零时: 上海的零时
# 时间类：年，月，日，时，分，秒，时区

# 2019-08-03 08:09:26.987697 +00:00
# cur_date = timezone.now()
#
# # 2019-08-03 16:09:26.987697 +08:00
# shanghai_date = cur_date.astimezone(tz=pytz.timezone(settings.TIME_ZONE))
#
# # 上海的零时
# # 2019-08-03 00:00:00.000000 +08:00
# shanghai_0_date = shanghai_date.replace(hour=0, minute=0, second=0, microsecond=0)