from django.urls import path
from identities.views import introspect

urlpatterns = [path("api/tokens/introspect/", introspect, name="introspect")]
