from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Issue, IssueComment

IC = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent'
TA = IC + ' resize-y'
SE = IC + ' bg-white'


class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = [
            'title_hy', 'title_en', 'description_hy', 'description_en',
            'category', 'area', 'village_name', 'latitude', 'longitude',
            'location_address', 'image',
        ]
        widgets = {
            'title_hy':         forms.TextInput(attrs={'class': IC, 'placeholder': 'Վերնագրե՛ք խնդիրը...'}),
            'title_en':         forms.TextInput(attrs={'class': IC, 'placeholder': 'Issue title in English (optional)'}),
            'description_hy':   forms.Textarea(attrs={'class': TA, 'rows': 4, 'placeholder': 'Նկարագրե՛ք խնդիրը...'}),
            'description_en':   forms.Textarea(attrs={'class': TA, 'rows': 4, 'placeholder': 'Describe the issue in English (optional)...'}),
            'category':         forms.Select(attrs={'class': SE}),
            'area':             forms.Select(attrs={'class': SE}),
            'village_name':     forms.TextInput(attrs={'class': IC, 'placeholder': 'Village name'}),
            'latitude':         forms.HiddenInput(),
            'longitude':        forms.HiddenInput(),
            'location_address': forms.TextInput(attrs={'class': IC, 'placeholder': 'Նշե՛ք հասցեն...'}),
            'image':            forms.FileInput(attrs={'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-navy hover:file:bg-blue-100', 'accept': 'image/*'}),
        }
        labels = {
            'title_hy':         _('Title (Armenian)'),
            'title_en':         _('Title (English)'),
            'description_hy':   _('Description (Armenian)'),
            'description_en':   _('Description (English)'),
            'category':         _('Category'),
            'area':             _('Area'),
            'village_name':     _('Village Name'),
            'location_address': _('Address / Landmark'),
            'image':            _('Photo'),
        }

    def clean_title_hy(self):
        val = self.cleaned_data.get('title_hy', '').strip()
        if len(val) < 5:
            raise forms.ValidationError(_('Title must be at least 5 characters.'))
        return val


class IssueCommentForm(forms.ModelForm):
    class Meta:
        model = IssueComment
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent resize-y',
                'rows': 3,
                'placeholder': 'Write a comment... / Մեկնաբանություն...',
            })
        }
        labels = {'body': _('Comment')}
