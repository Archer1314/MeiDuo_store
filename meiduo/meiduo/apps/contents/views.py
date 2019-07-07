from django import http
from django.shortcuts import render
from django.views import View


# Create your views here.
class IndexContents(View):
    def get(self, request):
        response = render(request, 'index.html')
        return response


