# Generated by Django 3.0.6 on 2023-06-26 02:10

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('name', models.CharField(max_length=225, primary_key=True, serialize=False)),
                ('path', models.TextField(blank=True, null=True)),
                ('value', models.CharField(max_length=225)),
                ('html', models.TextField()),
            ],
        ),
    ]
