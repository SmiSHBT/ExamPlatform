from django.urls import path
from . import views
urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('tests/', views.tests_list, name='tests_list'),
    path('test/<int:test_id>/start/', views.test_start, name='test_start'),
    path('test/<int:test_id>/save-focus/', views.save_focus, name='save_focus'),
    path('test/<int:test_id>/submit/', views.test_submit, name='test_submit'),
    path('test/<int:test_id>/screenshot/', views.save_screenshot, name='save_screenshot'),
    path('tests/upload/', views.upload_test, name='upload_test'),
    path('', views.index),
]
