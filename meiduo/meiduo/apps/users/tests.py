# from django.views.generic.base import View
# from rest_framework.views import APIView
# from django.conf import settings
#!/usr/bin/env python


# def func():
#     fun_list = []
#     for i in range(4):
#         def foo(x, i=i):
#             return x*i
#         fun_list.append(foo)
#     return fun_list
#
#
# for m in func():
#     print(m(2))

class SingleTool(object):
    __instance = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def addxnum(self,*args):
        my_sum = 0
        for value in args:
            my_sum +=value
        return my_sum


t1 = SingleTool()
print(t1.addxnum(1,2,3))
print(t1)
t2=SingleTool()
print(t2)


a = [(i-2, i-1, i) for i in range(1, 100) if i % 3 == 0]
print(a)
print([[x for x in range(1,100)][i:i+3] for i in range(0, 100, 3)])