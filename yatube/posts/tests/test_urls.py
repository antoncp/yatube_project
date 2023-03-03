from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_client, cls.auth_author = Client(), Client()
        cls.random_user = User.objects.create_user(username='random_guy')
        cls.author_user = User.objects.create_user(username='author')
        cls.auth_client.force_login(cls.random_user)
        cls.auth_author.force_login(cls.author_user)
        cls.group = Group.objects.create(
            title='Якобы такая группа',
            slug='test-slug',
            description='Группа с непонятной целью и содержанием',
        )
        cls.post = Post.objects.create(
            author=cls.author_user,
            text='Пост про все хорошее и против всего плохого. Автор жжет.',
        )

    def test_urls_exists(self):
        """Проверка доступности страниц любому пользователю."""
        url_names = {
            '/': 'Главная страница',
            f'/group/{self.group.slug}/': 'Страница группы',
            f'/profile/{self.random_user}/': 'Страница автора',
            f'/posts/{self.post.id}/': 'Детальная страница поста'
        }
        for url, what in url_names.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'Не загружается: {what}')

    def test_404_page(self):
        """Проверка ошибки 404 для несуществующей страницы."""
        response = self.client.get('/abracadabra/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_create_page_exists(self):
        """Проверка доступности страницы создания поста для
        авторизованного пользователя.
        """
        response = self.auth_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_redirect_anonymous(self):
        """Страница /create/ перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/')

    def test_create_comment_anonymous(self):
        """Страница создания комментария перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.client.get(
            f'/posts/{self.post.id}/comment/', follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/comment/')

    def test_comments_redirect_to_detail_post(self):
        """Страница комментариев перенаправляет авторизированного пользователя
        на страницу поста.
        """
        response = self.auth_client.get(
            f'/posts/{self.post.id}/comment/',
            follow=True)
        self.assertRedirects(
            response, f'/posts/{self.post.id}/')

    def test_edit_post_page_exists_for_author(self):
        """Проверка доступности страницы редактирования поста для автора."""
        response = self.auth_author.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_redirect_no_author(self):
        """Страница редактирования поста отправит не автора данного поста на
        детальную страницу поста без опции редактирования.
        """
        response = self.auth_client.get(
            f'/posts/{self.post.id}/edit/',
            follow=True)
        self.assertRedirects(
            response, f'/posts/{self.post.id}/')

    def test_edit_redirect_anonymous(self):
        """Страница редактирования поста перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.client.get(
            f'/posts/{self.post.id}/edit/',
            follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.author_user}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/abracadabra/': 'core/404.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.auth_author.get(address)
                self.assertTemplateUsed(response, template)
