from django.urls import path
from . import views

urlpatterns = [

    path('', views.show_directories, name='find'),
    path('directories', views.find_directories, name='scan'),
    path('dir', views.show_directories, name='find'),
    path('sub', views.show_subdomains, name='subdomains'),
    path('subdomains', views.find_subdomains, name='scan_domain'),

    
]


