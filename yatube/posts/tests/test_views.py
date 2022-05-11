import time
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse
from django import forms

from posts.forms import PostForm
from posts.models import Post, Group
from core.views import page_not_found

User = get_user_model()


class StaticURLTests(TestCase):
    PAGINATOR_TEST_COUNT = 13

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        for post_count in range(StaticURLTests.PAGINATOR_TEST_COUNT):
            time.sleep(0.001)
            cls.post = Post.objects.create(
                author=cls.user,
                text=f"Текст поста номер - {post_count}",
                group=cls.group,
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        template_url_names = (
            ('posts:index', None, 'posts/index.html'),
            ('posts:follow_index', None, 'posts/follow.html'),
            ('posts:group_list', (self.group.slug,), 'posts/group_list.html'),
            ('posts:profile', (self.user,), 'posts/profile.html'),
            ('posts:post_detail', (self.post.id,), 'posts/post_detail.html'),
            ('posts:post_create', None, 'posts/create_post.html'),
            ('posts:post_edit', (self.post.id,), 'posts/create_post.html'),
            ('posts:post_delete', (self.post.id,), 'posts/post_delete.html'),
        )
        for name, argument, template in template_url_names:
            with self.subTest(name=name):
                response = self.authorized_client.get(
                    reverse(name, args=argument)
                )
                self.assertTemplateUsed(response, template)

    def test_page404_uses_correct_template(self):
        """Проверка что код 404 отдаёт соответствующий шаблон."""
        response = self.client.get(page_not_found)
        self.assertTemplateUsed(response, 'core/404.html')

    def check_common_variables(self, response, bool_variable=False):
        """Проверка Автора, Текст, Группу, Дату, Картинки"""
        if bool_variable is True:
            response_object = response.context.get('post')
        else:
            response_object = response.context.get('page_obj')[0]
        self.assertEqual(response_object.author, self.user)
        self.assertEqual(response_object.text, self.post.text)
        self.assertEqual(response_object.group, self.post.group)
        self.assertEqual(response_object.pub_date, self.post.pub_date)
        self.assertEqual(response_object.image, self.post.image)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.check_common_variables(response)

    def test_group_list_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:group_list', args=(self.group.slug,)))
        self.assertEqual(response.context['group'], self.group)
        self.check_common_variables(response)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.client.get(
            reverse('posts:profile', args=(self.user.username,)))
        self.assertEqual(response.context['author'], self.user)
        self.check_common_variables(response)

    def test_post_detail_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        response = self.client.get(
            reverse('posts:post_detail',
                    args=(self.post.id,)
                    ))
        self.check_common_variables(response, True)

    def test_post_edit_and_create_post_have_correct_context(self):
        """Шаблон post_edit и create_post для создание
        сформирован с правильным контекстом"""
        self.post_create_url = ('posts:post_create', None, PostForm)
        self.post_edit_url = ('posts:post_edit', (self.post.id,), PostForm)

        url_list = (
            self.post_create_url,
            self.post_edit_url,
        )
        create_form = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for name, argument, post_form in url_list:
            with self.subTest(name=name):
                response = self.authorized_client.post(
                    reverse(name, args=argument)
                )
                for value, expected in create_form.items():
                    with self.subTest(value=value):
                        form_filed = response.context.get('form').fields.get(
                            value)
                        self.assertIsInstance(form_filed, expected)
                        self.assertIsInstance(
                            response.context['form'], post_form)
                        self.assertIn('form', response.context)

    def testing_paginator(self):
        templates_list_paginator = (
            ('posts:index', None),
            ('posts:group_list', (self.post.group.slug,)),
            ('posts:profile', (self.user,)),
        )
        for name, argument in templates_list_paginator:
            with self.subTest(name=name):
                response1 = self.client.get(reverse(name, args=argument))
                response2 = self.client.get(
                    reverse(name, args=argument) + '?page=2')
                self.assertEqual(
                    len(response1.context['page_obj']), settings.MAX_POSTS)
                remain_pages = self.PAGINATOR_TEST_COUNT - settings.MAX_POSTS
                self.assertEqual(len(
                    response2.context['page_obj']), remain_pages)

    def test_group_for_correct_post(self):
        """Проверка, чтобы пост был не в первой группе"""
        self.second_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug1',
            description='Тестовое описание 2 гурппы'
        )
        form_data = {
            'text': self.post.text,
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                text=self.post.text,
                group=self.group.id
            ).exists()
        )
        response = self.authorized_client.get(
            reverse('posts:group_list', args=(self.second_group.slug,)))
        page_object = response.context['page_obj']
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(page_object), 0)
