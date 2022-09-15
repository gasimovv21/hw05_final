from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow, Comment, UserIp
from .utils import page_obj_func


def index(request):
    post_list = Post.objects.select_related('author', 'group').all()
    context = {
        'page_obj': page_obj_func(request, post_list),
    }
    return render(request, 'posts/index.html', context)


def get_client_ip(request):
    x_forw_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forw_for is not None:
        ip = x_forw_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def show_client_ip(request):
    ip_adresse = get_client_ip(request)
    UserIp.objects.all().create(Ip=ip_adresse)

    return render(request, 'adresse.html', {"ip_adresse":ip_adresse})


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
    following = (
        True if request.user.is_authenticated
        and author.following.filter(user=request.user).exists() else False)
    context = {
        'page_obj': page_obj_func(request, post),
        'author': author,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    following = (
        True if request.user.is_authenticated
        and post.author.following.filter(
            user=request.user).exists() else False)
    context = {
        'post': post,
        'form': form,
        'comments': post.comments.all(),
        'following': following,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None)
    if not form.is_valid() or request.method == 'GET':
        return render(request, 'posts/post_create.html', {'form': form})
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
    context = {
        'form': form,
        'post': post,
    }
    return render(request, 'posts/post_edit.html', context)


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
def comment_delete(request, comment_id, post_id):
    comment = get_object_or_404(Comment, id=comment_id)
    post = get_object_or_404(Post, id=post_id)
    if comment.author == request.user or post.author == request.user:
        comment.delete()
    else:
        return redirect('posts:post_detail', post.pk)
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
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(user=request.user,
                          author__username=username).delete()
    return redirect('posts:profile', username=username)
