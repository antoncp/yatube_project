import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_author = Client()
        cls.author_user = User.objects.create_user(username='author')
        cls.auth_author.force_login(cls.author_user)
        cls.post = Post.objects.create(
            author=cls.author_user,
            text='Пост, который будет изменен в ходе теста post_edit.',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        tasks_count = Post.objects.count()
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
            'text': 'Созданный специально для проверки пост',
            'image': uploaded
        }
        response = self.auth_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        new_post = Post.objects.latest('id')
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.author_user}))
        self.assertEqual(Post.objects.count(), tasks_count + 1)
        self.assertEqual(new_post.text, form_data.get('text'))
        self.assertEqual(new_post.image.name,
                         'posts/' + form_data.get('image').name)

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        form_data = {
            'text': 'После правки текст такой.',
        }
        response = self.auth_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.id}))
        self.assertEqual(get_object_or_404(Post, id=self.post.id).text,
                         form_data.get('text'))

    def test_create_comment(self):
        """Валидная форма создает комментарий к посту."""
        form_data = {
            'text': 'Новый комментарий',
        }
        response = self.auth_author.post(
            (reverse('posts:add_comment', kwargs={'post_id': self.post.id})),
            data=form_data,
            follow=True
        )
        comment = Comment.objects.latest('id')
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.id}))
        self.assertEqual(comment.text, form_data.get('text'))
        self.assertEqual(response.context.get('comments')[0].text,
                         form_data.get('text'))
