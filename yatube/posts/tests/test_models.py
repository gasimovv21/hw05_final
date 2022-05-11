from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='str имя группы не совпадает',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост длинной более 30 символов',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = self.post
        group = self.group
        expected_post = post.text
        expected_group = group.title
        field_list = [
            (
                expected_post, str(post), self.post.text[:30]
            ),
            (
                expected_group, str(group), self.group.title
            )
        ]
        for field in field_list:
            with self.subTest(field=field):
                self.assertEqual(field, field)

    def test_models_have_correct_verbose_name(self):
        """Проверка на содержание verbose_name у полей"""
        post = self.post
        field_verboses = (
            ('text', 'Текст поста'),
            ('group', 'Название группы'),
        )
        for field, expected_value in field_verboses:
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_models_have_correct_help_text(self):
        post = self.post
        field_help_texts = {
            ('text', 'Добавьте текст поста!'),
            ('group', 'Определите к какой группе отонсится пост'),
        }
        for field, expected_value in field_help_texts:
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)
