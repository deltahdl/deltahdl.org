"""E2E tests for redirect functionality.

Per tenets: If the test sends an HTTP request, it's an e2e test.
"""
import requests


def test_apex_returns_301(apex_domain):
    """Verify apex domain returns 301 Moved Permanently."""
    response = requests.get(
        f"https://{apex_domain}", timeout=30, allow_redirects=False
    )
    assert response.status_code == 301


def test_apex_redirects_to_github(apex_domain, redirect_target):
    """Verify apex domain redirects to GitHub repository."""
    response = requests.get(
        f"https://{apex_domain}", timeout=30, allow_redirects=False
    )
    location = response.headers.get("Location", "")
    assert location == redirect_target


def test_www_returns_301(www_domain):
    """Verify www domain returns 301 Moved Permanently."""
    response = requests.get(
        f"https://{www_domain}", timeout=30, allow_redirects=False
    )
    assert response.status_code == 301


def test_www_redirects_to_github(www_domain, redirect_target):
    """Verify www domain redirects to GitHub repository."""
    response = requests.get(
        f"https://{www_domain}", timeout=30, allow_redirects=False
    )
    location = response.headers.get("Location", "")
    assert location == redirect_target


def test_http_apex_redirects(apex_domain):
    """Verify HTTP apex domain redirects (HTTPS upgrade or redirect)."""
    response = requests.get(
        f"http://{apex_domain}", timeout=30, allow_redirects=False
    )
    assert response.status_code in [301, 302, 307, 308]


def test_http_www_redirects(www_domain):
    """Verify HTTP www domain redirects (HTTPS upgrade or redirect)."""
    response = requests.get(
        f"http://{www_domain}", timeout=30, allow_redirects=False
    )
    assert response.status_code in [301, 302, 307, 308]
