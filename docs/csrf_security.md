"""
# CSRF Security Documentation

## Overview

This document explains the Cross-Site Request Forgery (CSRF) protection implementation in the Travel Planning Platform application.

## What is CSRF?

CSRF (Cross-Site Request Forgery) is a type of security vulnerability where an attacker tricks a user's browser into making unwanted requests to a website where the user is already authenticated. This can lead to unauthorized actions being performed on behalf of the authenticated user.

## Protection Implementation

The Travel Planning Platform implements CSRF protection using Flask-WTF's CSRFProtect extension. This protection mechanism works by:

1. Generating a unique token for each user session
2. Including this token in all forms as a hidden field
3. Validating the token on form submission
4. Rejecting requests that don't include a valid token

## Configuration

CSRF protection is configured in two main files:

### 1. app/__init__.py

CSRF protection is enabled application-wide with:

```python
app.config['WTF_CSRF_ENABLED'] = True
```

### 2. app/csrf_config.py

This file contains the detailed configuration for CSRF protection:

```python
app.config['WTF_CSRF_CHECK_DEFAULT'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour token expiration
```

It also defines routes that are exempt from CSRF protection:

```python
app.config['WTF_CSRF_EXEMPT_LIST'] = ['/statistics/set-home-location', '/statistics/validate-address']
```

## Implementation in Templates

All forms in the application include a CSRF token with the following HTML:

```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

This ensures that POST requests to the server include the necessary CSRF token.

## AJAX Requests

For AJAX requests that use POST, PUT, or DELETE methods, the CSRF token is included in the request headers. This is handled by JavaScript in the main.js file, which automatically adds the token to all fetch() and XMLHttpRequest calls.

## Troubleshooting

If you encounter "Bad Request - The CSRF token is missing" errors:

1. Ensure the form includes the CSRF token field
2. For AJAX requests, make sure the request headers include 'X-CSRFToken'
3. Check that the session hasn't expired (tokens expire after 1 hour by default)
4. Verify that the route isn't accidentally in the exempt list
"""