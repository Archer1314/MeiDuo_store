from celery_tasks.sms.yuntongxun.sms import CCP
from celery_tasks.sms import constants
from celery_tasks.main import celery_app


@celery_app.task()
def sms_code_send(mobile, sms_code):
    CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_EXPIRE_REDIS // 60], 1)