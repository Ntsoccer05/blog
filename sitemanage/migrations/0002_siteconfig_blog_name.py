# Generated by Django 3.1 on 2021-11-03 09:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitemanage', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteconfig',
            name='blog_name',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='ブログ名'),
        ),
    ]
