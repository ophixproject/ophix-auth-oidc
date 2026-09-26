"""
Unit tests for OphixOIDCBackend's own custom logic.

Deliberately does NOT test mozilla-django-oidc's own protocol handling
(redirect/callback/token exchange/signature verification) - that's a mature,
separately-tested library. These tests target only the code Ophix actually
wrote: the Azure AD ID-token claims merge, the group-to-permission mapping,
and the email-based user lookup/creation.

get_userinfo() makes a real HTTP call in the parent class
(OIDCAuthenticationBackend.get_userinfo uses requests.get against
OIDC_OP_USER_ENDPOINT) - mocked out here rather than hit over the network.
"""
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from ophix_auth_oidc.backend import OphixOIDCBackend


# ---------------------------------------------------------------------------
# get_userinfo - Azure AD ID-token claims merge
# ---------------------------------------------------------------------------

@patch("mozilla_django_oidc.auth.OIDCAuthenticationBackend.get_userinfo")
def test_get_userinfo_merges_groups_from_id_token_payload(mock_super):
    mock_super.return_value = {"email": "alice@example.com"}
    backend = OphixOIDCBackend()

    result = backend.get_userinfo(
        "access-token", "id-token", {"groups": ["group-a", "group-b"]}
    )

    assert result["groups"] == ["group-a", "group-b"]
    assert result["email"] == "alice@example.com"


@patch("mozilla_django_oidc.auth.OIDCAuthenticationBackend.get_userinfo")
def test_get_userinfo_merges_roles_from_id_token_payload(mock_super):
    mock_super.return_value = {"email": "alice@example.com"}
    backend = OphixOIDCBackend()

    result = backend.get_userinfo("access-token", "id-token", {"roles": ["admin"]})

    assert result["roles"] == ["admin"]


@patch("mozilla_django_oidc.auth.OIDCAuthenticationBackend.get_userinfo")
def test_get_userinfo_does_not_override_existing_userinfo_groups(mock_super):
    # If the userinfo endpoint itself already returned groups, the ID token
    # payload must not silently overwrite it.
    mock_super.return_value = {"email": "alice@example.com", "groups": ["from-userinfo"]}
    backend = OphixOIDCBackend()

    result = backend.get_userinfo("access-token", "id-token", {"groups": ["from-id-token"]})

    assert result["groups"] == ["from-userinfo"]


@patch("mozilla_django_oidc.auth.OIDCAuthenticationBackend.get_userinfo")
def test_get_userinfo_handles_missing_payload(mock_super):
    mock_super.return_value = {"email": "alice@example.com"}
    backend = OphixOIDCBackend()

    result = backend.get_userinfo("access-token", "id-token", None)

    assert result == {"email": "alice@example.com"}


@patch("mozilla_django_oidc.auth.OIDCAuthenticationBackend.get_userinfo")
def test_get_userinfo_handles_non_dict_payload(mock_super):
    # A JWT payload should always decode to a dict, but don't crash if some
    # provider ever sends something unexpected.
    mock_super.return_value = {"email": "alice@example.com"}
    backend = OphixOIDCBackend()

    result = backend.get_userinfo("access-token", "id-token", "not-a-dict")

    assert result == {"email": "alice@example.com"}


# ---------------------------------------------------------------------------
# get_username / filter_users_by_claims
# ---------------------------------------------------------------------------

def test_get_username_prefers_email():
    backend = OphixOIDCBackend()
    assert backend.get_username({"email": "alice@example.com"}) == "alice@example.com"


def test_get_username_falls_back_to_preferred_username():
    backend = OphixOIDCBackend()
    assert backend.get_username({"preferred_username": "alice@example.com"}) == "alice@example.com"


def test_get_username_truncates_to_150_chars():
    long_email = "a" * 200 + "@example.com"
    backend = OphixOIDCBackend()
    assert len(backend.get_username({"email": long_email})) == 150


