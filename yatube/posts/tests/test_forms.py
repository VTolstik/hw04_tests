from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User

USERNAME = "NoName"
ANOTHER_USERNAME = "NoName2"
GROUP_SLUG = "test-slug"
ANOTHER_SLUG = "test-slug2"
CREATE_POST = reverse("posts:post_create")
LOGIN_URL = reverse("users:login")
PROFILE_URL = reverse("posts:profile", args=[USERNAME])


class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.another_user = User.objects.create_user(username=ANOTHER_USERNAME)
        cls.another_authorized_client = Client()
        cls.another_authorized_client.force_login(cls.another_user)
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug=GROUP_SLUG,
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
            group=cls.group,
        )
        cls.POST_URL = reverse("posts:post_detail", args=[cls.post.pk])
        cls.EDIT_POST_URL = reverse("posts:post_edit", args=[cls.post.pk])
        cls.EDIT_POST_URL_REDIRECT = f"{LOGIN_URL}?next={cls.EDIT_POST_URL}"
        cls.another_group = Group.objects.create(
            title="Тестовая группа другая",
            slug=ANOTHER_SLUG,
        )

    def test_create_post(self):
        """Проверим создание поста через форму
        авторизированным клиентом"""
        posts = Post.objects.all()
        # posts = set(Post.objects.all())
        form_data = {
            "text": "Тестовый пост2",
            "group": self.group.id,
        }
        response = self.authorized_client.post(
            CREATE_POST,
            data=form_data,
            # follow=True,
        )
        # posts = set(Post.objects.all()) - posts
        # self.assertEqual(len(posts), 1)
        self.assertEqual(posts.count(), 2)
        # post = posts.pop()
        post = Post.objects.get(id=self.post.pk + 1)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(post.group.id, form_data["group"])
        self.assertEqual(post.text, form_data["text"])
        self.assertEqual(post.author, self.user)
        self.assertRedirects(response, PROFILE_URL)

    def test_guest_client_not_create_post(self):
        """Проверим создание поста через форму
        неавторизированным клиентом"""
        posts = set(Post.objects.all())
        form_data = {
            "text": "Тестовый пост2",
            "group": self.group.id,
        }
        response = self.guest_client.post(
            CREATE_POST,
            data=form_data,
        )
        self.assertEqual(posts, set(Post.objects.all()))
        self.assertEqual(response.status_code, 302)

    def test_post_edit_post(self):
        """Проверяем редактирование поста
        авторизированным клиентом"""
        post_count = Post.objects.count()
        form_data = {
            "text": "Тестовый пост редактирование",
            "group": self.another_group.id,
        }
        response = self.authorized_client.post(
            self.EDIT_POST_URL, data=form_data, follow=True
        )
        post = Post.objects.get(id=self.post.pk)
        # post = self.post
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.POST_URL)
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group.id, form_data["group"])
        self.assertEqual(post.text, form_data["text"])

    def test_guest_or_another_not_edit_post(self):
        """Проверяем редактирование поста неавторизированным
        клиентом или не автором поста"""
        post_count = Post.objects.count()
        clients_not_edit = [
            (self.another_authorized_client, self.POST_URL),
            (self.guest_client, self.EDIT_POST_URL_REDIRECT),
        ]
        form_data = {
            "text": "Тестовый пост редактирование",
            "group": self.another_group.id,
        }
        for client, redirect in clients_not_edit:
            with self.subTest(client=client):
                response = client.post(
                    self.EDIT_POST_URL, data=form_data,
                )
                post = Post.objects.get(id=self.post.pk)
                self.assertEqual(Post.objects.count(), post_count)
                self.assertRedirects(response, redirect)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.group, self.post.group)
