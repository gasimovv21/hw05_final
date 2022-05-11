import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        self.author = User.objects.create_user(username='NoName')
        self.post = Post.objects.create(
            author=self.author,
            text='Тестовый текст',
            group=self.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author_authorized_client = Client()
        self.author_authorized_client.force_login(self.author)
        self.post_count = Post.objects.count()

    def test_create_new_post(self):
        """Валидная форма создает запись в Post."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': self.post.text,
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.author_authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(
            Post.objects.filter(
                text=self.post.text,
                group=self.group.id,
                image='posts/small.gif'
            ).exists()
        )
        self.assertRedirects(response, reverse(
            'posts:profile', args=(self.author,)))
        self.assertEqual(Post.objects.count(), self.post_count + 1)
        self.assertEqual(form_data['text'], self.post.text)
        self.assertEqual(form_data['group'], self.group.id)
        self.assertEqual(form_data['image'], uploaded)

    def test_author_can_edit_post(self):
        """Тест что автор может редактировать
        пост и проверка на то что пост изменён"""
        self.second_group = Group.objects.create(
            title='Тестовая группа2',
            slug='test_slug2',
            description='Тестовое описание2'
        )
        form_data = {
            'text': 'Новый тестовый текст',
            'group': self.second_group.id,
        }
        response_argument = reverse('posts:post_detail', args=(self.post.id,))
        response = self.author_authorized_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data,
        )
        self.assertRedirects(response, response_argument)
        first_object = Post.objects.first()
        self.assertEqual(first_object.group, self.second_group)
        self.assertEqual(first_object.text, 'Новый тестовый текст')
        self.assertEqual(first_object.author, self.author)
        self.assertEqual(Post.objects.count(), self.post_count)
        response = self.author_authorized_client.get(
            reverse('posts:group_list', args=(self.group.slug,)))
        page_object = response.context['page_obj']
        self.assertEqual(len(page_object), 0)
