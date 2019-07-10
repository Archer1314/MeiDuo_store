#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    execute_from_command_line(sys.argv)


# 2019.7.3 已安装ok
# amqp==2.4.2
# billiard==3.6.0.0
# celery==4.3.0                 ok
# certifi==2019.3.9
# chardet==3.0.4
# Django==1.11.11               ok
# django-crontab==0.7.1
# django-haystack==2.8.1
# django-redis==4.10.0          ok
# elasticsearch==2.4.1
# idna==2.8
# itsdangerous==1.1.0           ok
# Jinja2==2.10.1                ok
# kombu==4.5.0
# MarkupSafe==1.1.1
# mutagen==1.42.0
# pika==1.0.1
# Pillow==6.0.0                 ok
# pycryptodomex==3.7.2
# PyMySQL==0.9.3                ok
# python-alipay-sdk==1.10.0
# pytz==2019.1                  ok
# QQLoginTool==0.3.0            ok
# redis==3.2.1                  ok
# requests==2.21.0
# urllib3==1.24.2
# uWSGI==2.0.18
# vine==1.3.0
