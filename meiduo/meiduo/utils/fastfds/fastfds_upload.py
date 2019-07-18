from fdfs_client.client import Fdfs_client

# 上传下载的客户端类
# 创建客户端实例, 指定配置文件(类似redis、mysql)
fds_client = Fdfs_client('./client.conf')
# 指定要上传的文件，注意必须要能找到要上传的文件：如图片
img_file_id = fds_client.upload_by_filename('/home/python/Desktop/20.png')

# 成功会返回file_id， 后续根据该id拿下载图片
# print(img_file_id)
# {
# 'Group name': 'group1',
# 'Remote file_id': 'group1/M00/00/00/wKjqgV0sQ1yAe3FKAAIADxjeIsQ986.png',
# 'Status': 'Upload successed.',
# 'Local file name': '/home/python/Desktop/20.png',
# 'Uploaded size': '128.00KB',
# 'Storage IP': '192.168.234.129'}

# Fastfds 的服务器只负责存储和管理（file_id 解决每个文件的唯一性）
# 客户端要负责上传和判断是否重复（存储的两大问题， 重复和唯一性， 重复性需要开发者自己制定逻辑进行判断：如读取校验）

# 下载(获取)的方法， 是根据http协议进行获取的，故将 Nginx 服务器绑定到 Storage：
# 1、网址：配置/安装trucker是的配置ip，端口：8888 ，本次的配置是：192.168.234.129:8888 访问的是Nginx（HTTP服务器负载）
# Nginx是一款自由的、开源的、高性能的HTTP服务器和反向代理服务器；同时也是一个IMAP、POP3、SMTP代理服务器；
# Nginx可以作为一个HTTP服务器进行网站的发布处理，另外Nginx可以作为反向代理进行负载均衡的实现。
# 2、资源路径，因为是绑定到Storage， 故近需file_id 即可
