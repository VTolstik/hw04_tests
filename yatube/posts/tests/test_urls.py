from django.test import TestCase, Client
from posts.models import User, Post, Group


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст поста',
            group=cls.group
        )
        cls.INDEX = '/'
        cls.CREATE = '/create/'
        cls.GROUP = f'/group/{cls.group.slug}/'
        cls.PROFILE = f'/profile/{cls.user.username}/'
        cls.POST = f'/posts/{cls.post.id}/'
        cls.EDIT_POST = f'/posts/{cls.post.id}/edit/'
        cls.UNEXISTING = '/unexisting_page/'

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user)
        self.user = User.objects.create(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names = {
            self.INDEX: 'posts/index.html',
            self.CREATE: 'posts/create_post.html',
            self.GROUP: 'posts/group_list.html',
            self.PROFILE: 'posts/profile.html',
            self.POST: 'posts/post_detail.html',
            self.EDIT_POST: 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_url_access(self):
        guest_access = {
            self.INDEX: 200,
            self.UNEXISTING: 404,
            self.CREATE: 302,
            self.GROUP: 200,
            self.PROFILE: 200,
            self.POST: 200,
            self.EDIT_POST: 302,
        }

        authorized_access = {
            self.CREATE: 200,
            self.EDIT_POST: 302,
        }

        for url, status in guest_access.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status)

        for url, status in authorized_access.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, status)

        response = self.author_client.get(self.EDIT_POST)
        self.assertEqual(response.status_code, 200)
