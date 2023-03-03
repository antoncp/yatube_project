from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Comment, Follow, Group, Post

User = get_user_model()


class ModelsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.follower = User.objects.create_user(username='follower')
        cls.group = Group.objects.create(
            title='Якоба такая группа',
            slug='test-slug',
            description='Группа с непонятной целью и содержанием',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Пост про все хорошее и против всего плохого. Автор жжет.',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Еще один комментарий.',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Еще один комментарий.',
        )
        cls.subscription = Follow.objects.create(
            user=cls.follower,
            author=cls.user,
        )

    def test_group_model_have_correct_object_names(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        expected_group_name = self.group.title
        self.assertEqual(expected_group_name, str(self.group))

    def test_post_model_have_correct_object_names(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        expected_post_name = self.post.text[:15]
        self.assertEqual(expected_post_name, str(self.post))

    def test_comment_model_have_correct_object_names(self):
        """Проверяем, что у модели Comment корректно работает __str__."""
        expected_post_name = self.comment.text
        self.assertEqual(expected_post_name, str(self.comment))

    def test_follow_model_have_correct_object_names(self):
        """Проверяем, что у модели Follow корректно работает __str__."""
        expected_post_name = f'{self.follower} подписан на {self.user}'
        self.assertEqual(expected_post_name, str(self.subscription))
