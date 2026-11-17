from django.db import models
from django.db.models import Avg, Count

class Industry(models.Model):
    wp_id = models.PositiveBigIntegerField(unique=True)
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120,unique=True)
    def __str__(self): return self.name

class Reviewer(models.Model):
    # Attribution only. Credentials and roles exclusively live in auth service.
    wp_id = models.PositiveBigIntegerField(unique=True)
    username = models.CharField(max_length=150)
    display_name = models.CharField(max_length=250)
    def __str__(self): return self.display_name

class BrandQuerySet(models.QuerySet):
    def with_review_stats(self):
        return self.annotate(review_count=Count('reviews'),calculated_average=Avg('reviews__rating'))

class Brand(models.Model):
    wp_id = models.PositiveBigIntegerField(unique=True)
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=200,unique=True)
    body = models.TextField(blank=True)
    short_description = models.TextField(blank=True)
    description_is_edited = models.BooleanField(default=False)
    website_url = models.URLField(max_length=500,blank=True)
    founded_year = models.PositiveSmallIntegerField(null=True,blank=True)
    headquarters = models.CharField(max_length=250,blank=True)
    wp_average_rating = models.DecimalField(max_digits=3,decimal_places=1,null=True,blank=True)
    industry = models.ForeignKey(Industry,null=True,blank=True,on_delete=models.SET_NULL,related_name='brands')
    published_at = models.DateTimeField()
    objects = BrandQuerySet.as_manager()
    def __str__(self): return self.name

class Review(models.Model):
    wp_id = models.PositiveBigIntegerField(unique=True)
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=200,unique=True)
    brand = models.ForeignKey(Brand,on_delete=models.CASCADE,related_name='reviews')
    author = models.ForeignKey(Reviewer,on_delete=models.PROTECT,related_name='reviews')
    reviewer_name = models.CharField(max_length=250,blank=True)
    reviewer_location = models.CharField(max_length=250,blank=True)
    rating = models.PositiveSmallIntegerField(choices=[(n,str(n)) for n in range(1,6)])
    body = models.TextField(blank=True)
    published_at = models.DateTimeField(db_index=True)
    class Meta: ordering = ('-published_at','-wp_id')
    def __str__(self): return self.name
