"""WP users imported, role and explicit Clerk link preserved on repeat."""
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from identities.models import User
pytestmark=pytest.mark.django_db

class Cursor:
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def execute(self,query):pass
    def fetchall(self):
        return [{'ID':1,'user_login':'admin','user_email':'admin@example.com','display_name':'Admin'},
                {'ID':2,'user_login':'demo','user_email':'demo@example.com','display_name':'Demo'}]
class Connection:
    def cursor(self):return Cursor()
    def close(self):pass

def test_migration_preserves_explicit_link_and_role(monkeypatch):
    from identities.management.commands import migrate_wp_users
    monkeypatch.setattr(migrate_wp_users.pymysql,'connect',lambda **kwargs:Connection())
    call_command('migrate_wp_users',verbosity=0)
    admin=User.objects.get(username='admin')
    assert admin.role=='editor' and not admin.has_usable_password()
    call_command('link_clerk_user',username='admin',clerk_user_id='user_real1234567',verbosity=0)
    admin.refresh_from_db()
    assert admin.clerk_user_id=='user_real1234567'
    other=User.objects.get(username='demo')
    other.role='editor';other.save(update_fields=['role'])
    call_command('migrate_wp_users',verbosity=0)
    admin.refresh_from_db();other.refresh_from_db()
    assert User.objects.count()==2 and other.role=='editor' and admin.clerk_user_id=='user_real1234567'
    with pytest.raises(CommandError):
        call_command('link_clerk_user',username='demo',clerk_user_id='user_real1234567',verbosity=0)
