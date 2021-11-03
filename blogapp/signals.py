from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from .models import Comment, Reply



@receiver(post_save, sender=Comment)
def send_mail_to_author(sender, instance, created, **kwargs):
    if created:
        # views.py側で、requestオブジェクトをインスタンスに格納しています。
        request = instance.request

        # コメントの投稿者を識別するため、投稿者のセッションにコメントのpkを入れておく
        request.session[str(instance.pk)] = True

        context = {
            'post': instance.post,
        }
        subject = render_to_string('blogapp/mail/comment_notify_subject.txt', context, request)
        message = render_to_string('blogapp/mail/comment_notify_message.txt', context, request)
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [settings.DEFAULT_FROM_EMAIL]
        send_mail(subject, message, from_email, recipient_list)


@receiver(post_save, sender=Reply)
def send_mail_to_comment_user(sender, instance, created, **kwargs):
    """コメントに返信があったことを、管理者とコメント者に伝える"""
    if created:
        # views.py側で、requestオブジェクトをインスタンスに格納しています。
        request = instance.request

        # コメントの投稿者を識別するため、投稿者のセッションにコメントのpkを入れておく
        request.session[str(instance.pk)] = True

        comment = instance.comment
        post = comment.post

        context = {
            'post': post,
        }
        subject = render_to_string('blogapp/mail/reply_notify_subject.txt', context, request)
        message = render_to_string('blogapp/mail/reply_notify_message.txt', context, request)

        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = []

        # コメントした人がメールアドレスを入力してれば、返信があったことを知らせる
        if (comment.useremail or comment.mailadress) and not request.session.get(str(comment.pk)):
            recipient_list.extend([comment.useremail, comment.mailadress])
        email = EmailMessage(subject, message, from_email, recipient_list)
        email.send()
