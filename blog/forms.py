from django import forms
from .models import Comment

class EmailPostForm(forms.Form):
    name = forms.CharField(max_length=255)
    email = forms.EmailField()
    to = forms.EmailField()
    comments = forms.CharField(required=False, widget=forms.Textarea)

# have to use modelfrom this time because you have to build a form dynamically from Comment model
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('name', 'email', 'body') 

# use the query field to let users introduce search terms
class SearchForm(forms.Form):
    query = forms.CharField()