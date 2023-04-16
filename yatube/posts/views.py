# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User
from .forms import PostForm
from .utils import pagination
from django.contrib.auth.decorators import login_required


def index(request):
    posts = Post.objects.select_related('author', 'group')
    page_obj = pagination(request, posts)
    title = 'Последние обновления на сайте'
    context = {
        'page_obj': page_obj,
        'title': title,
    }
    return render(request, 'posts/index.html', context)


# View-функция для страницы сообщества:
def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author', 'group')
    page_obj = pagination(request, posts)
    title = f'Записи сообщества {group.title}'
    description = group.description
    context = {
        'group': group,
        'page_obj': page_obj,
        # 'posts': posts,
        'title': title,
        'description': description,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('author', 'group')
    page_obj = pagination(request, posts)
    context = {
        'author': author,
        'page_obj': page_obj,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    context = {
        'post': post,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None)
    context = {
        'form': form,
        'title': 'Новый пост',
    }

    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            form.save()
            return redirect('posts:profile', username=post.author)
        return render(request, template, context)
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    is_edit = True
    if request.user.id != post.author.id:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        post = form.save(commit=False)
        form.save()
        return redirect('posts:post_detail', post_id=post.id)
    context = {
        'form': form,
        'is_edit': is_edit,
        'title': 'Редактирование поста',
    }
    return render(request, template, context)
