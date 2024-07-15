# Generated by Django 5.0.6 on 2024-07-10 20:51

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("calendrier", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="activite",
            old_name="nom",
            new_name="activite",
        ),
        migrations.RemoveField(
            model_name="activite",
            name="heure_debut",
        ),
        migrations.RemoveField(
            model_name="activite",
            name="heure_fin",
        ),
        migrations.RemoveField(
            model_name="activite",
            name="motif",
        ),
        migrations.AddField(
            model_name="activite",
            name="object",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="activite",
            name="date_debut",
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name="activite",
            name="date_fin",
            field=models.DateTimeField(),
        ),
    ]
