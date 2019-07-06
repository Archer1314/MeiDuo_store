from celery import Celery

# 本文件为启动文件
# 实例化生产对象
celery_app = Celery('meiduo')

# 配置该应用的的中间人,消息仓库
celery_app.config_from_object('celery_tasks.config')

# 指定要进行的任务
# sms下设置任务的文件名必须为tasks,此处不用写完,后续默认补齐,,列表是为了可设置多个任务文件,默认为空
celery_app.autodiscover_tasks(['celery_tasks.sms'])
