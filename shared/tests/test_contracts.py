"""Pytest 9 tests for Clerk session validation and shared Pydantic models."""
from datetime import datetime, timedelta, timezone
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from pydantic import ValidationError
from brand_contracts.schemas import BrandListQuery, BrandPatch, Role, WPBrand
from brand_contracts.security import verify_clerk_token, TokenRejected, has_role

ISS = 'https://demo.clerk.accounts.dev'
AZP = 'http://localhost:3000'

@pytest.fixture
def keypair():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    class FakeJWKS:
        def get_signing_key_from_jwt(self, token):
            class Key: pass
            result = Key();result.key = private.public_key()
            return result
    return private, FakeJWKS()

def mint(private, **updates):
    now = int(datetime.now(timezone.utc).timestamp())
    payload = {'sub':'user_test1234','sid':'sess_test1234','iss':ISS,'azp':AZP,
               'iat':now-1,'nbf':now-1,'exp':now+60,'fva':[0,0]}
    payload.update(updates)
    return jwt.encode(payload, private, algorithm='RS256', headers={'kid':'sample'})

def verify(token, client):
    return verify_clerk_token(token,issuer=ISS,jwks_url=ISS+'/.well-known/jwks.json',
                              authorized_parties=[AZP],client=client)

def test_valid_session_token_with_extra_clerk_claims(keypair):
    private, client=keypair
    claims=verify(mint(private),client)
    assert claims.sub=='user_test1234' and claims.sid=='sess_test1234'

@pytest.mark.parametrize('overrides',[
    {'iss':'https://evil.example'}, {'azp':'https://evil.example'},
    {'exp':1}, {'nbf':9999999999}, {'sid':'invalid'}, {'sub':'not-clerk'},
])
def test_invalid_tokens_fail_closed(keypair, overrides):
    private,client=keypair
    with pytest.raises(TokenRejected):verify(mint(private,**overrides),client)

def test_wrong_signing_key(keypair):
    private,client=keypair
    attacker=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    with pytest.raises(TokenRejected):verify(mint(attacker),client)

def test_no_verification_without_config(keypair):
    private,client=keypair
    with pytest.raises(TokenRejected):
        verify_clerk_token(mint(private),issuer='',jwks_url='',authorized_parties=[],client=client)

def test_roles():
    assert has_role(Role.EDITOR, Role.EDITOR) and has_role(Role.EDITOR, Role.READER)
    assert not has_role(Role.READER, Role.EDITOR) and not has_role(None, Role.EDITOR)

@pytest.mark.parametrize('data', [{'sort':'name'},{'page_size':51},{'page':0},{'industry':'Invalid!'},{'extra':1}])
def test_invalid_query(data):
    with pytest.raises(ValidationError):BrandListQuery.model_validate(data)

def test_patch_extra_forbidden():
    with pytest.raises(ValidationError):BrandPatch.model_validate({'short_description':'x','role':'editor'})

def test_wp_validation():
    base={'source_id':1,'name':'Acme','slug':'acme','published_at':datetime.now(timezone.utc)}
    assert WPBrand(**base,website_url='https://example.com').website_url.startswith('https://')
    with pytest.raises(ValidationError):WPBrand(**base,website_url='javascript:alert(1)')
