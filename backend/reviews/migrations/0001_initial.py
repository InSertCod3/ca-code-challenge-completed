from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial=True
    dependencies=[]
    operations=[
        migrations.CreateModel(name='Industry',fields=[
            ('id',models.BigAutoField(primary_key=True,serialize=False)),
            ('wp_id',models.PositiveBigIntegerField(unique=True)),
            ('name',models.CharField(max_length=120)),('slug',models.SlugField(max_length=120,unique=True))]),
        migrations.CreateModel(name='Reviewer',fields=[
            ('id',models.BigAutoField(primary_key=True,serialize=False)),
            ('wp_id',models.PositiveBigIntegerField(unique=True)),
            ('username',models.CharField(max_length=150)),('display_name',models.CharField(max_length=250))]),
        migrations.CreateModel(name='Brand',fields=[
            ('id',models.BigAutoField(primary_key=True,serialize=False)),('wp_id',models.PositiveBigIntegerField(unique=True)),
            ('name',models.CharField(max_length=250)),('slug',models.SlugField(max_length=200,unique=True)),
            ('body',models.TextField(blank=True)),('short_description',models.TextField(blank=True)),
            ('description_is_edited',models.BooleanField(default=False)),
            ('website_url',models.URLField(max_length=500,blank=True)),
            ('founded_year',models.PositiveSmallIntegerField(null=True,blank=True)),
            ('headquarters',models.CharField(max_length=250,blank=True)),
            ('wp_average_rating',models.DecimalField(max_digits=3,decimal_places=1,null=True,blank=True)),
            ('published_at',models.DateTimeField()),
            ('industry',models.ForeignKey(null=True,blank=True,on_delete=django.db.models.deletion.SET_NULL,
                                          related_name='brands',to='reviews.industry'))]),
        migrations.CreateModel(name='Review',fields=[
            ('id',models.BigAutoField(primary_key=True,serialize=False)),('wp_id',models.PositiveBigIntegerField(unique=True)),
            ('name',models.CharField(max_length=250)),('slug',models.SlugField(max_length=200,unique=True)),
            ('reviewer_name',models.CharField(max_length=250,blank=True)),
            ('reviewer_location',models.CharField(max_length=250,blank=True)),
            ('rating',models.PositiveSmallIntegerField(choices=[(n,str(n)) for n in range(1,6)])),
            ('body',models.TextField(blank=True)),('published_at',models.DateTimeField(db_index=True)),
            ('author',models.ForeignKey(to='reviews.reviewer',related_name='reviews',on_delete=django.db.models.deletion.PROTECT)),
            ('brand',models.ForeignKey(to='reviews.brand',related_name='reviews',on_delete=django.db.models.deletion.CASCADE))],
            options={'ordering':('-published_at','-wp_id')}),
    ]
