import stripe
from django.views.generic.edit import FormView
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import login
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView,
    PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
)
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import render, resolve_url, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.core.signing import BadSignature, SignatureExpired, loads, dumps
from django.views.generic import TemplateView, CreateView, DetailView, UpdateView, DeleteView, ListView
from .models import Post, Like, Category, Comment, Reply, PriceHistory
from django.urls import reverse_lazy
from django.template.loader import render_to_string
from django.contrib import messages
from .forms import (PostForm, LoginForm, UserCreateForm, UserUpdateForm, MyPasswordChangeForm,
                    MyPasswordResetForm, MySetPasswordForm, SearchForm, ContactForm, CommentForm, ReplyForm)
from .mixins import SuperuserRequiredMixin


stripe.api_key = settings.STRIPE_SECRET_KEY

User = get_user_model()


class OnlyMyPostMixin(UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        post = Post.objects.get(id=self.kwargs['pk'])
        return post.author == self.request.user

class OnlyMyCommentMixin(UserPassesTestMixin):
    raise_exception=True

    def test_func(self):
        comment=Comment.objects.get(id=self.kwargs['pk'])
        return comment.useremail==self.request.user.email

class OnlyMyReplyMixin(UserPassesTestMixin):
    raise_exception=True

    def test_func(self):
        reply=Reply.objects.get(id=self.kwargs['pk'])
        return reply.authority==self.request.user.email

class Index(TemplateView):
    template_name = 'blogapp/index.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        if Post.updated_at:
            post_list = Post.objects.all().order_by('-updated_at')[:9]
        else:
            post_list = Post.objects.all().order_by('-created_at')[:9]
        context = {
            'post_list': post_list,
        }
        return context


class PostCreate(SuperuserRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    success_url = reverse_lazy('blogapp:index')

    def form_valid(self, form):
        form.instance.author_id = self.request.user.id
        return super(PostCreate, self).form_valid(form)

    def get_success_url(self):
        messages.success(self.request, '記事を登録しました。')
        return resolve_url('blogapp:index')


class PostDetail(DetailView):
    model = Post

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['publick_key'] = settings.STRIPE_PUBLIC_KEY
        detail_data = Post.objects.get(id=self.kwargs['pk'])
        category_posts = Post.objects.filter(
            category=detail_data.category).order_by('-created_at')[:5]
        params = {
            'object': detail_data,
            'category_posts': category_posts,
            'context': context,
        }
        return params

    def post(self, request, *args, **kwargs):
        post = self.get_object()
        token = request.POST['stripeToken']
        try:
            charge = stripe.Charge.create(
                amount=post.price,
                currency='jpy',
                source=token,
                description='メール：{} メンター名：{}'.format(
                    request.user.email, post.title),
            )
            messages.info(self.request, 'お支払い完了しました')
        except stripe.error.CardError as e:
            context = self.get_context_data()
            context['message'] = 'Your payment cannot be completed The card has been declined'
            return render(request, 'blogapp/post_detail.html', context)
        else:
            PriceHistory.objects.create(
                post=post, user=request.user, stripe_id=charge.id)
            return redirect('blogapp:index')


class PostUpdate(SuperuserRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm

    def get_success_url(self):
        messages.info(self.request, '記事を更新しました。')
        return resolve_url('blogapp:post_detail', pk=self.kwargs['pk'])


class PostDelete(SuperuserRequiredMixin, DeleteView):
    model = Post

    def get_success_url(self):
        messages.info(self.request, '記事を削除しました。')
        return resolve_url('blogapp:index')


class PostList(ListView):
    model = Post
    paginate_by = 5

    def get_queryset(self):
        if Post.updated_at:
            return Post.objects.all().order_by('-updated_at')
        else:
            return Post.objects.all().order_by('-created_at')


class Login(LoginView):
    form_class = LoginForm
    template_name = 'blogapp/login.html'


class Logout(LogoutView):
    template_name = 'blogapp/logout.html'


class UserCreate(CreateView):
    """ユーザー仮登録"""
    template_name = 'blogapp/user_create.html'
    form_class = UserCreateForm

    def form_valid(self, form):
        """仮登録と本登録用メールの発行."""
        # 仮登録と本登録の切り替えは、is_active属性を使うと簡単です。
        # 退会処理も、is_activeをFalseにするだけにしておくと捗ります。
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        # アクティベーションURLの送付
        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol': 'https' if self.request.is_secure() else 'http',
            'domain': domain,
            'token': dumps(user.pk),
            'user': user,
        }

        subject = render_to_string(
            'blogapp/mail_template/create/subject.txt', context)
        message = render_to_string(
            'blogapp/mail_template/create/message.txt', context)

        user.email_user(subject, message)
        return redirect('blogapp:user_create_done')


class UserCreateDone(TemplateView):
    """ユーザー仮登録したよ"""
    template_name = 'blogapp/user_create_done.html'


class UserCreateComplete(TemplateView):
    """メール内URLアクセス後のユーザー本登録"""
    template_name = 'blogapp/user_create_complete.html'
    timeout_seconds = getattr(
        settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)  # デフォルトでは1日以内

    def get(self, request, **kwargs):
        """tokenが正しければ本登録."""
        token = kwargs.get('token')
        try:
            user_pk = loads(token, max_age=self.timeout_seconds)

        # 期限切れ
        except SignatureExpired:
            return HttpResponseBadRequest()

        # tokenが間違っている
        except BadSignature:
            return HttpResponseBadRequest()

        # tokenは問題なし
        else:
            try:
                user = User.objects.get(pk=user_pk)
            except User.DoesNotExist:
                return HttpResponseBadRequest()
            else:
                if not user.is_active:
                    # まだ仮登録で、他に問題なければ本登録とする
                    user.is_active = True
                    user.save()
                    return super().get(request, **kwargs)

        return HttpResponseBadRequest()


class OnlyYouMixin(UserPassesTestMixin):
    """本人か、スーパーユーザーだけユーザーページアクセスを許可する"""
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return user.pk == self.kwargs['pk'] or user.is_superuser


class UserDetail(OnlyYouMixin, DetailView):
    """ユーザーの詳細ページ"""
    model = User
    # デフォルトユーザーを使う場合に備え、きちんとtemplate名を書く
    template_name = 'blogapp/user_detail.html'


class UserUpdate(OnlyYouMixin, UpdateView):
    """ユーザー情報更新ページ"""
    model = User
    form_class = UserUpdateForm
    template_name = 'blogapp/user_form.html'  # デフォルトユーザーを使う場合に備え、きちんとtemplate名を書く

    def get_success_url(self):
        return resolve_url('blogapp:user_detail', pk=self.kwargs['pk'])


class PasswordChange(PasswordChangeView):
    """パスワード変更ビュー"""
    form_class = MyPasswordChangeForm
    success_url = reverse_lazy('blogapp:password_change_done')
    template_name = 'blogapp/password_change.html'


class PasswordChangeDone(PasswordChangeDoneView):
    """パスワード変更しました"""
    template_name = 'blogapp/password_change_done.html'


class PasswordReset(PasswordResetView):
    """パスワード変更用URLの送付ページ"""
    subject_template_name = 'blogapp/mail_template/password_reset/subject.txt'
    email_template_name = 'blogapp/mail_template/password_reset/message.txt'
    template_name = 'blogapp/password_reset_form.html'
    form_class = MyPasswordResetForm
    success_url = reverse_lazy('blogapp:password_reset_done')


class PasswordResetDone(PasswordResetDoneView):
    """パスワード変更用URLを送りましたページ"""
    template_name = 'blogapp/password_reset_done.html'


class PasswordResetConfirm(PasswordResetConfirmView):
    """新パスワード入力ページ"""
    form_class = MySetPasswordForm
    success_url = reverse_lazy('blogapp:password_reset_complete')
    template_name = 'blogapp/password_reset_confirm.html'


class PasswordResetComplete(PasswordResetCompleteView):
    """新パスワード設定しましたページ"""
    template_name = 'blogapp/password_reset_complete.html'


@login_required
def Like_add(request, *args, **kwargs):
    post = Post.objects.get(id=kwargs['post_id'])
    is_liked = Like.objects.filter(user=request.user, post=post).count()
    if is_liked > 0:
        liking = Like.objects.get(
            post_id=kwargs['post_id'], user=request.user)
        liking.delete()
        post.like_num -= 1
        # post.save()
        messages.info(request, 'お気に入りを削除しました。')
        return redirect('blogapp:index')
    post.like_num += 1
    # post.save()
    like = Like()
    like.user = request.user
    like.post = post
    like.save()

    messages.success(request, 'お気に入りに追加しました。')
    return redirect('blogapp:index')


class CategoryList(ListView):
    model = Category


class CategoryDetail(DetailView):
    model = Category
    slug_field = 'name_en'
    slug_url_kwarg = 'name_en'

    def get_context_data(self, *args, **kwargs):
        detail_data = Category.objects.get(name_en=self.kwargs['name_en'])
        category_posts = Post.objects.filter(
            category=detail_data.id).order_by('-created_at')

        params = {
            'object': detail_data,
            'category_posts': category_posts,
        }

        return params


def Search(request):
    if request.method == 'POST':
        searchform = SearchForm(request.POST)

        if searchform.is_valid():
            freeword = searchform.cleaned_data['freeword']
            search_list = Post.objects.filter(
                Q(title__icontains=freeword) | Q(content__icontains=freeword))

        params = {
            'search_list': search_list,
        }

        return render(request, 'blogapp/search.html', params)


class LikeDetail(ListView):
    model = Like

    paginate_by = 5

    def get_queryset(self):
        return Like.objects.filter(user=self.request.user)


class ContactFormView(FormView):
    template_name = 'blogapp/contact_form.html'
    form_class = ContactForm

    def form_valid(self, form):
        form.send_email()
        return super().form_valid(form)

    def get_success_url(self):
        messages.info(self.request, 'お問い合わせは正常に送信されました。')
        return resolve_url('blogapp:index')


class CommentFormView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm

    def form_valid(self, form):
        comment = form.save(commit=False)
        post_pk = self.kwargs['pk']
        post = get_object_or_404(Post, pk=post_pk)
        comment.useremail = self.request.user.email
        comment.post = post
        comment.request = self.request
        comment.save()
        return redirect('blogapp:post_detail', pk=post_pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post_pk = self.kwargs['pk']
        context['post'] = get_object_or_404(Post, pk=post_pk)
        context['form'] = CommentForm( initial = { 
                'author': self.request.user.name,
                'mailadress' : self.request.user.email, 
            }) 
        return context


class CommentDelete(OnlyMyCommentMixin, DeleteView):
    model = Comment

    def get_success_url(self):
        comment = get_object_or_404(Comment, pk=self.kwargs['pk'])
        pk = comment.post.id
        messages.info(self.request, 'コメントを削除しました。')
        return resolve_url('blogapp:post_detail', pk=pk)


class ReplyFormView(LoginRequiredMixin, CreateView):
    model = Reply
    form_class = ReplyForm

    def form_valid(self, form):
        reply = form.save(commit=False)
        comment_pk = self.kwargs['pk']
        comment = get_object_or_404(Comment, pk=comment_pk)
        reply.comment = comment
        reply.request = self.request
        reply.authority = self.request.user.email
        reply.save()
        return redirect('blogapp:post_detail', pk=reply.comment.post.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs['pk']
        comment = get_object_or_404(Comment, pk=pk)
        context['comment'] = comment
        context['post'] = comment.post
        context['form'] = ReplyForm( initial = { 'author': self.request.user.name } ) 
        return context


class ReplyDelete(OnlyMyReplyMixin, DeleteView):
    model = Reply

    def get_success_url(self):
        reply = get_object_or_404(Reply, pk=self.kwargs['pk'])
        pk = reply.comment.post.id
        messages.info(self.request, '返信コメントを削除しました。')
        return resolve_url('blogapp:post_detail', pk=pk)


def google(request):
    return render(request, 'blogapp/google285b2115e8e0c8a6.html')


class Privacy(TemplateView):
    template_name = 'blogapp/privacy.html'


class Service(TemplateView):
    template_name = 'blogapp/service.html'


class AskedQuestion(TemplateView):
    template_name = 'blogapp/asked_question.html'


