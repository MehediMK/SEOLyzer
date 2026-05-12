from datetime import date
from urllib.parse import urlparse
import re

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


def parse_volume(s):
    if not s:
        return 0
    s = str(s).strip().upper()
    m = re.match(r'^([\d.]+)([KM])?$', s)
    if not m:
        try:
            return int(float(s.replace(',', '')))
        except (ValueError, AttributeError):
            return 0
    num = float(m.group(1))
    suffix = m.group(2)
    if suffix == 'K':
        return int(num * 1000)
    if suffix == 'M':
        return int(num * 1000000)
    return int(num)


def _ctr_for_rank(rank):
    if rank is None or rank <= 0:
        return 0.0
    curve = {1: 0.35, 2: 0.20, 3: 0.11, 4: 0.08, 5: 0.055,
             6: 0.04, 7: 0.03, 8: 0.025, 9: 0.02, 10: 0.015}
    return curve.get(rank, 0.01 if rank <= 20 else 0.005)


class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects', null=True, blank=True)
    name = models.CharField(max_length=255)
    domain = models.URLField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('dashboard')


class AuditResult(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='audit')
    health_score = models.IntegerField(default=0)
    total_errors = models.IntegerField(default=0)
    total_warnings = models.IntegerField(default=0)
    total_passed = models.IntegerField(default=0)
    passed_core_web_vitals = models.BooleanField(default=True)
    lcp_value = models.CharField(max_length=20, default='N/A')   # e.g. "1.2s"
    fid_value = models.CharField(max_length=20, default='N/A')   # e.g. "18ms"
    cls_value = models.CharField(max_length=20, default='N/A')   # e.g. "0.08"
    quick_recommendation = models.TextField(blank=True)
    last_crawled = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Audit for {self.project.name}"

    @property
    def score_label(self):
        if self.health_score >= 80:
            return 'Excellent'
        elif self.health_score >= 60:
            return 'Good'
        elif self.health_score >= 40:
            return 'Needs Work'
        return 'Poor'


class AuditIssue(models.Model):
    SEVERITY_CHOICES = [
        ('critical', 'Critical'),
        ('warning', 'Warning'),
        ('passed', 'Passed'),
    ]
    audit = models.ForeignKey(AuditResult, on_delete=models.CASCADE, related_name='issues')
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='warning')
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100, blank=True)
    icon = models.CharField(max_length=50, default='error')

    def __str__(self):
        return f"[{self.severity}] {self.title}"


class Keyword(models.Model):
    INTENT_CHOICES = [
        ('informational', 'Informational'),
        ('commercial', 'Commercial'),
        ('transactional', 'Transactional'),
        ('navigational', 'Navigational'),
    ]
    TREND_CHOICES = [
        ('up', 'Trending Up'),
        ('flat', 'Stable'),
        ('down', 'Trending Down'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='keywords')
    keyword = models.CharField(max_length=255)
    rank = models.IntegerField(null=True, blank=True)
    previous_rank = models.IntegerField(null=True, blank=True)
    search_volume = models.CharField(max_length=50, null=True, blank=True)  # e.g. '8.4k'
    cpc = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    difficulty = models.FloatField(default=0.5, help_text="0.0 (Easy) to 1.0 (Hard)")
    intent = models.CharField(max_length=20, choices=INTENT_CHOICES, default='informational')
    trend = models.CharField(max_length=10, choices=TREND_CHOICES, default='flat')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.keyword

    @property
    def rank_change(self):
        if self.rank is not None and self.previous_rank is not None:
            return self.previous_rank - self.rank
        return 0

    @property
    def difficulty_pct(self):
        return int(self.difficulty * 100)

    @property
    def difficulty_label(self):
        if self.difficulty < 0.33:
            return 'Easy'
        elif self.difficulty < 0.66:
            return 'Medium'
        return 'Hard'

    @property
    def difficulty_color(self):
        if self.difficulty < 0.33:
            return 'green'
        elif self.difficulty < 0.66:
            return 'amber'
        return 'red'


class Backlink(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='backlinks')
    url = models.URLField(max_length=500)
    anchor_text = models.CharField(max_length=255, blank=True)
    domain_authority = models.IntegerField(default=0)
    is_new = models.BooleanField(default=True)
    found_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.url

    @property
    def domain_name(self):
        parsed = urlparse(self.url)
        return parsed.netloc or self.url

    @property
    def authority_pct(self):
        return min(self.domain_authority, 100)

    @property
    def authority_color(self):
        if self.domain_authority >= 70:
            return 'emerald'
        elif self.domain_authority >= 40:
            return 'yellow'
        return 'red'


class Competitor(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='competitors')
    name = models.CharField(max_length=255)
    domain = models.URLField()
    domain_rating = models.IntegerField(default=0)
    organic_traffic = models.CharField(max_length=50, blank=True)   # e.g. '120K'
    keywords_count = models.IntegerField(default=0)
    backlinks_count = models.CharField(max_length=50, blank=True)   # e.g. '45.2K'
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def domain_name(self):
        parsed = urlparse(self.domain)
        return parsed.netloc or self.domain


class DailySnapshot(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='snapshots')
    date = models.DateField(default=date.today)
    traffic_estimate = models.FloatField(default=0.0)
    avg_rank = models.FloatField(default=0.0)
    performance_score = models.IntegerField(default=0)
    backlinks_count = models.IntegerField(default=0)
    new_backlinks = models.IntegerField(default=0)

    class Meta:
        unique_together = ('project', 'date')
        ordering = ['date']

    def __str__(self):
        return f"{self.project.name} / {self.date}"

    @classmethod
    def compute_and_save(cls, project):
        today = date.today()
        keywords = project.keywords.all()
        audit = getattr(project, 'audit', None)

        traffic_est = 0.0
        total_ctr = 0.0
        rank_sum = 0
        rank_count = 0
        for kw in keywords:
            vol = parse_volume(kw.search_volume)
            ctr = _ctr_for_rank(kw.rank)
            traffic_est += vol * ctr
            total_ctr += ctr
            if kw.rank is not None:
                rank_sum += kw.rank
                rank_count += 1

        avg_rank = round(rank_sum / rank_count, 1) if rank_count else 0.0
        perf_score = audit.health_score if audit else 0
        bl_count = project.backlinks.count()
        new_bl = project.backlinks.filter(is_new=True).count()

        snapshot, created = cls.objects.update_or_create(
            project=project,
            date=today,
            defaults={
                'traffic_estimate': round(traffic_est, 0),
                'avg_rank': avg_rank,
                'performance_score': perf_score,
                'backlinks_count': bl_count,
                'new_backlinks': new_bl,
            },
        )
        return snapshot, created
