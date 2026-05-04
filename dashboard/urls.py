from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('audit/', views.seo_audit, name='seo_audit'),
    path('keywords/', views.keywords, name='keywords'),
    path('backlinks/', views.backlinks, name='backlinks'),
    path('competitors/', views.competitors, name='competitors'),
    path('settings/', views.settings, name='settings'),
    path('pricing/', views.pricing, name='pricing'),
    path('landing/', views.landing_page, name='landing_page'),
]
