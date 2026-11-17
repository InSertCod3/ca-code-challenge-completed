"""Re-runnable user import preserving auth-owned roles and passwords."""
import os
from django.core.management.base import BaseCommand,CommandError
from django.db import transaction
import pymysql
from pydantic import ValidationError
from brand_contracts.schemas import WPUser,Role
from identities.models import User

class Command(BaseCommand):
    help='Import WP user identities and roles; credentials are managed by Clerk.'
    def handle(self,*args,**kwargs):
        try:
            db=pymysql.connect(host=os.getenv('WP_DB_HOST','db'),user=os.getenv('WORDPRESS_DB_USER','wp'),
                password=os.getenv('WORDPRESS_DB_PASSWORD','wp'),database=os.getenv('WORDPRESS_DB_NAME','wp'),
                charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor)
            try:
                with db.cursor() as c:
                    c.execute('SELECT ID, user_login, user_email, display_name FROM wp_users ORDER BY ID')
                    users=[WPUser(source_id=r['ID'],username=r['user_login'],email=r['user_email'],
                                  display_name=r['display_name']) for r in c.fetchall()]
            finally: db.close()
        except (pymysql.MySQLError,ValidationError) as exc: raise CommandError(str(exc)) from exc
        with transaction.atomic():
            for u in users:
                user,created=User.objects.get_or_create(wp_id=u.source_id,
                    defaults={'username':u.username,'email':u.email,
                              'role':Role.EDITOR.value if u.username=='admin' else Role.READER.value})
                if created:
                    user.set_unusable_password()
                    user.save(update_fields=['password'])
                else:
                    user.email=u.email
                    user.save(update_fields=['email'])
        self.stdout.write(self.style.SUCCESS(f'Synchronized {len(users)} auth users; existing roles/Clerk links preserved'))
