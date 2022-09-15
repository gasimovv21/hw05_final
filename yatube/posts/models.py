from django.contrib.auth import get_user_model
from django.db import models

from core.models import CreatedModel

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200,
                             verbose_name='Имя группы',
                             help_text='Укажите название группы')
    slug = models.SlugField(unique=True,
                            verbose_name='Номер группы',
                            help_text='Укажите номер группы')
    description = models.TextField(verbose_name='Описание',
                                   help_text='Укажите описание вашей группы')

    def __str__(self):
        return f'{self.title}'


class Post(CreatedModel):
    text = models.TextField(verbose_name='Текст поста',
                            help_text='Добавьте текст поста!')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts')
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Название группы',
        help_text='Определите к какой группе отонсится пост')
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True)

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Публикация'
        verbose_name_plural = 'Публикаций'

    def __str__(self):
        return f'{self.text[:30]}'


class Comment(CreatedModel):
    text = models.TextField(verbose_name='Добавьте комментарий',
                            help_text='Добавьте текст поста!')
    post = models.ForeignKey(
        Post,
        related_name='comments',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        related_name='comments',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f'{self.text[:30]}'


class Follow(CreatedModel):
    user = models.ForeignKey(
        User,
        related_name="follower",
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE,
    )

    class Meta:
        models.UniqueConstraint(fields=['user', 'author'],
                                name='unique_booking')


class UserIp(CreatedModel):
    Ip = models.CharField(max_length=50)