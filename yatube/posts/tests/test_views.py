import time
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse
from django import forms

from posts.forms import PostForm
from posts.models import Post, Group, Follow, Comment
from core.views import page_not_found

User = get_user_model()


class StaticURLTests(TestCase):
    PAGINATOR_TEST_COUNT = 13

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.notfollower = User.objects.create_user(username='hatefollow')
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
        self.not_follower = Client()
        self.not_follower.force_login(self.notfollower)
        self.url_index = reverse('posts:index')
        self.follow_count = Follow.objects.count()
        self.comment_count = Comment.objects.count()
        self.url_follow_index = reverse('posts:follow_index')
        self.url_add_comment = reverse(
            'posts:add_comment', args=(self.post.id,))

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
        self.assertContains(response, '<img')

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

    def test_cache_for_index_page(self):
        """Тест кеша главной страницы!"""
        response = self.client.get(self.url_index)
        post_count = Post.objects.count()
        Post.objects.get(id=self.post.id).delete()
        response2 = self.client.get(self.url_index)
        self.assertEqual(response.content, response2.content)
        post_count2 = Post.objects.count()
        cache.clear()
        self.assertEqual(post_count - 1, post_count2)
        response3 = self.client.get(self.url_index)
        self.assertNotEqual(response3.content, response.content)

    def test_profile_follow(self):
        """Тест на подписку"""
        Follow.objects.get_or_create(user=self.user, author=self.post.author)
        follow_count2 = Follow.objects.count()
        self.assertEqual(follow_count2, self.follow_count + 1)

    def test_profile_unfollow(self):
        """Тест на проверку отписки"""
        Follow.objects.get_or_create(user=self.user, author=self.post.author)
        follow_count_before_delete = Follow.objects.count()
        Follow.objects.filter(
            user=self.user,
            author__username=self.user.username).delete()
        self.assertEqual(self.follow_count, follow_count_before_delete - 1)

    def test_no_follower(self):
        """Проверка, что у не фаловера в фоллоу индексе пагинатор пустой"""
        Follow.objects.get_or_create(user=self.user, author=self.post.author)
        response = self.not_follower.get(self.url_follow_index)
        page_object = response.context['page_obj']
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(page_object), 0)

    def test_anonim_cannot_follow(self):
        """Проверка что аноним не может подписоваться!"""
        response = self.client.get(self.url_follow_index)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(self.follow_count, 0)

    def test_comments(self):
        """Тест комментарий"""
        Comment.objects.create(
            text=self.post.text,
            author=self.user,
            post=self.post)
        comment_count2 = Comment.objects.count()
        self.assertEqual(comment_count2, self.comment_count + 1)

    def test_anonim_cannot_leave_comment(self):
        """Проверка что аноним не может комментировать!"""
        response = self.client.get(self.url_add_comment)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(self.comment_count, 0)
