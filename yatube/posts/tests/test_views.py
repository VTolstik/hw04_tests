from datetime import datetime
from django import forms

from django.test import Client, TestCase
from django.urls import reverse

from posts.utils import ITEMS_PER_PAGE
from posts.models import Group, Post, User


USERNAME = "AuthorName"
ADD_USERNAME = "AddName"
GROUP_SLUG = "test-slug"
ADD_SLUG = "add-test-slug"
ANOTHER_GROUP = reverse("posts:group_list", args=[ADD_SLUG])

INDEX = reverse("posts:index")
CREATE = reverse("posts:post_create")
GROUP = reverse("posts:group_list", args=[GROUP_SLUG])
PROFILE = reverse("posts:profile", args=[USERNAME])


class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.another_user = User.objects.create_user(username=ADD_USERNAME)
        cls.another_authorized_client = Client()
        cls.another_authorized_client.force_login(cls.another_user)
        cls.date = datetime.now()
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug=GROUP_SLUG,
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
            group=cls.group,
            pub_date=cls.date,
        )
        cls.another_group = Group.objects.create(
            title="Тестовая группа другая",
            slug=ADD_SLUG,
        )
        cls.POST = reverse("posts:post_detail", args=[cls.post.id])
        cls.EDIT_POST = reverse("posts:post_edit", args=[cls.post.id])

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names = {
            INDEX: 'posts/index.html',
            CREATE: 'posts/create_post.html',
            GROUP: 'posts/group_list.html',
            PROFILE: 'posts/profile.html',
            self.POST: 'posts/post_detail.html',
            self.EDIT_POST: 'posts/create_post.html',
        }
        for reverse_name, template in templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def context_post(self, post):
        """Метод проверки контекста поста."""
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.pk, self.post.pk)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response_context = self.authorized_client.get(
            INDEX).context["page_obj"]
        self.assertEqual(len(response_context), 1)
        self.context_post(response_context[0])

    def test_group_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(GROUP)
        response_context = response.context["page_obj"]
        self.assertEqual(len(response_context), 1)
        self.context_post(response_context[0])
        group = response.context.get("group")
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.description, self.group.description)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.pk, self.group.pk)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(PROFILE)
        response_context = response.context["page_obj"]
        self.assertEqual(len(response_context), 1)
        self.context_post(response_context[0])
        post_author = response.context.get("author")
        self.assertEqual(post_author, self.user)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        self.context_post(self.authorized_client.get(
            self.POST).context.get("post"))

    def test_paginator_on_pages(self):
        """Пагинация на страницах."""
        Post.objects.all().delete()
        Post.objects.bulk_create(
            Post(
                author=self.user,
                group=self.group,
                text=f"Пост #{i}",
            )
            for i in range(ITEMS_PER_PAGE + 1)
        )
        url_pages = {
            INDEX: ITEMS_PER_PAGE,
            f"{INDEX}?page=2": 1,
            GROUP: ITEMS_PER_PAGE,
            f"{GROUP}?page=2": 1,
            PROFILE: ITEMS_PER_PAGE,
            f"{PROFILE}?page=2": 1,
        }
        for url_page, args in url_pages.items():
            with self.subTest(url_page=url_page):
                self.assertEqual(
                    len(self.another_authorized_client.get(
                        url_page).context.get("page_obj")),
                    args,
                )

    form_fields = {
        'text': forms.fields.CharField,
        'group': forms.fields.ChoiceField,
    }

    def test_create_post_show_correct_context(self):
        """Проверка контекста создания поста posts:post_create"""
        response = self.authorized_client.get(CREATE)
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                field = response.context.get('form').fields[value]
                self.assertIsInstance(field, expected)

    def test_edit_post_show_correct_context(self):
        """Проверка контекста редактирование поста posts:post_create"""
        response = self.authorized_client.get(self.EDIT_POST)
        self.assertTrue(response.context.get('is_edit'))
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                field = response.context.get('form').fields[value]
                self.assertIsInstance(field, expected)

    def test_post_created_not_show_group_profile(self):
        """Проверка отсутстствия постов не в той группе"""
        urls = (
            reverse('posts:group_list', kwargs={
                'slug': self.another_group.slug}),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                page_obj = response.context.get('page_obj')
                self.assertEqual(len(page_obj), 0)

    def test_post_created_show_group_and_profile(self):
        """Проверка постов на страницах: главной, группы и пользователя"""
        urls = (INDEX, GROUP, PROFILE)
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                page_obj = response.context.get('page_obj')
                self.assertEqual(len(page_obj), 1)
