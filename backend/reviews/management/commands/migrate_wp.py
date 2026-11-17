"""Atomic, repeatable MariaDB -> normalized Django import, Pydantic validated before writes."""
from collections import defaultdict
from datetime import timezone as dt_timezone
from decimal import Decimal
from html import unescape
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.html import strip_tags
import pymysql
from pydantic import ValidationError
from brand_contracts.schemas import WPBrand, WPIndustry, WPReview, WPUser
from reviews.models import Industry, Reviewer, Brand, Review

def clean(value):
    return ' '.join(unescape(strip_tags(value or '')).split())

def snapshot(cursor):
    cursor.execute('SELECT term_id, name, slug FROM wp_terms')
    terms={int(r['term_id']):r for r in cursor.fetchall()}
    cursor.execute("SELECT term_taxonomy_id, term_id FROM wp_term_taxonomy WHERE taxonomy='industry'")
    taxonomy={int(r['term_taxonomy_id']):int(r['term_id']) for r in cursor.fetchall()}
    industries=[WPIndustry(source_id=i,name=terms[i]['name'],slug=terms[i]['slug']) for i in sorted(set(taxonomy.values()))]
    cursor.execute('SELECT object_id, term_taxonomy_id FROM wp_term_relationships')
    assignments={int(r['object_id']):taxonomy[int(r['term_taxonomy_id'])] for r in cursor.fetchall() if int(r['term_taxonomy_id']) in taxonomy}
    cursor.execute('SELECT ID, user_login, user_email, display_name FROM wp_users ORDER BY ID')
    users=[WPUser(source_id=r['ID'],username=r['user_login'],email=r['user_email'],display_name=r['display_name']) for r in cursor.fetchall()]
    ids={u.source_id for u in users}
    cursor.execute("""SELECT pm.post_id, pm.meta_key, pm.meta_value FROM wp_postmeta pm
                      JOIN wp_posts p ON p.ID=pm.post_id WHERE p.post_type IN ('brand','review')""")
    meta=defaultdict(dict)
    for r in cursor.fetchall(): meta[int(r['post_id'])][r['meta_key']]=r['meta_value']
    cursor.execute("""SELECT ID, post_author, post_title, post_name, post_content, post_excerpt,
                      post_date_gmt, post_type FROM wp_posts
                      WHERE post_status='publish' AND post_type IN ('brand','review') ORDER BY ID""")
    brands=[]; reviews=[]
    for p in cursor.fetchall():
        source_id=int(p['ID']); m=meta[source_id]
        common={'source_id':source_id,'name':clean(p['post_title']),'slug':p['post_name'],
                'body':clean(p['post_content']),
                'published_at':p['post_date_gmt'].replace(tzinfo=dt_timezone.utc)}
        if p['post_type']=='brand':
            brands.append(WPBrand(**common,short_description=clean(p['post_excerpt'] or p['post_content'])[:500],
                  website_url=m.get('website_url',''),founded_year=int(m['founded_year']) if m.get('founded_year') else None,
                  headquarters=m.get('headquarters',''),
                  source_average_rating=float(m['average_rating']) if m.get('average_rating') else None,
                  industry_id=assignments.get(source_id)))
        else:
            if int(p['post_author']) not in ids: raise CommandError(f'unknown review author {source_id}')
            reviews.append(WPReview(**common,brand_source_id=int(m.get('brand',0)),
                 author_source_id=int(p['post_author']),rating=int(m.get('rating',0)),
                 reviewer_name=m.get('reviewer_name',''),reviewer_location=m.get('reviewer_location','')))
    brand_ids={b.source_id for b in brands}
    if any(r.brand_source_id not in brand_ids for r in reviews):
        raise CommandError('review references a nonpublished brand')
    return industries,users,brands,reviews

class Command(BaseCommand):
    help='Validate and import published WP brands/reviews, safely re-runnable.'
    def add_arguments(self,parser):
        parser.add_argument('--dry-run',action='store_true')
        parser.add_argument('--prune',action='store_true')

    def handle(self,*args,**options):
        try:
            connection=pymysql.connect(host=os.getenv('WP_DB_HOST','db'),database=os.getenv('WORDPRESS_DB_NAME','wp'),
                user=os.getenv('WORDPRESS_DB_USER','wp'),password=os.getenv('WORDPRESS_DB_PASSWORD','wp'),
                cursorclass=pymysql.cursors.DictCursor,charset='utf8mb4',connect_timeout=10,read_timeout=30)
            try:
                with connection.cursor() as cursor: industries,users,brands,reviews=snapshot(cursor)
            finally: connection.close()
        except (pymysql.MySQLError,ValidationError,ValueError,TypeError) as exc:
            raise CommandError(f'WordPress source validation failed: {exc}') from exc
        if options['dry_run']:
            self.stdout.write(f'Validated {len(industries)} industries, {len(users)} users, {len(brands)} brands, {len(reviews)} reviews')
            return
        with transaction.atomic():
            for i in industries:
                Industry.objects.update_or_create(wp_id=i.source_id,defaults={'name':i.name,'slug':i.slug})
            for u in users:
                Reviewer.objects.update_or_create(wp_id=u.source_id,defaults={'username':u.username,'display_name':u.display_name})
            for b in brands:
                existing=Brand.objects.filter(wp_id=b.source_id).first()
                defaults=dict(name=b.name,slug=b.slug,body=b.body,website_url=b.website_url,
                    founded_year=b.founded_year,headquarters=b.headquarters,
                    wp_average_rating=Decimal(str(b.source_average_rating)) if b.source_average_rating is not None else None,
                    industry=Industry.objects.filter(wp_id=b.industry_id).first(),published_at=b.published_at)
                if not existing or not existing.description_is_edited:
                    defaults['short_description']=b.short_description
                Brand.objects.update_or_create(wp_id=b.source_id,defaults=defaults)
            for r in reviews:
                Review.objects.update_or_create(wp_id=r.source_id,defaults={
                    'name':r.name,'slug':r.slug,'body':r.body,'rating':r.rating,
                    'brand':Brand.objects.get(wp_id=r.brand_source_id),
                    'author':Reviewer.objects.get(wp_id=r.author_source_id),
                    'reviewer_name':r.reviewer_name,'reviewer_location':r.reviewer_location,
                    'published_at':r.published_at})
            if options['prune']:
                Review.objects.exclude(wp_id__in=[r.source_id for r in reviews]).delete()
                Brand.objects.exclude(wp_id__in=[b.source_id for b in brands]).delete()
                Reviewer.objects.exclude(wp_id__in=[u.source_id for u in users]).delete()
                Industry.objects.exclude(wp_id__in=[i.source_id for i in industries]).delete()
        self.stdout.write(self.style.SUCCESS(f'Imported {len(brands)} brands, {len(reviews)} reviews and {len(users)} reviewer snapshots'))
