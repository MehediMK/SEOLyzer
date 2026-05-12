import csv
import re
import requests
from collections import Counter
from urllib.parse import urljoin, urlparse

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

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


def _analysis_session_snapshot(result):
    return {
        'url': result.get('url', ''),
        'final_url': result.get('final_url', ''),
        'score': result.get('score', 0),
        'score_label': result.get('score_label', ''),
        'issues': result.get('issues', []),
        'pagespeed': result.get('pagespeed') or {},
    }


def _issue_icon(issue_type):
    return {
        'critical': 'error',
        'warning': 'warning',
        'passed': 'check_circle',
    }.get(issue_type, 'error')


def _issue_category(message):
    message = message.lower()
    if 'title' in message or 'meta' in message or 'h1' in message or 'canonical' in message:
        return 'On-Page'
    if 'image' in message or 'alt' in message:
        return 'Accessibility'
    if 'ssl' in message or 'https' in message:
        return 'Security'
    if 'redirect' in message:
        return 'Crawlability'
    return 'Technical'


def _save_analysis_to_project(project, analysis):
    issues = analysis.get('issues', [])
    pagespeed = analysis.get('pagespeed') or {}
    critical_count = sum(1 for issue in issues if issue.get('type') == 'critical')
    warning_count = sum(1 for issue in issues if issue.get('type') == 'warning')
    passed_count = sum(1 for issue in issues if issue.get('type') == 'passed')
    recommendation = next(
        (issue.get('msg', '') for issue in issues if issue.get('type') in ('critical', 'warning')),
        'Keep monitoring this site for new SEO opportunities.',
    )

    audit, _ = AuditResult.objects.update_or_create(
        project=project,
        defaults={
            'health_score': analysis.get('score') or 0,
            'total_errors': critical_count,
            'total_warnings': warning_count,
            'total_passed': passed_count,
            'passed_core_web_vitals': (pagespeed.get('performance', 100) or 0) >= 80,
            'lcp_value': pagespeed.get('lcp', 'N/A'),
            'fid_value': pagespeed.get('fid', 'N/A'),
            'cls_value': pagespeed.get('cls', 'N/A'),
            'quick_recommendation': recommendation,
        },
    )
    audit.issues.all().delete()

    for issue in issues:
        message = issue.get('msg', 'SEO audit check')
        AuditIssue.objects.create(
            audit=audit,
            severity=issue.get('type', 'warning'),
            title=message[:255],
            description=message,
            category=_issue_category(message),
            icon=_issue_icon(issue.get('type')),
        )

    return audit


