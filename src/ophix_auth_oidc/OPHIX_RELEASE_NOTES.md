# Ophix Auth Oidc Release Notes

## 2026.09.26.03

- Verified real compatibility under Python 3.14 (not just added the classifier) as part of the taskserver-release-wave compatibility sweep, and added `Programming Language :: Python :: 3.14` to the package classifiers.

## 2026.09.26.02

- Added a real unit test suite (`tests/test_backend.py`, 17 tests, all pass)
  covering every custom code path in `OphixOIDCBackend`: the Azure AD
  ID-token claims merge (including malformed/missing payload and not
  clobbering existing userinfo), all four group-to-permission mapping
  branches, the bare-string-vs-list groups claim edge case, email-based user
  lookup, and the create/update integration. Deliberately does not re-test
  mozilla-django-oidc's own protocol handling (redirect/callback/token
  exchange) - that's a mature, separately-tested library; these tests target
  only the code Ophix actually wrote. Install test deps with
  `pip install -e .[test] --no-deps` (no ophix-server-base needed - the
  backend only imports Django and mozilla-django-oidc directly) and run
  with `pytest`.

## 2026.09.26.01

- Development Status dropped from Beta to Alpha — no test-harness evidence
  exists for this package yet (checked: no test files, no mock-IdP
  references anywhere in the repo). Beta implied more confidence than
  actually exists; corrected pending real testing.

## 2026.04.27.01

- Added `OPHIX_RELEASE_NOTES.md` for release notes delivery.
