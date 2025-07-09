
# 🌐 Cloudflare + EC2 + Nginx Setup Guide with Troubleshooting

This guide summarizes how to configure Cloudflare with an EC2 instance running Nginx, based on actual deployment experience — including all issues that were resolved step by step.

---

## ✅ Overview

You will:

- Use **Cloudflare** to manage DNS, proxy and HTTPS
- Use **Nginx** on EC2 to serve a React frontend and proxy to FastAPI backend
- Fix common issues: Cloudflare 521, Nginx config conflicts, file permissions, etc.

---

## 🧾 Step-by-Step Setup

### 1️⃣ Buy/Connect a Domain on Cloudflare

1. Go to [https://dash.cloudflare.com](https://dash.cloudflare.com)
2. Add or buy a domain (e.g. `rookiealgo.com`)
3. Cloudflare provides nameservers (e.g. `emma.ns.cloudflare.com`)
4. Update nameservers in your domain registrar if needed (skip if purchased from Cloudflare)

---

### 2️⃣ Configure Cloudflare DNS

In **DNS → Records**:

| Type | Name | Value         | Proxy Status |
|------|------|---------------|--------------|
| A    | @    | EC2 public IP | Proxied (orange cloud) |
| A    | www  | EC2 public IP | Proxied                |

---

### 3️⃣ Set SSL/TLS Settings

Go to **SSL/TLS → Overview**, set mode to:

```
Full ✅
```

> Don’t use “Strict” unless EC2 has valid TLS cert

---

## 🛠️ EC2 + Nginx Configuration

### 4️⃣ Install Nginx on Ubuntu EC2

```bash
sudo apt update
sudo apt install nginx -y
```

---

### 5️⃣ Configure Nginx

Create or update `/etc/nginx/sites-available/api-only`:

```nginx
server {
    listen 80;
    server_name rookiealgo.com www.rookiealgo.com;

    root /home/ubuntu/react-app;
    index index.html;

    location / {
        try_files $uri /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable and reload:

```bash
sudo ln -sf /etc/nginx/sites-available/api-only /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

---

## ❗Common Problems + Solutions

### ❌ `Error 521` (Cloudflare can't reach origin)

- ✅ Fixed by ensuring EC2 Security Group allows **port 80** (HTTP)
- ✅ Nginx was not running or not listening on `0.0.0.0:80`
- ✅ Nginx config conflicted with default → `conflicting server_name` warning

### ❌ `curl http://localhost` → Connection Refused

- 🔍 Nginx config not loaded or no file in `sites-enabled/`
- ✅ Fixed by symlinking correct config + `sudo nginx -t` + reload

### ❌ `Permission denied` for `/home/ubuntu/react-app/index.html`

- 🔥 Nginx runs as `www-data` user, but can’t access user folder
- ✅ Fixed with:

```bash
sudo chmod +x /home/ubuntu
sudo chown -R www-data:www-data /home/ubuntu/react-app
sudo chmod -R 755 /home/ubuntu/react-app
```

### ❌ `rewrite or internal redirection cycle`

- 🔁 Caused by missing `index.html` or lack of read permission
- ✅ Fixed by correcting permissions

### ❌ `nslookup` does not return correct IP

- 🕐 DNS not yet propagated
- ✅ Wait 1–10 minutes or flush local DNS

---

## ✅ Final Test Checklist

- ✅ `curl http://localhost/` → returns `index.html`
- ✅ `curl http://localhost/api/hello` → returns FastAPI response
- ✅ `https://rookiealgo.com/` shows frontend in browser
- ✅ No more 521 errors from Cloudflare

---

## 🎉 You're Done!

You now have:

- Cloudflare-protected domain
- HTTPS via proxy
- Nginx serving React + proxying FastAPI
- Fully functional fullstack deployment on EC2
