# Generated by Django 2.2.16 on 2022-05-11 19:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0029_auto_20220511_1240'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='text',
            field=models.TextField(help_text='Добавьте текст поста!', verbose_name='Добавьте комментарий'),
        ),
    ]
