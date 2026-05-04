from django.shortcuts import render

def dashboard(request):
    return render(request, 'dashboard/dashboard.html')

def seo_audit(request):
    return render(request, 'dashboard/seo_audit.html')

def keywords(request):
    return render(request, 'dashboard/keywords.html')

def backlinks(request):
    return render(request, 'dashboard/backlinks.html')

def competitors(request):
    return render(request, 'dashboard/competitors.html')

def settings(request):
    return render(request, 'dashboard/settings.html')

def pricing(request):
    return render(request, 'dashboard/pricing.html')

def landing_page(request):
    return render(request, 'dashboard/landing.html')
