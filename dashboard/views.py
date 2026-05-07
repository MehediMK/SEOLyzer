import csv
import requests
from urllib.parse import urlparse

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AuditIssueForm, BacklinkForm, CompetitorForm, KeywordForm, ProjectForm
from .models import AuditIssue, AuditResult, Backlink, Competitor, Keyword, Project


# ───────────────────────────────────────────────
# Helper: get project scoped to current user
# ───────────────────────────────────────────────
def get_user_project(request, pk=None):
    """Return the requested project (or first) for the logged-in user."""
    qs = Project.objects.filter(user=request.user)
    if pk:
        return get_object_or_404(qs, pk=pk)
    # Use session-stored active project, or fallback to first
    active_pk = request.session.get('active_project_pk')
    if active_pk:
        project = qs.filter(pk=active_pk).first()
        if project:
            return project
    return qs.first()


# ───────────────────────────────────────────────
# PROJECT SWITCHER
# ───────────────────────────────────────────────
@login_required
def switch_project(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    request.session['active_project_pk'] = project.pk
    messages.success(request, f'Switched to project: {project.name}')
    return redirect('dashboard')


@login_required
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user
            project.save()
            # Auto-create empty audit
            AuditResult.objects.create(project=project)
            request.session['active_project_pk'] = project.pk
            messages.success(request, f'Project "{project.name}" created! Analyze it now.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = ProjectForm()
    return render(request, 'dashboard/project_form.html', {'form': form, 'title': 'Create New Project'})


@login_required
def delete_project(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    if request.method == 'POST':
        name = project.name
        # Clear session if this was the active project
        if request.session.get('active_project_pk') == pk:
            del request.session['active_project_pk']
        project.delete()
        messages.success(request, f'Project "{name}" deleted.')
    return redirect('dashboard')


# ───────────────────────────────────────────────
# LIVE URL ANALYZER
# ───────────────────────────────────────────────
@login_required
def analyze_url(request):
    """Fetch basic on-page SEO data from any URL and show results."""
    result = None
    error = None
    url = ''

    if request.method == 'POST':
        url = request.POST.get('url', '').strip()
        if not url:
            error = 'Please enter a URL.'
        else:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            try:
                result = _scrape_url(url)
                # Optionally fetch PageSpeed if API key is set
                if settings.GOOGLE_PAGESPEED_API_KEY:
                    result['pagespeed'] = _fetch_pagespeed(url)
            except Exception as e:
                error = f'Could not analyze URL: {str(e)}'

    return render(request, 'dashboard/analyze_url.html', {
        'url': url,
        'result': result,
        'error': error,
        'projects': Project.objects.filter(user=request.user),
    })


def _scrape_url(url):
    """Scrape basic SEO elements from a URL using requests + BeautifulSoup."""
    from bs4 import BeautifulSoup

    headers = {'User-Agent': 'Mozilla/5.0 (compatible; SEOInsightBot/1.0)'}
    resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
    soup = BeautifulSoup(resp.text, 'html.parser')

    # Title
    title_tag = soup.find('title')
    title = title_tag.get_text(strip=True) if title_tag else ''

    # Meta description
    meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
    meta_desc = meta_desc_tag.get('content', '') if meta_desc_tag else ''

    # H1 tags
    h1_tags = [h.get_text(strip=True) for h in soup.find_all('h1')]

    # Canonical
    canonical_tag = soup.find('link', rel='canonical')
    canonical = canonical_tag.get('href', '') if canonical_tag else ''

    # Robots meta
    robots_tag = soup.find('meta', attrs={'name': 'robots'})
    robots = robots_tag.get('content', '') if robots_tag else 'index, follow (default)'

    # Images without alt
    all_images = soup.find_all('img')
    images_without_alt = [img.get('src', '')[:80] for img in all_images if not img.get('alt')]

    # Internal links
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    all_links = soup.find_all('a', href=True)
    internal_links = [a['href'] for a in all_links if a['href'].startswith(base) or a['href'].startswith('/')]
    external_links = [a['href'] for a in all_links if a['href'].startswith('http') and base not in a['href']]

    # Issues detection
    issues = []
    if not title:
        issues.append({'type': 'critical', 'msg': 'Missing <title> tag'})
    elif len(title) > 70:
        issues.append({'type': 'warning', 'msg': f'Title too long: {len(title)} chars (recommended ≤ 60)'})
    elif len(title) < 30:
        issues.append({'type': 'warning', 'msg': f'Title too short: {len(title)} chars (recommended ≥ 30)'})
    else:
        issues.append({'type': 'passed', 'msg': f'Title length is good: {len(title)} chars'})

    if not meta_desc:
        issues.append({'type': 'critical', 'msg': 'Missing meta description'})
    elif len(meta_desc) > 160:
        issues.append({'type': 'warning', 'msg': f'Meta description too long: {len(meta_desc)} chars'})
    else:
        issues.append({'type': 'passed', 'msg': f'Meta description found: {len(meta_desc)} chars'})

    if not h1_tags:
        issues.append({'type': 'critical', 'msg': 'No <h1> tag found'})
    elif len(h1_tags) > 1:
        issues.append({'type': 'warning', 'msg': f'Multiple H1 tags found ({len(h1_tags)}). Use only one.'})
    else:
        issues.append({'type': 'passed', 'msg': 'Exactly one H1 tag found'})

    if images_without_alt:
        issues.append({'type': 'warning', 'msg': f'{len(images_without_alt)} image(s) missing alt text'})
    elif all_images:
        issues.append({'type': 'passed', 'msg': f'All {len(all_images)} images have alt text'})

    if not canonical:
        issues.append({'type': 'warning', 'msg': 'No canonical URL tag found'})
    else:
        issues.append({'type': 'passed', 'msg': f'Canonical URL set: {canonical[:60]}'})

    # SSL
    if url.startswith('https://'):
        issues.append({'type': 'passed', 'msg': 'HTTPS / SSL is active'})
    else:
        issues.append({'type': 'critical', 'msg': 'Site is not using HTTPS (SSL)'})

    # Redirect check
    if resp.url != url:
        issues.append({'type': 'warning', 'msg': f'Redirect detected: {url} → {resp.url[:80]}'})

    score = _calculate_score(issues)

    return {
        'url': url,
        'final_url': resp.url,
        'status_code': resp.status_code,
        'title': title,
        'title_length': len(title),
        'meta_desc': meta_desc,
        'meta_desc_length': len(meta_desc),
        'h1_tags': h1_tags,
        'canonical': canonical,
        'robots': robots,
        'images_total': len(all_images),
        'images_without_alt': images_without_alt[:5],
        'images_without_alt_count': len(images_without_alt),
        'internal_links_count': len(internal_links),
        'external_links_count': len(external_links),
        'issues': issues,
        'score': score,
        'score_label': 'Excellent' if score >= 80 else ('Good' if score >= 60 else 'Needs Work'),
    }


def _calculate_score(issues):
    """Simple score: each passed = +points, each critical = -big, warning = -small."""
    score = 100
    for issue in issues:
        if issue['type'] == 'critical':
            score -= 20
        elif issue['type'] == 'warning':
            score -= 8
    return max(0, min(100, score))


def _fetch_pagespeed(url):
    """Fetch Core Web Vitals from Google PageSpeed Insights API."""
    api_key = settings.GOOGLE_PAGESPEED_API_KEY
    api_url = (
        f'https://www.googleapis.com/pagespeedonline/v5/runPagespeed'
        f'?url={url}&strategy=mobile&key={api_key}'
        f'&category=performance&category=seo&category=accessibility'
    )
    try:
        resp = requests.get(api_url, timeout=30)
        data = resp.json()
        cats = data.get('lighthouseResult', {}).get('categories', {})
        audits = data.get('lighthouseResult', {}).get('audits', {})
        return {
            'performance': int((cats.get('performance', {}).get('score', 0) or 0) * 100),
            'seo': int((cats.get('seo', {}).get('score', 0) or 0) * 100),
            'accessibility': int((cats.get('accessibility', {}).get('score', 0) or 0) * 100),
            'lcp': audits.get('largest-contentful-paint', {}).get('displayValue', 'N/A'),
            'fid': audits.get('max-potential-fid', {}).get('displayValue', 'N/A'),
            'cls': audits.get('cumulative-layout-shift', {}).get('displayValue', 'N/A'),
            'fcp': audits.get('first-contentful-paint', {}).get('displayValue', 'N/A'),
            'tbt': audits.get('total-blocking-time', {}).get('displayValue', 'N/A'),
        }
    except Exception:
        return None


# ───────────────────────────────────────────────
# DASHBOARD
# ───────────────────────────────────────────────
@login_required
def dashboard(request):
    all_projects = Project.objects.filter(user=request.user)
    project = get_user_project(request)
    context = {'all_projects': all_projects, 'project': project}
    if project:
        audit = getattr(project, 'audit', None)
        all_keywords = project.keywords.all()
        context.update({
            'audit': audit,
            'keywords': all_keywords[:10],
            'backlinks_count': project.backlinks.count(),
            'new_backlinks_count': project.backlinks.filter(is_new=True).count(),
            'top_3_keywords': all_keywords.filter(rank__lte=3).count(),
            'positive_rank_changes': sum(1 for k in all_keywords if k.rank_change > 0),
            'alerts': audit.issues.filter(severity='critical').order_by('-id')[:3] if audit else [],
        })
    return render(request, 'dashboard/dashboard.html', context)


# ───────────────────────────────────────────────
# SEO AUDIT
# ───────────────────────────────────────────────
@login_required
def seo_audit(request):
    project = get_user_project(request)
    context = {'project': project, 'all_projects': Project.objects.filter(user=request.user)}
    if project:
        audit = getattr(project, 'audit', None)
        context['audit'] = audit
        if audit:
            context['critical_issues'] = audit.issues.filter(severity='critical')
            context['warning_issues'] = audit.issues.filter(severity='warning')
            context['passed_issues'] = audit.issues.filter(severity='passed')
    return render(request, 'dashboard/seo_audit.html', context)


@login_required
def add_audit_issue(request):
    project = get_user_project(request)
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


@login_required
def delete_audit_issue(request, pk):
    issue = get_object_or_404(AuditIssue, pk=pk)
    if request.method == 'POST':
        issue.delete()
        messages.success(request, "Issue deleted.")
    return redirect('seo_audit')


# ───────────────────────────────────────────────
# KEYWORDS
# ───────────────────────────────────────────────
@login_required
def keywords(request):
    project = get_user_project(request)
    kw_list = project.keywords.all().order_by('rank') if project else Keyword.objects.none()
    form = KeywordForm()
    context = {
        'project': project,
        'all_projects': Project.objects.filter(user=request.user),
        'keywords': kw_list,
        'form': form,
        'total_keywords': kw_list.count(),
        'avg_difficulty': round(kw_list.aggregate(avg=Avg('difficulty'))['avg'] or 0, 2),
    }
    return render(request, 'dashboard/keywords.html', context)


@login_required
def add_keyword(request):
    project = get_user_project(request)
    if not project:
        messages.error(request, "No project found. Create one first.")
        return redirect('create_project')
    if request.method == 'POST':
        form = KeywordForm(request.POST)
        if form.is_valid():
            kw = form.save(commit=False)
            kw.project = project
            kw.save()
            messages.success(request, f'Keyword "{kw.keyword}" added.')
        else:
            messages.error(request, "Please fix the errors.")
    return redirect('keywords')


@login_required
def edit_keyword(request, pk):
    kw = get_object_or_404(Keyword, pk=pk, project__user=request.user)
    if request.method == 'POST':
        form = KeywordForm(request.POST, instance=kw)
        if form.is_valid():
            form.save()
            messages.success(request, f'Keyword "{kw.keyword}" updated.')
            return redirect('keywords')
    else:
        form = KeywordForm(instance=kw)
    return render(request, 'dashboard/keyword_form.html', {'form': form, 'kw': kw, 'title': 'Edit Keyword'})


@login_required
def delete_keyword(request, pk):
    kw = get_object_or_404(Keyword, pk=pk, project__user=request.user)
    if request.method == 'POST':
        name = kw.keyword
        kw.delete()
        messages.success(request, f'Keyword "{name}" deleted.')
    return redirect('keywords')


@login_required
def export_keywords_csv(request):
    project = get_user_project(request)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="keywords.csv"'
    writer = csv.writer(response)
    writer.writerow(['Keyword', 'Rank', 'Previous Rank', 'Change', 'Volume', 'CPC', 'Difficulty', 'Intent', 'Trend'])
    for kw in (project.keywords.all() if project else []):
        writer.writerow([
            kw.keyword, kw.rank, kw.previous_rank, kw.rank_change,
            kw.search_volume, kw.cpc, kw.difficulty_pct, kw.get_intent_display(), kw.trend
        ])
    return response


# ───────────────────────────────────────────────
# BACKLINKS
# ───────────────────────────────────────────────
@login_required
def backlinks(request):
    project = get_user_project(request)
    bl_list = project.backlinks.all().order_by('-found_at') if project else Backlink.objects.none()
    form = BacklinkForm()
    context = {
        'project': project,
        'all_projects': Project.objects.filter(user=request.user),
        'backlinks': bl_list,
        'form': form,
        'total_backlinks': bl_list.count(),
        'new_backlinks': bl_list.filter(is_new=True).count(),
        'avg_authority': round(bl_list.aggregate(avg=Avg('domain_authority'))['avg'] or 0),
    }
    return render(request, 'dashboard/backlinks.html', context)


@login_required
def add_backlink(request):
    project = get_user_project(request)
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


@login_required
def delete_backlink(request, pk):
    bl = get_object_or_404(Backlink, pk=pk, project__user=request.user)
    if request.method == 'POST':
        bl.delete()
        messages.success(request, 'Backlink deleted.')
    return redirect('backlinks')


@login_required
def export_backlinks_csv(request):
    project = get_user_project(request)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="backlinks.csv"'
    writer = csv.writer(response)
    writer.writerow(['URL', 'Domain', 'Anchor Text', 'Domain Authority', 'Status', 'Found At'])
    for bl in (project.backlinks.all() if project else []):
        writer.writerow([
            bl.url, bl.domain_name, bl.anchor_text, bl.domain_authority,
            'New' if bl.is_new else 'Existing', bl.found_at.strftime('%Y-%m-%d')
        ])
    return response


# ───────────────────────────────────────────────
# COMPETITORS
# ───────────────────────────────────────────────
@login_required
def competitors(request):
    project = get_user_project(request)
    comp_list = project.competitors.all().order_by('-domain_rating') if project else Competitor.objects.none()
    form = CompetitorForm()
    context = {
        'project': project,
        'all_projects': Project.objects.filter(user=request.user),
        'competitors': comp_list,
        'form': form,
    }
    return render(request, 'dashboard/competitors.html', context)


@login_required
def add_competitor(request):
    project = get_user_project(request)
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


@login_required
def delete_competitor(request, pk):
    comp = get_object_or_404(Competitor, pk=pk, project__user=request.user)
    if request.method == 'POST':
        comp.delete()
        messages.success(request, 'Competitor removed.')
    return redirect('competitors')


# ───────────────────────────────────────────────
# SETTINGS
# ───────────────────────────────────────────────
@login_required
def settings_view(request):
    project = get_user_project(request)
    all_projects = Project.objects.filter(user=request.user)
    form = ProjectForm(instance=project) if project else ProjectForm()
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            p = form.save(commit=False)
            p.user = request.user
            p.save()
            messages.success(request, 'Project settings saved.')
            return redirect('settings')
    return render(request, 'dashboard/settings.html', {
        'project': project, 'form': form, 'all_projects': all_projects
    })


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
