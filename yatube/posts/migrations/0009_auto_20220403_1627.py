# Generated by Django 2.2.9 on 2022-04-03 12:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0008_auto_20220403_0345'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ('-pub_date',), 'verbose_name': 'Публикация', 'verbose_name_plural': 'Публикаций'},
        ),
    ]
