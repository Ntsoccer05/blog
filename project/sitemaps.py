from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from blogapp.models import Post


class BlogPostSitemap(Sitemap):
    """
    ブログ記事のサイトマップ
    """
    changefreq = "daily"
    priority = 0.8
    protocol = "https"

    def items(self):
        return Post.objects.all()

    # モデルに get_absolute_url() が定義されている場合は不要
    def location(self, obj):
        return reverse('blogapp:post_detail', args=[obj.pk])

    def lastmod(self, obj):
        if obj.updated_at:
          return obj.updated_at
        else:
          return obj.created_at


class StaticViewSitemap(Sitemap):
    """
    静的ページのサイトマップ
    """
    changefreq = "weekly"
    priority = 0.5
    protocol = "https"

    def items(self):
        return ['blogapp:index', 'blogapp:category_list', 'blogapp:post_list']

    def location(self, item):
        return reverse(item)
