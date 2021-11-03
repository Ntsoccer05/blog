from django.contrib import admin
from .models import User, Post, Like, Category, PriceHistory, Comment, Reply
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import ugettext_lazy as _


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_at', 'updated_at')
    search_fields = ['title']
    list_filter = ['updated_at','created_at']
    list_display_links = ('title',)
    ordering = ('-updated_at',)


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post')
    list_display_links = ('post',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('name',)


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'created_at', 'stripe_id')
    list_display_links = ('post',)
    search_fields = ['post__title']


class MyUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'


class MyUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email',)


class MyUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('name',)}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    form = MyUserChangeForm
    add_form = MyUserCreationForm
    list_display = ('email', 'name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('email', 'name')
    ordering = ('email',)


admin.site.register(User, MyUserAdmin)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    def post_title(self, obj):
        return obj.post.title

    list_filter = ['created_at']
    list_display = ('id', 'author', 'post_title', 'text', 'useremail', 'mailadress', 'created_at',)
    list_display_links = ('text',)
    search_fields = ['text',]
    ordering = ('-created_at',)



@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):

    list_filter = ['created_at']
    list_display = ('id', 'author', 'text', 'created_at',)
    list_display_links = ('text',)
    search_fields = ['text']
    ordering = ('-created_at',)