from django.contrib import admin
from .models import Project, AuditResult, AuditIssue, Keyword, Backlink, Competitor


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'domain', 'created_at')
    search_fields = ('name', 'domain')


@admin.register(AuditResult)
class AuditResultAdmin(admin.ModelAdmin):
    list_display = ('project', 'health_score', 'total_errors', 'total_warnings', 'passed_core_web_vitals', 'last_crawled')


@admin.register(AuditIssue)
class AuditIssueAdmin(admin.ModelAdmin):
    list_display = ('title', 'severity', 'category', 'audit')
    list_filter = ('severity',)
    search_fields = ('title',)


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'project', 'rank', 'search_volume', 'cpc', 'difficulty', 'intent', 'trend')
    list_filter = ('intent', 'trend', 'project')
    search_fields = ('keyword',)


@admin.register(Backlink)
class BacklinkAdmin(admin.ModelAdmin):
    list_display = ('domain_name', 'anchor_text', 'domain_authority', 'is_new', 'found_at')
    list_filter = ('is_new',)

    def domain_name(self, obj):
        return obj.domain_name


@admin.register(Competitor)
class CompetitorAdmin(admin.ModelAdmin):
    list_display = ('name', 'domain', 'domain_rating', 'organic_traffic', 'keywords_count')
    search_fields = ('name', 'domain')
