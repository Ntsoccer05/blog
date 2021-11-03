from django import forms
from django.contrib.auth import get_user_model
from .models import Post, Comment, Reply
from django.contrib.auth.forms import (
    AuthenticationForm, UserCreationForm, PasswordChangeForm,
    PasswordResetForm, SetPasswordForm
)
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.mail import BadHeaderError, send_mail, EmailMessage
from django.http import HttpResponse
from django.conf import settings
from django.forms import ModelForm, TextInput, Textarea
from ckeditor.widgets import CKEditorWidget

User = get_user_model()


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'category', 'content', 'thumbnail', 'price',)
        widgets = {
            'text': CKEditorWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class LoginForm(AuthenticationForm):
    """ログインフォーム"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            # placeholderにフィールドのラベルを入れる
            field.widget.attrs['placeholder'] = field.label


class UserCreateForm(UserCreationForm):
    """ユーザー登録用フォーム"""

    class Meta:
        model = User
        fields = ('name', 'email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data['email']
        User.objects.filter(email=email, is_active=False).delete()
        return email


class UserUpdateForm(forms.ModelForm):
    """ユーザー情報更新フォーム"""

    name = forms.CharField(help_text='※新しい名前を記入してください。', label="名前", required=True, widget=forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '名前',
            }))

    class Meta:
        model = User
        fields = ('name',)

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     for field in self.fields.values():
    #         field.widget.attrs['class'] = 'form-control'


class MyPasswordChangeForm(PasswordChangeForm):
    """パスワード変更フォーム"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class MyPasswordResetForm(PasswordResetForm):
    """パスワード忘れたときのフォーム"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class MySetPasswordForm(SetPasswordForm):
    """パスワード再設定用フォーム(パスワード忘れて再設定)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class SearchForm(forms.Form):
    freeword = forms.CharField(
        min_length=1, max_length=30, label="", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ContactForm(forms.Form):
    name = forms.CharField(
        label='',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'お名前'
        })
    )
    email = forms.EmailField(
        label='',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'メールアドレス',
        })
    )
    subject = forms.CharField(
        label='',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '件名',
        })
    )
    message = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'お問い合わせ'
        })
    )

    def send_email(self):
        message = self.cleaned_data['message']
        name = self.cleaned_data['name']
        email = self.cleaned_data['email']
        sender = self.cleaned_data['email']
        subject = self.cleaned_data['subject']
        recipient_list = [settings.EMAIL_HOST_USER]
        try:
            message = EmailMessage(subject="名前: " + name + " 内容: " + subject,
                            body="From："+sender+"\n"+message,
                            from_email=email,
                            to=recipient_list,
                        )
            message.send()
        except BadHeaderError:
            return HttpResponse('無効なヘッダが検出されました。')


class CommentForm(ModelForm):
    author = forms.CharField(help_text='※変更可能(デフォルトは「ユーザー名」)', label="名前", required=True, widget=forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '名前',
            }))
    mailadress = forms.CharField(help_text='※コメント欄には表示されません。入力すると返信があった際にメール通知します。変更可', label='メールアドレス', required=False, widget=forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'メールアドレス(※任意です)',
            }))
    text = forms.CharField(label='コメント', widget=forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'コメント内容'
            }))
    class Meta:
        model = Comment
        fields = ('text', 'author', 'mailadress')


class ReplyForm(ModelForm):
    author = forms.CharField(help_text='※変更可能(デフォルトは「ユーザー名」)', label="名前", required=True, widget=forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '名前',
            }))
    class Meta:
        model = Reply
        fields = ('text','author')
        widgets = {
            'text': Textarea(attrs={
                'class': 'form-control',
                'placeholder': '返信内容',
            }),
        }
