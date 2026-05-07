from django.urls import path
from . import views

urlpatterns = [
    # Main pages
    path('', views.dashboard, name='dashboard'),
    path('audit/', views.seo_audit, name='seo_audit'),
    path('keywords/', views.keywords, name='keywords'),
    path('backlinks/', views.backlinks, name='backlinks'),
    path('competitors/', views.competitors, name='competitors'),
    path('settings/', views.settings_view, name='settings'),
    path('pricing/', views.pricing, name='pricing'),
    path('landing/', views.landing_page, name='landing_page'),

    # Keyword CRUD
    path('keywords/add/', views.add_keyword, name='add_keyword'),
    path('keywords/<int:pk>/edit/', views.edit_keyword, name='edit_keyword'),
    path('keywords/<int:pk>/delete/', views.delete_keyword, name='delete_keyword'),

    # Backlink CRUD
    path('backlinks/add/', views.add_backlink, name='add_backlink'),
    path('backlinks/<int:pk>/delete/', views.delete_backlink, name='delete_backlink'),

    # Competitor CRUD
    path('competitors/add/', views.add_competitor, name='add_competitor'),
    path('competitors/<int:pk>/delete/', views.delete_competitor, name='delete_competitor'),

    # Audit Issue CRUD
    path('audit/issues/add/', views.add_audit_issue, name='add_audit_issue'),
    path('audit/issues/<int:pk>/delete/', views.delete_audit_issue, name='delete_audit_issue'),
]
