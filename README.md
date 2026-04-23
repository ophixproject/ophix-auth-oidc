# ophix-auth-oidc

OpenID Connect / Azure AD SSO authentication plugin for [ophix-server-base](https://github.com/ophixproject/ophix-server-base).

Activated automatically when `OIDC_RP_CLIENT_ID` is set in `.env`. Provides
`OphixOIDCBackend` with group claim merging, user auto-provisioning, and
staff/superuser mapping from group membership.

---

## Installation

```bash
pip install ophix-auth-oidc
```

---

## Configuration (`.env`)

| Variable | Default | Purpose |
| --- | --- | --- |
| `OIDC_RP_CLIENT_ID` | — | OAuth2 client ID — setting this activates the plugin |
| `OIDC_RP_CLIENT_SECRET` | — | OAuth2 client secret |
| `OIDC_RP_SIGN_ALGO` | `RS256` | Token signing algorithm |
| `OIDC_OP_AUTHORIZATION_ENDPOINT` | — | Provider authorisation endpoint URL |
| `OIDC_OP_TOKEN_ENDPOINT` | — | Provider token endpoint URL |
| `OIDC_OP_USER_ENDPOINT` | — | Provider userinfo endpoint URL |
| `OIDC_OP_JWKS_ENDPOINT` | — | Provider JWKS endpoint URL |
| `OIDC_AZURE_TENANT_ID` | — | Azure AD tenant ID — sets all four endpoint URLs automatically |
| `OIDC_STAFF_GROUP_ID` | — | Group claim value that grants `is_staff=True` |
| `OIDC_SUPERUSER_GROUP_ID` | — | Group claim value that grants `is_superuser=True` |

### Azure AD shortcut

Set only `OIDC_AZURE_TENANT_ID` and all four endpoint URLs are derived automatically
from the Microsoft identity platform — no need to configure them individually.

---

## Notes

- OIDC and LDAP (`ophix-auth-ldap`) can be active simultaneously — OIDC handles the
  SSO redirect flow, LDAP handles the admin username/password form.
- Falls back gracefully if `mozilla-django-oidc` is not installed — a warning is logged
  and the plugin has no effect.
