from django import forms
from .models import Keyword, Backlink, Competitor, Project, AuditIssue


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'domain']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'My Website',
            }),
            'domain': forms.URLInput(attrs={
                'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'https://example.com',
            }),
        }


class KeywordForm(forms.ModelForm):
    class Meta:
        model = Keyword
        fields = ['keyword', 'rank', 'previous_rank', 'search_volume', 'cpc', 'difficulty', 'intent', 'trend']
        widgets = {
            'keyword': forms.TextInput(attrs={
                'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'e.g. seo tools',
            }),
            'rank': forms.NumberInput(attrs={
                'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': '1',
            }),
            'previous_rank': forms.NumberInput(attrs={
                'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': '3',
            }),
            'search_volume': forms.TextInput(attrs={
                'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': '8.4k',
            }),
            'cpc': forms.NumberInput(attrs={
                'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': '12.40',
                'step': '0.01',
            }),
            'difficulty': forms.NumberInput(attrs={
                'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': '0.72',
                'step': '0.01', 'min': '0', 'max': '1',
            }),
            'intent': forms.Select(attrs={
                'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
            }),
            'trend': forms.Select(attrs={
                'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
            }),
        }


class BacklinkForm(forms.ModelForm):
    class Meta:
        model = Backlink
        fields = ['url', 'anchor_text', 'domain_authority', 'is_new']
        widgets = {
            'url': forms.URLInput(attrs={
                'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'https://referring-site.com/page',
            }),
            'anchor_text': forms.TextInput(attrs={
                'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'best seo tools',
            }),
            'domain_authority': forms.NumberInput(attrs={
                'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': '65', 'min': '0', 'max': '100',
            }),
            'is_new': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-indigo-600 focus:ring-indigo-500',
            }),
        }


class CompetitorForm(forms.ModelForm):
    class Meta:
        model = Competitor
        fields = ['name', 'domain', 'domain_rating', 'organic_traffic', 'keywords_count', 'backlinks_count']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'Ahrefs',
            }),
            'domain': forms.URLInput(attrs={
                'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'https://ahrefs.com',
            }),
            'domain_rating': forms.NumberInput(attrs={
                'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': '90', 'min': '0', 'max': '100',
            }),
            'organic_traffic': forms.TextInput(attrs={
                'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': '1.2M',
            }),
            'keywords_count': forms.NumberInput(attrs={
                'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': '2400000',
            }),
            'backlinks_count': forms.TextInput(attrs={
                'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': '14.5M',
            }),
        }


class AuditIssueForm(forms.ModelForm):
    class Meta:
        model = AuditIssue
        fields = ['severity', 'title', 'description', 'category', 'icon']
        widgets = {
            'severity': forms.Select(attrs={'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500'}),
            'title': forms.TextInput(attrs={'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500', 'placeholder': 'Missing meta descriptions'}),
            'description': forms.Textarea(attrs={'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500', 'rows': 3}),
            'category': forms.TextInput(attrs={'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500', 'placeholder': 'On-Page'}),
            'icon': forms.TextInput(attrs={'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500', 'placeholder': 'error'}),
        }
