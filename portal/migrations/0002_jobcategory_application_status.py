import django.db.models.deletion
from django.db import migrations, models


def migrate_categories_forward(apps, schema_editor):
    JobPost = apps.get_model('portal', 'JobPost')
    JobCategory = apps.get_model('portal', 'JobCategory')

    for job in JobPost.objects.all():
        name = (job.category or 'General').strip() or 'General'
        category, _ = JobCategory.objects.get_or_create(name=name)
        job.category_ref = category
        job.save(update_fields=['category_ref'])


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
            options={
                'verbose_name_plural': 'job categories',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='jobapplication',
            name='status',
            field=models.CharField(
                choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')],
                default='pending',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='jobpost',
            name='category_ref',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='jobs',
                to='portal.jobcategory',
            ),
        ),
        migrations.RunPython(migrate_categories_forward, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='jobpost',
            name='category',
        ),
        migrations.RenameField(
            model_name='jobpost',
            old_name='category_ref',
            new_name='category',
        ),
        migrations.AlterField(
            model_name='jobpost',
            name='category',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='jobs',
                to='portal.jobcategory',
            ),
        ),
    ]
