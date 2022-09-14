from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse


class TaskURLTests(TestCase):
    def test_author_tech_url_exists(self):
        urls_list = (
            ('about:author', 'about/author.html'),
            ('about:tech', 'about/tech.html'),
        )
        for name, url in urls_list:
            self.subTest(name=name)
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(response, url)

    def test_urls_uses_correct_template(self):
        """URL-адреса используют соотвествующие шаблоны"""
        reverse_list = (
            ('about:author', '/about/author/'),
            ('about:tech', '/about/tech/'),
        )
        for name, url in reverse_list:
            with self.subTest():
                self.assertEqual(url, reverse(name))
