from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group')
    
    def clean_text(self):
        data = self.cleaned_data['text']
        if len(data) < 30:
            raise forms.ValidationError('Слишком короткий пост')
        return data
