from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Avg
from .models import Project, AuditResult, AuditIssue, Keyword, Backlink, Competitor
from .forms import KeywordForm, BacklinkForm, CompetitorForm, ProjectForm, AuditIssueForm


# ───────────────────────────────────────────────
# Helper: get active project (first in DB)
# ───────────────────────────────────────────────
def get_project():
    return Project.objects.first()


# ───────────────────────────────────────────────
# DASHBOARD
# ───────────────────────────────────────────────
def dashboard(request):
    project = get_project()
    context = {}
    if project:
        audit = getattr(project, 'audit', None)
        all_keywords = project.keywords.all()
        context['project'] = project
        context['audit'] = audit
        context['keywords'] = all_keywords[:10]
        context['backlinks_count'] = project.backlinks.count()
        context['new_backlinks_count'] = project.backlinks.filter(is_new=True).count()
        context['top_3_keywords'] = all_keywords.filter(rank__lte=3).count()
        context['positive_rank_changes'] = sum(1 for k in all_keywords if k.rank_change > 0)
        context['alerts'] = project.audit.issues.filter(severity='critical').order_by('-id')[:3] if audit else []
    return render(request, 'dashboard/dashboard.html', context)


# ───────────────────────────────────────────────
# SEO AUDIT
# ───────────────────────────────────────────────
def seo_audit(request):
    project = get_project()
    context = {'project': project}
    if project:
        audit = getattr(project, 'audit', None)
        context['audit'] = audit
        if audit:
            context['critical_issues'] = audit.issues.filter(severity='critical')
            context['warning_issues'] = audit.issues.filter(severity='warning')
            context['passed_issues'] = audit.issues.filter(severity='passed')
    return render(request, 'dashboard/seo_audit.html', context)


def add_audit_issue(request):
    project = get_project()
    audit = getattr(project, 'audit', None) if project else None
    if not audit:
        messages.error(request, "No audit found for this project.")
        return redirect('seo_audit')
    if request.method == 'POST':
        form = AuditIssueForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.audit = audit
            issue.save()
            messages.success(request, "Audit issue added successfully.")
            return redirect('seo_audit')
    else:
        form = AuditIssueForm()
    return render(request, 'dashboard/issue_form.html', {'form': form, 'title': 'Add Audit Issue'})


def delete_audit_issue(request, pk):
    issue = get_object_or_404(AuditIssue, pk=pk)
    if request.method == 'POST':
        issue.delete()
        messages.success(request, "Issue deleted.")
    return redirect('seo_audit')


# ───────────────────────────────────────────────
# KEYWORDS
# ───────────────────────────────────────────────
def keywords(request):
    project = get_project()
    kw_list = project.keywords.all().order_by('rank') if project else Keyword.objects.none()
    form = KeywordForm()
    context = {
        'project': project,
        'keywords': kw_list,
        'form': form,
        'total_keywords': kw_list.count(),
        'avg_difficulty': round(kw_list.aggregate(avg=Avg('difficulty'))['avg'] or 0, 2),
    }
    return render(request, 'dashboard/keywords.html', context)


def add_keyword(request):
    project = get_project()
    if not project:
        messages.error(request, "No project found.")
        return redirect('keywords')
    if request.method == 'POST':
        form = KeywordForm(request.POST)
        if form.is_valid():
            kw = form.save(commit=False)
            kw.project = project
            kw.save()
            messages.success(request, f'Keyword "{kw.keyword}" added successfully.')
        else:
            messages.error(request, "Please fix the errors below.")
    return redirect('keywords')


def edit_keyword(request, pk):
    kw = get_object_or_404(Keyword, pk=pk)
    if request.method == 'POST':
        form = KeywordForm(request.POST, instance=kw)
        if form.is_valid():
            form.save()
            messages.success(request, f'Keyword "{kw.keyword}" updated.')
            return redirect('keywords')
    else:
        form = KeywordForm(instance=kw)
    return render(request, 'dashboard/keyword_form.html', {'form': form, 'kw': kw, 'title': 'Edit Keyword'})


def delete_keyword(request, pk):
    kw = get_object_or_404(Keyword, pk=pk)
    if request.method == 'POST':
        name = kw.keyword
        kw.delete()
        messages.success(request, f'Keyword "{name}" deleted.')
    return redirect('keywords')


# ───────────────────────────────────────────────
# BACKLINKS
# ───────────────────────────────────────────────
def backlinks(request):
    project = get_project()
    bl_list = project.backlinks.all().order_by('-found_at') if project else Backlink.objects.none()
    form = BacklinkForm()
    context = {
        'project': project,
        'backlinks': bl_list,
        'form': form,
        'total_backlinks': bl_list.count(),
        'new_backlinks': bl_list.filter(is_new=True).count(),
        'avg_authority': round(bl_list.aggregate(avg=Avg('domain_authority'))['avg'] or 0),
    }
    return render(request, 'dashboard/backlinks.html', context)


def add_backlink(request):
    project = get_project()
    if not project:
        messages.error(request, "No project found.")
        return redirect('backlinks')
    if request.method == 'POST':
        form = BacklinkForm(request.POST)
        if form.is_valid():
            bl = form.save(commit=False)
            bl.project = project
            bl.save()
            messages.success(request, 'Backlink added successfully.')
        else:
            messages.error(request, "Please fix the errors.")
    return redirect('backlinks')


def delete_backlink(request, pk):
    bl = get_object_or_404(Backlink, pk=pk)
    if request.method == 'POST':
        bl.delete()
        messages.success(request, 'Backlink deleted.')
    return redirect('backlinks')


# ───────────────────────────────────────────────
# COMPETITORS
# ───────────────────────────────────────────────
def competitors(request):
    project = get_project()
    comp_list = project.competitors.all().order_by('-domain_rating') if project else Competitor.objects.none()
    form = CompetitorForm()
    context = {
        'project': project,
        'competitors': comp_list,
        'form': form,
    }
    return render(request, 'dashboard/competitors.html', context)


def add_competitor(request):
    project = get_project()
    if not project:
        messages.error(request, "No project found.")
        return redirect('competitors')
    if request.method == 'POST':
        form = CompetitorForm(request.POST)
        if form.is_valid():
            comp = form.save(commit=False)
            comp.project = project
            comp.save()
            messages.success(request, f'Competitor "{comp.name}" added.')
        else:
            messages.error(request, "Please fix the errors.")
    return redirect('competitors')


def delete_competitor(request, pk):
    comp = get_object_or_404(Competitor, pk=pk)
    if request.method == 'POST':
        comp.delete()
        messages.success(request, 'Competitor removed.')
    return redirect('competitors')


# ───────────────────────────────────────────────
# SETTINGS
# ───────────────────────────────────────────────
def settings_view(request):
    project = get_project()
    form = ProjectForm(instance=project)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project settings saved.')
            return redirect('settings')
    context = {'project': project, 'form': form}
    return render(request, 'dashboard/settings.html', context)


# ───────────────────────────────────────────────
# PRICING
# ───────────────────────────────────────────────
def pricing(request):
    return render(request, 'dashboard/pricing.html')


# ───────────────────────────────────────────────
# LANDING
# ───────────────────────────────────────────────
def landing_page(request):
    return render(request, 'dashboard/landing.html')
