import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from dashboard.models import Project, AuditResult, AuditIssue, Keyword, Backlink, Competitor


def seed():
    # Create a superuser if none exists
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser('admin', 'admin@seoinsightpro.com', 'admin123')
        print(f"Created superuser: admin / admin123")
    else:
        admin = User.objects.get(username='admin')

    # Clear existing data for this user
    Project.objects.filter(user=admin).delete()
    print("Cleared existing projects for admin.")

    project = Project.objects.create(
        user=admin,
        name="SEO Insight Pro",
        domain="https://seoinsightpro.com"
    )

    audit = AuditResult.objects.create(
        project=project,
        health_score=82,
        total_errors=12,
        total_warnings=28,
        total_passed=145,
        passed_core_web_vitals=True,
        lcp_value="1.2s",
        fid_value="18ms",
        cls_value="0.08",
        quick_recommendation="Converting PNGs to WebP could improve your score by up to 14 points."
    )

    AuditIssue.objects.create(audit=audit, severity='critical', title='Broken internal links detected (404)', description='12 pages are currently linking to non-existent URLs, harming crawl budget and UX.', category='Crawlability', icon='block')
    AuditIssue.objects.create(audit=audit, severity='critical', title='Missing Meta Descriptions', description='8 priority landing pages are missing meta descriptions, which may reduce CTR in SERPs.', category='On-Page', icon='description')
    AuditIssue.objects.create(audit=audit, severity='critical', title='SSL Certificate Expiration', description='Your certificate expires in less than 7 days. Automatic renewal failed.', category='Security', icon='dns')
    AuditIssue.objects.create(audit=audit, severity='warning', title='Slow Page Speed on Mobile', description='Core Web Vitals failing on 12 mobile pages. LCP above 4s threshold.', category='Performance', icon='speed')
    AuditIssue.objects.create(audit=audit, severity='warning', title='Images Missing Alt Text', description='43 images across 8 pages are missing descriptive alt attributes.', category='Accessibility', icon='image')
    AuditIssue.objects.create(audit=audit, severity='passed', title='H1 Tags Present', description='All pages have exactly one H1 tag.', category='On-Page', icon='check_circle')
    AuditIssue.objects.create(audit=audit, severity='passed', title='Robots.txt Valid', description='Your robots.txt file is correctly configured.', category='Technical', icon='check_circle')

    keywords_data = [
        ("seo reporting software", 4, 6, "8.4k", 12.40, 0.68, 'commercial', 'up'),
        ("best seo auditor", 1, 1, "1.2k", 8.15, 0.85, 'transactional', 'up'),
        ("enterprise seo dashboard", 12, 9, "3.5k", 15.90, 0.92, 'commercial', 'down'),
        ("backlink analyzer tool", 8, 9, "12.1k", 4.20, 0.72, 'transactional', 'up'),
        ("free keyword ranking tool", 5, 7, "45k", 0.85, 0.24, 'informational', 'up'),
        ("saas seo strategy guide", 22, 18, "12.4k", 4.20, 0.65, 'informational', 'flat'),
        ("enterprise keyword research", 14, 14, "8.9k", 12.50, 0.92, 'commercial', 'up'),
        ("best seo tools 2025", 9, 11, "32.1k", 8.15, 0.88, 'transactional', 'flat'),
    ]
    for kw, rank, prev, vol, cpc, diff, intent, trend in keywords_data:
        Keyword.objects.create(project=project, keyword=kw, rank=rank, previous_rank=prev,
                               search_volume=vol, cpc=cpc, difficulty=diff, intent=intent, trend=trend)

    backlinks_data = [
        ("https://techcrunch.com/2024/05/new-saas-trends", "SEO Software solution", 92, True),
        ("https://forbes.com/business/digital-growth-strategies", "Advanced Analytics Platform", 88, False),
        ("https://github.com/open-source/seo-tools", "Insight Pro API", 96, False),
        ("https://medium.com/@marketingpro/seo-insight-review", "best seo analytics", 64, True),
        ("https://techblog.com/seo-tools-review", "SEO Tools 2025", 65, True),
        ("https://marketingnews.net/best-dashboards", "top seo dashboard", 54, False),
    ]
    for url, anchor, da, is_new in backlinks_data:
        Backlink.objects.create(project=project, url=url, anchor_text=anchor, domain_authority=da, is_new=is_new)

    Competitor.objects.create(project=project, name="Ahrefs", domain="https://ahrefs.com", domain_rating=91, organic_traffic="1.2M", keywords_count=2400000, backlinks_count="14.5M")
    Competitor.objects.create(project=project, name="SEMrush", domain="https://semrush.com", domain_rating=88, organic_traffic="890K", keywords_count=1800000, backlinks_count="9.8M")
    Competitor.objects.create(project=project, name="Moz Pro", domain="https://moz.com", domain_rating=83, organic_traffic="540K", keywords_count=1100000, backlinks_count="6.2M")

    print(f"[OK] Seeded project: {project.name}")
    print(f"[KEY] Login: admin / admin123")
    print(f"[URL] Visit: http://127.0.0.1:8000/")



if __name__ == '__main__':
    seed()
