from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow
from .utils import page_obj_func


def index(request):
    post_list = Post.objects.select_related('author', 'group').all()
    context = {
        'page_obj': page_obj_func(request, post_list),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author').all()
    context = {
        'group': group,
        'page_obj': page_obj_func(request, post_list),
    }
    return render(request, 'posts/group_list.html', context)

def profile(request, username):
    author = get_object_or_404(User, username=username)
    post = author.posts.select_related('group')
    following = False
    if request.user.is_authenticated:
        if Follow.objects.filter(user=request.user, author=author):
            following = True
    context = {
        'page_obj': page_obj_func(request, post),
        'author': author,
        'following': following,
        'user': request.user,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None)
    if not form.is_valid() or request.method == 'GET':
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', username=post.author.username)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post.pk)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.pk)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post.pk)
    post.delete()
    return render(request, 'posts/post_delete.html')


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id,)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    context = {
        'page_obj': page_obj_func(request, post_list)
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect('posts:profile', username=username)
    Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user, author=author)
    follow.delete()
    return redirect('posts:profile', username=username)
