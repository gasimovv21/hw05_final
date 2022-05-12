from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = 'text', 'group', 'image'
        labels = {'text': 'Текст поста',
                  'group': 'Группа',
                  'image': 'Картинка'}
        help_texts = {'text': 'Добавьте текст поста!',
                      'group': 'Группа, к которой будет относиться пост',
                      'image': 'Загрузите картинку', }

    def clean_subject(self):
        data = self.cleaned_data['text']
        if data == '':
            raise forms.ValidationError('Поле не может быть пустым!')
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = 'text',
        labels = {'text': 'Текст комментарий'}
        help_texts = {"text": "Добавьте комментарий"}
