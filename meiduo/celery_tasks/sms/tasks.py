from celery_tasks.yuntongxun.sms import CCP
from celery_tasks.yuntongxun.constans import Constans
from celery_tasks.main import celery_app


@celery_app.tasks(name='sms_code_send')
def sms_code_send(mobile, sms_code):
    CCP().send_template_sms(mobile, [sms_code, Constans.SMS_CODE_EXPIRE_REDIS // 60], 1)