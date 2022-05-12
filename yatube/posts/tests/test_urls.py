from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group, Comment
User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NotAuthor')
        cls.author = User.objects.create_user(username='NoName')
        cls.follower = User.objects.create_user(username='Follower')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )

    def setUp(self) -> None:
        self.not_author_authorized_client = Client()
        self.author_authorized_client = Client()
        self.not_author_authorized_client.force_login(self.user)
        self.author_authorized_client.force_login(self.author)
        self.authorized_client_follower = Client()
        self.authorized_client_follower.force_login(self.follower)
        self.testing_urls = (
            ('posts:index', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.user,)),
            ('posts:post_detail', (self.post.id,)),
            ('posts:post_create', None),
            ('posts:post_edit', (self.post.id,)),
            ('posts:post_delete', (self.post.id,)),
            ('posts:follow_index', None),
            ('posts:profile_follow', (self.user,)),
            ('posts:profile_unfollow', (self.user,)),
        )
        self.comment_count = Comment.objects.count()
        self.post_count = Post.objects.count()
        self.url_post_profile_follow = reverse(
            'posts:profile_follow', args=(self.user.username,))
        self.url_post_profile_unfollow = reverse(
            'posts:profile_unfollow', args=(self.user.username,))
        self.url_post_follow_index = reverse(
            'posts:follow_index')
        self.url_index = reverse('posts:index')
        self.url_profile = reverse('posts:profile', args=(self.user,))

    def test_urls_uses_correct_template(self):
        """URL-адреса используют соотвествующие шаблоны"""
        template_url_names = (
            ('posts:index', None, 'posts/index.html'),
            ('posts:group_list', (self.group.slug,), 'posts/group_list.html'),
            ('posts:profile', (self.user,), 'posts/profile.html'),
            ('posts:post_detail', (self.post.id,), 'posts/post_detail.html'),
            ('posts:post_create', None, 'posts/create_post.html'),
            ('posts:post_edit', (self.post.id,), 'posts/create_post.html'),
        )
        for name, argument, template in template_url_names:
            with self.subTest(name=name):
                response = self.author_authorized_client.get(
                    reverse(name, args=argument))
                self.assertTemplateUsed(response, template)

    def test_404_page(self):
        """Запрос к несуществующей странице вернёт ошибку 404"""
        response = self.client.get('/n0t_ex15ting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_matching_hardcode_and_reversename(self):
        """Проверки на соответствия, хардкод ссылки равны reverse(name)"""
        name_arg_hardcodes = (
            ('posts:index', None, '/'),
            ('posts:group_list', (self.group.slug,), '/group/test_slug/'),
            ('posts:profile', (self.user,), f'/profile/{self.user}/'),
            ('posts:post_detail', (self.post.id,), f'/posts/{self.post.id}/'),
            ('posts:post_create', None, '/create/'),
            ('posts:post_edit', (self.post.id,),
                f'/posts/{self.post.id}/edit/'),
        )
        for name, argument, hardcode in name_arg_hardcodes:
            with self.subTest():
                self.assertEqual(hardcode, reverse(name, args=argument))

    def test_all_urls_available_for_author(self):
        """Все URLS доступны автору"""
        for name, argument in self.testing_urls:
            with self.subTest(name=name):
                if name in ['posts:profile_follow', 'posts:profile_unfollow']:
                    response_argument = reverse(name, args=argument)
                    response_variable_profile = reverse(
                        'posts:profile', args=argument
                    )
                    response = self.author_authorized_client.get(
                        response_argument, follow=True
                    )
                    self.assertRedirects(response, response_variable_profile)
                else:
                    response = self.author_authorized_client.get(
                        reverse(name, args=argument)
                    )
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_all_urls_except_edit_available_for_noauthor(self):
        """Все URLS, кроме edit доступны не автору"""
        for name, argument in self.testing_urls:
            with self.subTest(name=name):
                if name in ['posts:post_edit',
                            'posts:post_delete']:
                    response_variable_post_edit = reverse(
                        'posts:post_edit', args=argument
                    )
                    response_variable_post_detail = reverse(
                        'posts:post_detail', args=argument
                    )
                    response = self.not_author_authorized_client.get(
                        response_variable_post_edit, follow=True)
                    self.assertRedirects(
                        response,
                        response_variable_post_detail)
                else:
                    response = self.not_author_authorized_client.get(
                        reverse(name, args=argument))
                    if name in ['posts:profile_follow',
                                'posts:profile_unfollow']:
                        self.assertRedirects(response, self.url_profile)
                    else:
                        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_all_urls_except_edit_and_create_available_for_guest(self):
        """Все URLS, кроме edit и create доступны анониму"""
        for name, argument in self.testing_urls:
            with self.subTest(name=name):
                if name in ['posts:post_edit',
                            'posts:follow_index',
                            'posts:post_create',
                            'posts:profile_follow',
                            'posts:profile_unfollow',
                            'posts:post_delete']:
                    response_argument = reverse(name, args=argument)
                    response_auth_login = reverse('users:login')
                    response = self.client.get(
                        response_argument, follow=True)
                    self.assertRedirects(
                        response,
                        f'{response_auth_login}?next={response_argument}')
                else:
                    response = self.client.get(
                        reverse(name, args=argument))
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_exists(self):
        """Проверка, что не залогиненный пользователь не может создавать
        посты."""
        response = self.client.get(reverse('posts:post_create'))
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), self.post_count)

    def test_add_comment_to_posts(self):
        """Проверка после успешной отправки комментарий появляется на странице
        поста."""
        new_comment = {
            'text': 'test-comment',
        }
        self.author_authorized_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=new_comment,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), self.comment_count + 1)

    def test_authorized_exists(self):
        """Проверка, Комментировать посты может только авторизованный
        пользователь"""
        response_arugment_comment = reverse(
            'posts:add_comment', args=(self.post.id,))
        response_argument_login = reverse('users:login')
        response = self.client.get(response_arugment_comment)
        self.assertRedirects(
            response,
            f'{response_argument_login}?next={response_arugment_comment}')
        self.assertEqual(Comment.objects.count(), self.comment_count)

    def test_delete_posts(self):
        """Проверка что пост может удалить только автор поста"""
        response_arugment_post_delete = reverse(
            'posts:post_delete', args=(self.post.id,))
        response_argument_post_detail = reverse(
            'posts:post_detail', args=(self.post.id,))
        response = self.not_author_authorized_client.get(
            response_arugment_post_delete)
        self.assertRedirects(
            response, response_argument_post_detail)
        self.assertEqual(Post.objects.count(), self.post_count)

    def test_new_post_appears_in_follow_index(self):
        """Проверяем, что новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан."""
        self.authorized_client_follower.get(self.url_post_profile_follow)
        response = self.author_authorized_client.get(
            self.url_post_follow_index
        )
        self.assertContains(response, self.post.pk)
        response = self.not_author_authorized_client.get(
            self.url_post_follow_index)
        post_object = response.context['page_obj']
        self.assertEqual(len(post_object), 0)

    def test_user_can_follow_and_unfollow(self):
        """Проверка, что авторизованный пользователь может подписаться
        и отписаться"""
        url_list = {
            self.url_post_profile_follow,
            self.url_post_profile_unfollow,
        }
        for url in url_list:
            response = self.not_author_authorized_client.get(url)
            expected_url = reverse('posts:profile', args=(self.user.username,))
            self.assertRedirects(response, expected_url)