@pytest.mark.django_db
def test_filter_users_by_claims_matches_by_email_case_insensitive():
    User = get_user_model()
    User.objects.create_user("existing", email="Alice@Example.com")
    backend = OphixOIDCBackend()

    result = backend.filter_users_by_claims({"email": "alice@example.com"})

    assert list(result) == [User.objects.get(username="existing")]


@pytest.mark.django_db
def test_filter_users_by_claims_returns_none_without_email():
    backend = OphixOIDCBackend()
    result = backend.filter_users_by_claims({})
    assert list(result) == []


# ---------------------------------------------------------------------------
# _apply_group_permissions - the 4 real branches
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@override_settings(OIDC_STAFF_GROUP_ID="staff-group", OIDC_SUPERUSER_GROUP_ID="super-group")
def test_superuser_group_match_grants_staff_and_superuser():
    User = get_user_model()
    user = User.objects.create_user("alice")
    backend = OphixOIDCBackend()

    backend._apply_group_permissions(user, {"groups": ["super-group"]})

    assert user.is_staff is True
    assert user.is_superuser is True


@pytest.mark.django_db
@override_settings(OIDC_STAFF_GROUP_ID="staff-group", OIDC_SUPERUSER_GROUP_ID="super-group")
def test_staff_group_match_grants_staff_only():
    User = get_user_model()
    user = User.objects.create_user("alice")
    backend = OphixOIDCBackend()

    backend._apply_group_permissions(user, {"groups": ["staff-group"]})

    assert user.is_staff is True
    assert user.is_superuser is False


@pytest.mark.django_db
@override_settings(OIDC_STAFF_GROUP_ID="", OIDC_SUPERUSER_GROUP_ID="")
def test_no_groups_configured_grants_staff_to_everyone():
    User = get_user_model()
    user = User.objects.create_user("alice")
    backend = OphixOIDCBackend()

    backend._apply_group_permissions(user, {"groups": []})

    assert user.is_staff is True


@pytest.mark.django_db
@override_settings(OIDC_STAFF_GROUP_ID="staff-group", OIDC_SUPERUSER_GROUP_ID="super-group")
def test_groups_configured_but_user_in_neither_denies_access():
    User = get_user_model()
    user = User.objects.create_user("alice", is_staff=True, is_superuser=True)
    backend = OphixOIDCBackend()

    backend._apply_group_permissions(user, {"groups": ["some-other-group"]})

    assert user.is_staff is False
    assert user.is_superuser is False


@pytest.mark.django_db
@override_settings(OIDC_STAFF_GROUP_ID="staff-group", OIDC_SUPERUSER_GROUP_ID="super-group")
def test_groups_claim_as_bare_string_is_handled():
    # Some providers send a single group as a bare string rather than a
    # single-item list - must not crash on `in` against a string doing
    # substring matching instead of membership.
    User = get_user_model()
    user = User.objects.create_user("alice")
    backend = OphixOIDCBackend()

    backend._apply_group_permissions(user, {"groups": "staff-group"})

    assert user.is_staff is True
    assert user.is_superuser is False


# ---------------------------------------------------------------------------
# create_user / update_user - integration of the pieces above
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@override_settings(OIDC_STAFF_GROUP_ID="", OIDC_SUPERUSER_GROUP_ID="")
def test_create_user_applies_group_permissions():
    backend = OphixOIDCBackend()

    user = backend.create_user({"email": "alice@example.com", "groups": []})

    assert user.email == "alice@example.com"
    assert user.is_staff is True


@pytest.mark.django_db
@override_settings(OIDC_STAFF_GROUP_ID="staff-group", OIDC_SUPERUSER_GROUP_ID="")
def test_update_user_re_evaluates_group_permissions_on_every_login():
    User = get_user_model()
    user = User.objects.create_user("alice", email="alice@example.com", is_staff=True)
    backend = OphixOIDCBackend()

    # Group membership revoked since last login - update_user must reflect it.
    backend.update_user(user, {"email": "alice@example.com", "groups": []})

    user.refresh_from_db()
    assert user.is_staff is False
