from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


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
        from urllib.parse import urlparse
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
        from urllib.parse import urlparse
        parsed = urlparse(self.domain)
        return parsed.netloc or self.domain
