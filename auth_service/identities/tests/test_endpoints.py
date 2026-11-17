import json
from io import BytesIO
from types import SimpleNamespace
from urllib.error import HTTPError
import pytest
from django.test import Client
from identities.models import User
pytestmark=pytest.mark.django_db
KEY='separate-service-key-with-more-than-32-characters'

def check(client, token='test-session'):
    return client.post('/api/tokens/introspect/',data=json.dumps({'token':token}),
      content_type='application/json',HTTP_X_SERVICE_KEY=KEY)

def test_live_roles_and_session_revocation(monkeypatch):
    from identities import views
    monkeypatch.setenv('AUTH_INTROSPECT_KEY',KEY)
    claims=SimpleNamespace(sub='user_real123',sid='sess_real123')
    monkeypatch.setattr(views,'verify_clerk_token',lambda *args,**kwargs:claims)
    monkeypatch.setattr(views,'live_session',lambda claims:True)
    user=User.objects.create_user(username='writer',password=None,clerk_user_id=claims.sub,role='editor')
    client=Client()
    assert client.post('/api/tokens/introspect/',data='{}',content_type='application/json').status_code==403
    assert check(client).json()['role']=='editor'
    user.role='reader';user.save(update_fields=['role'])
    assert check(client).json()['role']=='reader'
    monkeypatch.setattr(views,'live_session',lambda claims:False)
    assert check(client).json()['active'] is False

def test_unknown_clerk_id_does_not_auto_link_or_elevate(monkeypatch):
    from identities import views
    monkeypatch.setenv('AUTH_INTROSPECT_KEY',KEY)
    User.objects.create_user(username='admin',password=None,role='editor',email='admin@example.com')
    monkeypatch.setattr(views,'verify_clerk_token',lambda *a,**kw:SimpleNamespace(sub='user_wrong1',sid='sess_test'))
    monkeypatch.setattr(views,'live_session',lambda claims:True)
    assert check(Client()).json()['active'] is False

def test_clerk_outage_fails_closed(monkeypatch):
    from identities import views
    monkeypatch.setenv('AUTH_INTROSPECT_KEY',KEY)
    monkeypatch.setattr(views,'verify_clerk_token',lambda *a,**kw:SimpleNamespace(sub='user_real123',sid='sess_test'))
    monkeypatch.setattr(views,'live_session',lambda claims:(_ for _ in ()).throw(OSError('network down')))
    assert check(Client()).status_code==503

def test_live_session_logs_safe_clerk_http_error_details(monkeypatch, caplog):
    from identities import views
    secret='sk_test_secret-value'
    monkeypatch.setenv('CLERK_SECRET_KEY',secret)
    error=HTTPError('https://api.clerk.com/v1/sessions/sess_private123',403,'Forbidden',
        {'clerk-trace-id':'trace-123','cf-ray':'ray-123','content-type':'application/json'},
        BytesIO(b'{"errors":[{"code":"authentication_invalid","message":"Denied sess_private123"}]}'))
    requests=[]
    def reject_request(request, **kwargs):
        requests.append(request)
        raise error
    monkeypatch.setattr(views,'urlopen',reject_request)

    with pytest.raises(HTTPError):
        views.live_session(SimpleNamespace(sid='sess_private123',sub='user_private123'))

    assert 'authentication_invalid' in caplog.text
    assert 'trace-123' in caplog.text
    assert 'ray-123' in caplog.text
    assert 'sess_private123' not in caplog.text
    assert 'user_private123' not in caplog.text
    assert secret not in caplog.text
    assert 'Denied [redacted]' in caplog.text
    assert requests[0].get_header('User-agent') == 'ca-code-challenge-auth-service/1.0'

def test_invalid_bearer_fails_closed(monkeypatch):
    from identities import views
    from brand_contracts.security import TokenRejected
    monkeypatch.setenv('AUTH_INTROSPECT_KEY',KEY)
    monkeypatch.setattr(views,'verify_clerk_token',lambda *a,**kw:(_ for _ in ()).throw(TokenRejected('bad')))
    assert check(Client()).json()['active'] is False
