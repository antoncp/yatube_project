import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_client, cls.auth_author, cls.auth_emptyreader = (
            Client(), Client(), Client())
        cls.random_user = User.objects.create_user(username='random_guy')
        cls.author_user = User.objects.create_user(username='author')
        cls.empty_user = User.objects.create_user(username='no_matter')
        cls.auth_client.force_login(cls.random_user)
        cls.auth_author.force_login(cls.author_user)
        cls.auth_emptyreader.force_login(cls.empty_user)
        cls.group = Group.objects.create(
            title='Якобы такая группа',
            slug='test-slug',
            description='Группа с непонятной целью и содержанием',
        )
        cls.group_mock = Group.objects.create(
            title='Группа без постов',
            slug='wrong-slug',
            description='Группа, чтобы проверить, что в нее не попадают посты',
        )
        test_posts_set = [Post
                          (author=cls.author_user,
                           group=cls.group,
                           text=f'{num}) Пост за все хорошее и против плохого')
                          for num in range(12)]
        Post.objects.bulk_create(test_posts_set)

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

        cls.post = Post.objects.create(
            author=cls.author_user,
            group=cls.group,
            text='12) Пост за все хорошее и против плохого',
            image=uploaded)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()

    def test_pages_uses_correct_template(self):
        """View-функции используют соответствующие шаблоны."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug':
                            self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username':
                            self.author_user}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            self.post.id}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.auth_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_paginator(self):
        """Пагинатор корректно разбивает и выводит записи постранично"""
        paginator_addresses = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.author_user})
        ]
        for paginator in paginator_addresses:
            with self.subTest(paginator=paginator):
                response = self.client.get(paginator)
                self.assertEqual(len(response.context['page_obj']), 10)
                response = self.client.get(paginator + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)

    def test_index_show_correct_context(self):
        """Проверка контекста главной страницы"""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(response.context.get('page_obj')[0].text,
                         self.post.text)
        self.assertEqual(response.context.get('page_obj')[0].pub_date,
                         self.post.pub_date)
        self.assertEqual(response.context.get('page_obj')[0].author,
                         self.post.author)
        self.assertEqual(response.context.get('page_obj')[0].group,
                         self.post.group)
        self.assertEqual(response.context.get('page_obj')[0].image,
                         self.post.image)

    def test_group_list_show_correct_context(self):
        """Проверка контекста group_list"""
        response = (self.client.
                    get(reverse('posts:group_list',
                        kwargs={'slug': self.group.slug})))
        self.assertEqual(response.context.get('page_obj')[0].text,
                         self.post.text)
        self.assertEqual(response.context.get('page_obj')[0].pub_date,
                         self.post.pub_date)
        self.assertEqual(response.context.get('page_obj')[0].author,
                         self.post.author)
        self.assertEqual(response.context.get('page_obj')[0].group,
                         self.post.group)
        self.assertEqual(response.context.get('group'), self.post.group)
        self.assertEqual(response.context.get('page_obj')[0].image,
                         self.post.image)

    def test_profile_show_correct_context(self):
        """Проверка контекста profile"""
        response = (self.client.
                    get(reverse('posts:profile',
                        kwargs={'username': self.author_user})))
        self.assertEqual(response.context.get('page_obj')[0].text,
                         self.post.text)
        self.assertEqual(response.context.get('page_obj')[0].pub_date,
                         self.post.pub_date)
        self.assertEqual(response.context.get('page_obj')[0].author,
                         self.post.author)
        self.assertEqual(response.context.get('page_obj')[0].group,
                         self.post.group)
        self.assertEqual(response.context.get('author'), self.post.author)
        self.assertEqual(response.context.get('page_obj')[0].image,
                         self.post.image)

    def test_post_detail_show_correct_context(self):
        """Проверка контекста post_detail"""
        response = (self.auth_client.
                    get(reverse('posts:post_detail',
                        kwargs={'post_id': self.post.id})))
        self.assertEqual(response.context.get('post').id,
                         self.post.id)
        self.assertEqual(response.context.get('post').text,
                         self.post.text)
        self.assertEqual(response.context.get('post').pub_date,
                         self.post.pub_date)
        self.assertEqual(response.context.get('post').author,
                         self.post.author)
        self.assertEqual(response.context.get('post').group,
                         self.post.group)
        self.assertEqual(response.context.get('post').image,
                         self.post.image)
        self.assertFalse(response.context.get('author'))
        self.assertTrue(response.context.get('form'))

    def test_post_edit_show_correct_context(self):
        """Проверка контекста post_edit"""
        response = (self.auth_author.
                    get(reverse('posts:post_edit',
                        kwargs={'post_id': self.post.id})))
        self.assertEqual(response.context.get('form').instance.text,
                         self.post.text)
        self.assertEqual(response.context.get('form').instance.group,
                         self.post.group)
        self.assertTrue(response.context.get('is_edit'))

    def test_post_create_show_correct_context(self):
        """Проверка контекста post_create"""
        response = self.auth_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_mock_group_is_empty(self):
        """Проверка, что созданный пост не попал в другую группу"""
        response = self.client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group_mock.slug}))
        self.assertNotIn(self.post, [*response.context.get('page_obj')])

    def test_cache(self):
        """Проверка работы функции кэширования. Удаленный пост продолжает
        показываться и исчезает после очистки кэша.
        """
        post = Post.objects.create(
            author=self.author_user,
            text='Специальный пост для тестирования кэша')
        response_predelete = self.client.get(reverse('posts:index'))
        post.delete()
        response_afterdelete = self.client.get(reverse('posts:index'))
        self.assertEqual(response_predelete.content,
                         response_afterdelete.content)
        cache.clear()
        response_after_clear_cash = self.client.get(reverse('posts:index'))
        self.assertNotEqual(response_afterdelete.content,
                            response_after_clear_cash.content)

    def test_subscriptions(self):
        """Проверка функции подписок. Авторизованный пользователь может
        подписаться и отписаться.
        """
        self.auth_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author_user}))
        response = self.auth_client.get(reverse('posts:follow_index'))
        self.assertEqual(response.context.get('page_obj')[0].author,
                         self.author_user)
        response = self.auth_emptyreader.get(reverse('posts:follow_index'))
        self.assertTrue(not [*response.context.get('page_obj')])
        self.auth_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author_user}))
        response = self.auth_client.get(reverse('posts:follow_index'))
        self.assertTrue(not [*response.context.get('page_obj')])