def _create_project_audit(project, analysis=None):
    if not analysis:
        return AuditResult.objects.create(project=project)

    return _save_analysis_to_project(project, analysis)


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
            analysis = None
            if request.POST.get('source') == 'url_analyzer':
                analysis = request.session.get('last_url_analysis')
                posted_domain = request.POST.get('domain', '')
                analysis_urls = {analysis.get('url'), analysis.get('final_url')} if analysis else set()
                if posted_domain not in analysis_urls:
                    analysis = None
            _create_project_audit(project, analysis)
            request.session['active_project_pk'] = project.pk
            if analysis:
                messages.success(request, f'Project "{project.name}" created with the latest audit analysis.')
                return redirect('seo_audit')
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
    save_project = None
    project_pk = request.POST.get('project') if request.method == 'POST' else request.GET.get('project')
    if project_pk:
        save_project = Project.objects.filter(user=request.user, pk=project_pk).first()
        if save_project:
            url = save_project.domain

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
                analysis = _analysis_session_snapshot(result)
                request.session['last_url_analysis'] = analysis
                if save_project:
                    _save_analysis_to_project(save_project, analysis)
                    request.session['active_project_pk'] = save_project.pk
                    messages.success(request, f'Audit results saved to "{save_project.name}".')
            except Exception as e:
                error = f'Could not analyze URL: {str(e)}'

    return render(request, 'dashboard/analyze_url.html', {
        'url': url,
        'result': result,
        'error': error,
        'projects': Project.objects.filter(user=request.user),
        'save_project': save_project,
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
    else:
        issues.append({'type': 'passed', 'msg': 'No images found requiring alt text'})

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

    else:
        issues.append({'type': 'passed', 'msg': 'No redirect detected'})

    score = _calculate_score(issues)

    return {
        'url': url,
        'final_url': resp.url,
        'project_name': parsed.netloc or url,
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


SEO_STOP_WORDS = {
    'about', 'above', 'after', 'again', 'also', 'and', 'are', 'because', 'been',
    'but', 'can', 'com', 'contact', 'for', 'from', 'get', 'has', 'have', 'here',
    'home', 'how', 'into', 'its', 'learn', 'more', 'not', 'our', 'page', 'read',
    'site', 'that', 'the', 'their', 'this', 'to', 'use', 'was', 'website',
    'what', 'when', 'where', 'which', 'who', 'will', 'with', 'www', 'you',
    'your',
}


def _fetch_soup(url):
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    from bs4 import BeautifulSoup

    headers = {'User-Agent': 'Mozilla/5.0 (compatible; SEOInsightBot/1.0)'}
    resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
    resp.raise_for_status()
    return resp, BeautifulSoup(resp.text, 'html.parser')


def _clean_keyword_text(text):
    text = re.sub(r'[^a-zA-Z0-9\s-]', ' ', text.lower())
    return re.sub(r'\s+', ' ', text).strip()


def _tokenize_keyword_text(text):
    return [
        token for token in re.findall(r'[a-zA-Z][a-zA-Z0-9-]{2,}', text.lower())
        if token not in SEO_STOP_WORDS
    ]


def _discover_keyword_candidates(url, limit=15):
    _, soup = _fetch_soup(url)
    sources = []

    title = soup.find('title')
    if title:
        sources.append(title.get_text(' ', strip=True))

    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        sources.append(meta_desc['content'])

    for tag in soup.find_all(['h1', 'h2', 'h3']):
        sources.append(tag.get_text(' ', strip=True))

    page_text = ' '.join(sources)
    tokens = _tokenize_keyword_text(page_text)
    phrase_counts = Counter()

    for source in sources:
        source_tokens = _tokenize_keyword_text(source)
        for size in (3, 2):
            for index in range(len(source_tokens) - size + 1):
                phrase = ' '.join(source_tokens[index:index + size])
                phrase_counts[phrase] += 1

    candidates = []
    seen = set()

    for source in sources:
        phrase = _clean_keyword_text(source)
        words = [word for word in phrase.split() if word not in SEO_STOP_WORDS]
        if 2 <= len(words) <= 6:
            phrase = ' '.join(words)
            if phrase and phrase not in seen:
                candidates.append(phrase)
                seen.add(phrase)

    for phrase, _ in phrase_counts.most_common(limit * 2):
        if phrase not in seen:
            candidates.append(phrase)
            seen.add(phrase)
        if len(candidates) >= limit:
            break

    if len(candidates) < limit:
        for word, _ in Counter(tokens).most_common(limit * 2):
            if word not in seen:
                candidates.append(word)
                seen.add(word)
            if len(candidates) >= limit:
                break

    return candidates[:limit]


def _discover_external_links(url, limit=50):
    resp, soup = _fetch_soup(url)
    base = urlparse(resp.url)
    links = []
    seen = set()

    for tag in soup.find_all('a', href=True):
        href = tag['href'].strip()
        if not href or href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
            continue

        absolute_url = urljoin(resp.url, href)
        parsed = urlparse(absolute_url)
        if not parsed.scheme.startswith('http') or not parsed.netloc:
            continue
        if parsed.netloc == base.netloc:
            continue
        if absolute_url in seen:
            continue

        seen.add(absolute_url)
        links.append({
            'url': absolute_url,
            'domain': parsed.netloc,
            'anchor_text': tag.get_text(' ', strip=True) or '(no anchor)',
            'rel': ' '.join(tag.get('rel', [])) if tag.get('rel') else '',
        })
        if len(links) >= limit:
            break

    return links


def _checklist_style(status):
    styles = {
        'passed': {
            'badge': 'PASSED',
            'row_class': 'border-green-100 bg-green-50/30 hover:border-green-200',
            'box_class': 'border-green-500 bg-green-50',
            'icon': 'check',
            'icon_class': 'text-green-600',
            'badge_class': 'text-green-600 bg-green-50',
            'action_label': 'View Check',
        },
        'required': {
            'badge': 'FIX',
            'row_class': 'border-error/20 bg-red-50/20',
            'box_class': 'border-error',
            'icon': 'priority_high',
            'icon_class': 'text-error',
            'badge_class': 'text-error bg-red-50',
            'action_label': 'Review Issue',
        },
        'review': {
            'badge': 'REVIEW',
            'row_class': 'border-amber-200 bg-amber-50/30 hover:border-amber-300',
            'box_class': 'border-amber-500 bg-amber-50',
            'icon': 'warning',
            'icon_class': 'text-amber-600',
            'badge_class': 'text-amber-700 bg-amber-50',
            'action_label': 'Review Issue',
        },
        'pending': {
            'badge': 'NOT CHECKED',
            'row_class': 'border-gray-100 hover:border-primary/20',
            'box_class': 'border-gray-300',
            'icon': 'radio_button_unchecked',
            'icon_class': 'text-gray-400',
            'badge_class': 'text-gray-500 bg-gray-50',
            'action_label': 'Run Audit',
        },
    }
    return styles[status]


def _issue_status(issue):
    if not issue:
        return 'pending'
    if issue.severity == 'passed':
        return 'passed'
    if issue.severity == 'critical':
        return 'required'
    return 'review'


def _find_check_issue(issues, terms, match_all=True):
    for issue in issues:
        haystack = f'{issue.title} {issue.description} {issue.category}'.lower()
        if match_all and all(term in haystack for term in terms):
            return issue
        if not match_all and any(term in haystack for term in terms):
            return issue
    return None


def _build_audit_checklist(audit):
    checks = [
        {
            'label': 'Title tag is present and sized correctly',
            'description': 'Confirms the page has a title tag and keeps it within the recommended search snippet range.',
            'terms': ('title',),
            'match_all': True,
        },
        {
            'label': 'Meta description is present',
            'description': 'Checks whether the page has a meta description that can support search result click-through rate.',
            'terms': ('meta description',),
            'match_all': True,
        },
        {
            'label': 'H1 structure is valid',
            'description': 'Verifies that the page has exactly one primary H1 heading.',
            'terms': ('h1',),
            'match_all': True,
        },
        {
            'label': 'Image alt text is covered',
            'description': 'Reviews images for missing alt attributes that affect accessibility and image SEO.',
            'terms': ('image', 'alt'),
            'match_all': True,
        },
        {
            'label': 'Canonical URL is configured',
            'description': 'Checks for a canonical tag to help search engines choose the preferred page URL.',
            'terms': ('canonical',),
            'match_all': True,
        },
        {
            'label': 'HTTPS / SSL is active',
            'description': 'Confirms the audited URL is using HTTPS.',
            'terms': ('https', 'ssl'),
            'match_all': False,
        },
        {
            'label': 'Redirect behavior is clean',
            'description': 'Flags unexpected redirects that may slow crawling or create canonical confusion.',
            'terms': ('redirect',),
            'match_all': True,
        },
    ]
    issues = list(audit.issues.all()) if audit else []
    checklist = []

    for check in checks:
        match = _find_check_issue(issues, check['terms'], check['match_all'])
        status = _issue_status(match)
        item = {
            'label': check['label'],
            'description': check['description'],
            'status': status,
            'message': match.description if match else 'Run an audit to evaluate this check.',
            'issue_id': match.pk if match else None,
            'tab_name': match.severity if match else '',
        }
        item.update(_checklist_style(status))
        checklist.append(item)

    return checklist


def _build_checklist_summary(checklist):
    return {
        'total': len(checklist),
        'passed': sum(1 for item in checklist if item['status'] == 'passed'),
        'needs_attention': sum(1 for item in checklist if item['status'] in ('required', 'review')),
        'not_checked': sum(1 for item in checklist if item['status'] == 'pending'),
    }


def _build_action_plan(critical_issues, warning_issues):
    issue_items = list(critical_issues[:3])
    if len(issue_items) < 3:
        issue_items.extend(list(warning_issues[:3 - len(issue_items)]))

    plan = [
        {
            'number': f'{index:02}',
            'title': issue.title,
            'description': issue.description,
            'link_label': 'Review issue',
            'link_icon': 'chevron_right',
            'link_url': '#tab-critical' if issue.severity == 'critical' else '#tab-warning',
            'tab_name': issue.severity,
            'issue_id': issue.pk,
        }
        for index, issue in enumerate(issue_items, start=1)
    ]

    fallback_items = [
        {
            'title': 'Compress Large Assets',
            'description': 'Use Brotli compression and serve images in next-gen formats like AVIF or WebP to reduce page weight.',
            'link_label': 'Instruction Guide',
            'link_icon': 'open_in_new',
            'link_url': '#',
        },
        {
            'title': 'Fix Schema Markups',
            'description': 'Review structured data blocks and update invalid JSON-LD to match current Schema.org requirements.',
            'link_label': 'View Errors',
            'link_icon': 'open_in_new',
            'link_url': '#',
        },
        {
            'title': 'Consolidate Redirect Chains',
            'description': 'Update source links so they point directly to the final destination URL and avoid multi-hop redirects.',
            'link_label': 'Download List',
            'link_icon': 'download',
            'link_url': '#',
        },
    ]

    for fallback in fallback_items:
        if len(plan) >= 3:
            break
        fallback['number'] = f'{len(plan) + 1:02}'
        plan.append(fallback)

    return plan


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
    critical_issues = AuditIssue.objects.none()
    warning_issues = AuditIssue.objects.none()
    passed_issues = AuditIssue.objects.none()
    audit = None
    context = {'project': project, 'all_projects': Project.objects.filter(user=request.user)}
    if project:
        audit = getattr(project, 'audit', None)
        context['audit'] = audit
        if audit:
            critical_issues = audit.issues.filter(severity='critical')
            warning_issues = audit.issues.filter(severity='warning')
            passed_issues = audit.issues.filter(severity='passed')
    checklist_items = _build_audit_checklist(audit)
    context.update({
        'critical_issues': critical_issues,
        'warning_issues': warning_issues,
        'passed_issues': passed_issues,
        'checklist_items': checklist_items,
        'checklist_summary': _build_checklist_summary(checklist_items),
        'action_plan_items': _build_action_plan(critical_issues, warning_issues),
    })
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
    avg_difficulty = kw_list.aggregate(avg=Avg('difficulty'))['avg'] or 0
    context = {
        'project': project,
        'all_projects': Project.objects.filter(user=request.user),
        'keywords': kw_list,
        'form': form,
        'total_keywords': kw_list.count(),
        'top_3_keywords': kw_list.filter(rank__lte=3).count(),
        'avg_difficulty': round(avg_difficulty * 100),
    }
    return render(request, 'dashboard/keywords.html', context)


@login_required
@require_POST
def discover_keywords(request):
    project = get_user_project(request)
    if not project:
        messages.error(request, "No project found. Create one first.")
        return redirect('create_project')

    try:
        candidates = _discover_keyword_candidates(project.domain)
    except Exception as e:
        messages.error(request, f'Could not discover keywords from {project.domain}: {e}')
        return redirect('keywords')

    created = 0
    skipped = 0
    for keyword in candidates:
        if project.keywords.filter(keyword__iexact=keyword).exists():
            skipped += 1
            continue
        Keyword.objects.create(
            project=project,
            keyword=keyword,
            difficulty=0.5,
            intent='informational',
            trend='flat',
        )
        created += 1

    if created:
        messages.success(
            request,
            f'Imported {created} on-page keyword candidate(s) from {project.domain}. '
            'Rank, volume and CPC need Search Console or keyword API data.',
        )
    else:
        messages.warning(request, f'No new keyword candidates found. {skipped} candidate(s) were already tracked.')
    return redirect('keywords')


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
    discovered_external_links = request.session.get('discovered_external_links', [])
    context = {
        'project': project,
        'all_projects': Project.objects.filter(user=request.user),
        'backlinks': bl_list,
        'discovered_external_links': discovered_external_links,
        'form': form,
        'total_backlinks': bl_list.count(),
        'new_backlinks': bl_list.filter(is_new=True).count(),
        'avg_authority': round(bl_list.aggregate(avg=Avg('domain_authority'))['avg'] or 0),
    }
    return render(request, 'dashboard/backlinks.html', context)


@login_required
@require_POST
def discover_external_links(request):
    project = get_user_project(request)
    if not project:
        messages.error(request, "No project found.")
        return redirect('backlinks')

    try:
        links = _discover_external_links(project.domain)
    except Exception as e:
        messages.error(request, f'Could not scan external links from {project.domain}: {e}')
        return redirect('backlinks')

    request.session['discovered_external_links'] = links
    if links:
        messages.success(
            request,
            f'Found {len(links)} outbound external link(s) on {project.domain}. '
            'True backlinks require Google Search Console or a backlink provider.',
        )
    else:
        messages.warning(request, 'No outbound external links found on the active project page.')
    return redirect('backlinks')


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
