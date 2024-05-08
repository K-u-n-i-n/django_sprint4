from django import forms
from .models import Profile, Post


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'email']


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('title',
                  'text',
                  'pub_date',
                  'location',
                  'category',
                  'image'
                  )
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
