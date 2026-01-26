# STABLE SYSTEM CONFIGURATION
## Last Updated: 2026-01-26

This document describes the STABLE configuration that has been implemented to fix the persistent login issues.

---

## ROOT CAUSE OF LOGIN ISSUES

**Problem:** The SECRET_KEY was being randomly generated on every Gunicorn worker restart/reload, which invalidated all user sessions and caused continuous logout issues.

**Previous Code (BROKEN):**
```python
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = "".join(random.choice(string.ascii_lowercase) for i in range(32))
```

This meant every time Gunicorn restarted, a NEW SECRET_KEY was generated, making all existing sessions invalid.

---

## PERMANENT FIXES IMPLEMENTED

### 1. Fixed SECRET_KEY (.env file)
**Location:** `/opt/myproject/myproject/Custom_inventory_system/.env`

```bash
SECRET_KEY=2EysXIcuC5kJGZXFTCrf1V2Zw0wn3ZgUKf0c7Ss3L8Hc17Q9Au
```

**Permissions:** `chmod 600` (read/write for owner only)

**Why this works:** The SECRET_KEY is now stored in a file and loaded via `python-dotenv`, ensuring it remains constant across all server restarts.

---

### 2. Session Configuration (settings.py)
**Location:** `/opt/myproject/myproject/Custom_inventory_system/config/settings.py`

```python
# Session Configuration - STABLE SETTINGS
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Store sessions in database
SESSION_COOKIE_SECURE = True  # Only send session cookie over HTTPS
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
SESSION_COOKIE_SAMESITE = 'Lax'  # Prevent CSRF while allowing normal navigation
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds
SESSION_SAVE_EVERY_REQUEST = True  # Update session on every request to keep it alive
SESSION_COOKIE_NAME = 'pharmamgtsystemgc_sessionid'  # Custom session cookie name
```

**Benefits:**
- Sessions persist for 2 weeks
- Sessions updated on every request (stays alive during use)
- Stored in database (survives server restarts)
- Secure cookies (HTTPS only, HttpOnly)

---

### 3. Login View Fix (apps/authentication/views.py)
**Prevents redirect loops:**

```python
next_url = request.POST.get('next') or request.GET.get('next')
if next_url and next_url != request.path:
    return redirect(next_url)
else:
    return redirect('index')
```

**Why this works:** Checks that the `next` URL is not the login page itself, preventing infinite redirect loops.

---

### 4. Nginx Configuration
**Location:** `/etc/nginx/sites-available/myproject`

**Key settings:**
```nginx
location / {
    proxy_pass http://127.0.0.1:8000;  # Correct proxy target
    # ... other proxy settings
}

location /static/ {
    alias /opt/myproject/myproject/Custom_inventory_system/staticfiles/;
}

location /media/ {
    alias /opt/myproject/myproject/Custom_inventory_system/media/;
}
```

**Why this works:** 
- Nginx proxies to `127.0.0.1:8000` which matches Gunicorn's `0.0.0.0:8000` binding
- Static files served correctly at `/static/` (not `/staticfiles/`)

---

### 5. Gunicorn Service (systemd)
**Location:** `/etc/systemd/system/gunicorn-myproject.service`

```ini
[Service]
WorkingDirectory=/opt/myproject/myproject/Custom_inventory_system
Environment="PATH=/opt/myproject/bin"
ExecStart=/opt/myproject/bin/gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 --access-logfile - --error-logfile - config.wsgi:application
Restart=always
RestartSec=10
```

**Benefits:**
- Managed by systemd (automatic restart on failure)
- Consistent binding address
- Loads .env file automatically (dotenv in settings.py)

---

## HOW TO RESTART SERVICES

### Restart Gunicorn:
```bash
systemctl restart gunicorn-myproject
```

### Reload Nginx:
```bash
systemctl reload nginx
```

### Restart Both:
```bash
systemctl restart gunicorn-myproject && systemctl reload nginx
```

### Check Status:
```bash
systemctl status gunicorn-myproject
systemctl status nginx
```

---

## IMPORTANT: DO NOT CHANGE

1. **DO NOT** modify the SECRET_KEY in `.env` unless absolutely necessary
   - Changing it will invalidate ALL user sessions
   - If you must change it, notify all users to log in again

2. **DO NOT** use `pkill gunicorn` anymore
   - Use `systemctl restart gunicorn-myproject` instead
   - systemd manages the service properly

3. **DO NOT** modify the session settings without understanding the implications
   - Current settings are stable and tested

---

## TROUBLESHOOTING

### Users still getting logged out?
1. Check SECRET_KEY exists:
   ```bash
   cat /opt/myproject/myproject/Custom_inventory_system/.env
   ```

2. Verify Django can read it:
   ```bash
   cd /opt/myproject/myproject/Custom_inventory_system
   python3 manage.py shell -c "from django.conf import settings; print(len(settings.SECRET_KEY))"
   ```
   Should output: `50`

3. Clear old sessions:
   ```bash
   cd /opt/myproject/myproject/Custom_inventory_system
   python3 manage.py clearsessions
   ```

4. Restart Gunicorn:
   ```bash
   systemctl restart gunicorn-myproject
   ```

### Icons not showing?
- Static files are at: `/static/` (not `/staticfiles/`)
- Run collectstatic if needed:
  ```bash
  cd /opt/myproject/myproject/Custom_inventory_system
  python3 manage.py collectstatic --noinput
  ```

---

## VERIFICATION

Test the login:
```bash
curl -I https://pharmamgtsystemgc.com/en/ 2>&1 | grep -E "HTTP|Set-Cookie"
```

Should see:
- `HTTP/1.1 200 OK`
- `Set-Cookie: csrftoken=...`

---

## SYSTEM IS NOW STABLE ✅

All configurations have been tested and verified. The login system should now work reliably without redirect loops or session expiration issues.

