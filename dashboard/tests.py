from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from .models import AuditIssue, AuditResult, Keyword, Project
from .views import _build_audit_checklist, _build_checklist_summary, _save_analysis_to_project


class AuditChecklistTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='owner', password='pass')
        self.project = Project.objects.create(
            user=self.user,
            name='Example',
            domain='https://example.com',
        )
        self.audit = AuditResult.objects.create(project=self.project, health_score=80)

    def test_checklist_uses_saved_audit_issues(self):
        AuditIssue.objects.create(
            audit=self.audit,
            severity='passed',
            title='Title length is good: 45 chars',
            description='Title length is good: 45 chars',
            category='On-Page',
            icon='check_circle',
        )
        AuditIssue.objects.create(
            audit=self.audit,
            severity='critical',
            title='Missing meta description',
            description='Missing meta description',
            category='On-Page',
            icon='error',
        )

        checklist = _build_audit_checklist(self.audit)
        summary = _build_checklist_summary(checklist)

        self.assertEqual(len(checklist), 7)
        self.assertEqual(summary['passed'], 1)
        self.assertEqual(summary['needs_attention'], 1)
        self.assertEqual(checklist[0]['status'], 'passed')
        self.assertEqual(checklist[1]['status'], 'required')

    def test_save_analysis_to_project_replaces_audit_data(self):
        AuditIssue.objects.create(
            audit=self.audit,
            severity='warning',
            title='Old issue',
            description='Old issue',
            category='Technical',
            icon='warning',
        )

        _save_analysis_to_project(self.project, {
            'score': 72,
            'pagespeed': {'performance': 91, 'lcp': '1.2s', 'fid': '20ms', 'cls': '0.02'},
            'issues': [
                {'type': 'critical', 'msg': 'Missing meta description'},
                {'type': 'warning', 'msg': 'No canonical URL tag found'},
                {'type': 'passed', 'msg': 'Exactly one H1 tag found'},
            ],
        })

        self.audit.refresh_from_db()
        self.assertEqual(self.audit.health_score, 72)
        self.assertEqual(self.audit.total_errors, 1)
        self.assertEqual(self.audit.total_warnings, 1)
        self.assertEqual(self.audit.total_passed, 1)
        self.assertEqual(self.audit.issues.count(), 3)
        self.assertFalse(self.audit.issues.filter(title='Old issue').exists())

    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_audit_page_renders_functional_checklist(self):
        AuditIssue.objects.create(
            audit=self.audit,
            severity='passed',
            title='HTTPS / SSL is active',
            description='HTTPS / SSL is active',
            category='Security',
            icon='check_circle',
        )

        self.client.force_login(self.user)
        response = self.client.get('/audit/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'On-Page SEO Checklist')
        self.assertContains(response, 'HTTPS / SSL is active')
        self.assertContains(response, 'focusIssue')


class WebsiteDiscoveryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='owner', password='pass')
        self.project = Project.objects.create(
            user=self.user,
            name='Example',
            domain='https://example.com',
        )
        self.client.force_login(self.user)

    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_discover_keywords_imports_on_page_candidates(self):
        Keyword.objects.create(project=self.project, keyword='existing keyword')

        with patch('dashboard.views._discover_keyword_candidates', return_value=[
            'existing keyword',
            'technical seo audit',
            'website crawler',
        ]):
            response = self.client.post('/keywords/discover/')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/keywords/')
        self.assertTrue(Keyword.objects.filter(project=self.project, keyword='technical seo audit').exists())
        self.assertTrue(Keyword.objects.filter(project=self.project, keyword='website crawler').exists())
        self.assertEqual(Keyword.objects.filter(project=self.project, keyword__iexact='existing keyword').count(), 1)

    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_discover_external_links_stores_scan_results_in_session(self):
        links = [{
            'url': 'https://docs.example.com/guide',
            'domain': 'docs.example.com',
            'anchor_text': 'Guide',
            'rel': 'nofollow',
        }]

        with patch('dashboard.views._discover_external_links', return_value=links):
            response = self.client.post('/backlinks/discover-external-links/')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/backlinks/')
        self.assertEqual(self.client.session['discovered_external_links'], links)

        response = self.client.get('/backlinks/')
        self.assertContains(response, 'External Links Found on Website')
        self.assertContains(response, 'docs.example.com')
