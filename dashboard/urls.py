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

    # Live URL Analyzer
    path('analyze/', views.analyze_url, name='analyze_url'),

    # Project management
    path('projects/create/', views.create_project, name='create_project'),
    path('projects/<int:pk>/switch/', views.switch_project, name='switch_project'),
    path('projects/<int:pk>/delete/', views.delete_project, name='delete_project'),

    # Keyword CRUD + export
    path('keywords/add/', views.add_keyword, name='add_keyword'),
    path('keywords/<int:pk>/edit/', views.edit_keyword, name='edit_keyword'),
    path('keywords/<int:pk>/delete/', views.delete_keyword, name='delete_keyword'),
    path('keywords/export/', views.export_keywords_csv, name='export_keywords_csv'),

    # Backlink CRUD + export
    path('backlinks/add/', views.add_backlink, name='add_backlink'),
    path('backlinks/<int:pk>/delete/', views.delete_backlink, name='delete_backlink'),
    path('backlinks/export/', views.export_backlinks_csv, name='export_backlinks_csv'),

    # Competitor CRUD
    path('competitors/add/', views.add_competitor, name='add_competitor'),
    path('competitors/<int:pk>/delete/', views.delete_competitor, name='delete_competitor'),

    # Audit Issue CRUD
    path('audit/issues/add/', views.add_audit_issue, name='add_audit_issue'),
    path('audit/issues/<int:pk>/delete/', views.delete_audit_issue, name='delete_audit_issue'),
]
