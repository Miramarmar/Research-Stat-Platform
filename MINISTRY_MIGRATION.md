# Ministry Hosting Migration Guide
## ResearchStat Platform — SILAB, University of Manouba

---

## Step 0 — Before You Start: Ask the Ministry IT Team

Send this exact list to ministry IT and wait for answers before proceeding:

```
1. Operating system and version? (target: Ubuntu 20.04 or 22.04)
2. Do we have sudo/root access, or managed access only?
3. Is outbound internet access allowed from the server? (needed for pip install)
4. Which ports are open? (need at minimum: 80, 443, and one app port)
5. Is an existing web server running? (Apache or Nginx already installed?)
6. Is PostgreSQL available, or do we provision our own?
7. Is there a domain/subdomain for us? (e.g., stats.manouba.tn)
8. Are SSL certificates managed by the ministry, or do we install our own?
9. Is Docker allowed on the server?
10. What is the backup policy?
```

---

## Path A — Docker Allowed (Recommended)

```bash
# 1. SSH into the server
ssh yourname@ministry-server-ip

# 2. Install Docker (if not already present)
sudo apt update && sudo apt install docker.io docker-compose -y

# 3. Clone your project
git clone https://github.com/yourusername/research-app.git
cd research-app

# 4. Create environment file (never commit this)
cp backend/.env.example .env
nano .env
# Fill in: ANTHROPIC_API_KEY, SECRET_KEY, and database credentials

# 5. Add ministry SSL certificates
mkdir certs
cp /path/to/ministry-cert.crt certs/cert.crt
cp /path/to/ministry-key.key  certs/key.key

# 6. Update nginx.conf — replace "your-ministry-domain.tn" with your real domain

# 7. Launch
docker-compose up -d

# 8. Verify
docker-compose ps          # all should show "Up"
curl http://localhost/health
```

---

## Path B — No Docker (Manual Setup)

### Install system dependencies
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip nodejs npm nginx postgresql -y
```

### Set up PostgreSQL
```bash
sudo -u postgres psql
CREATE DATABASE researchapp;
CREATE USER appuser WITH PASSWORD 'strong-password-here';
GRANT ALL PRIVILEGES ON DATABASE researchapp TO appuser;
\q
```

### Deploy backend
```bash
cd /var/www/research-app/backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create env file
cp .env.example .env
nano .env   # fill in all values
```

### Create systemd service (auto-start on reboot)
```bash
sudo nano /etc/systemd/system/researchapp.service
```
Paste:
```ini
[Unit]
Description=ResearchStat Backend
After=network.target postgresql.service

[Service]
User=www-data
WorkingDirectory=/var/www/research-app/backend
Environment="PATH=/var/www/research-app/backend/venv/bin"
EnvironmentFile=/var/www/research-app/backend/.env
ExecStart=/var/www/research-app/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload
sudo systemctl enable researchapp
sudo systemctl start researchapp
sudo systemctl status researchapp   # should show "active (running)"
```

### Build and deploy frontend
```bash
cd /var/www/research-app/frontend
npm install
REACT_APP_API_URL=https://your-ministry-domain.tn npm run build
```

### Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/researchapp
```
Paste:
```nginx
server {
    listen 80;
    server_name your-ministry-domain.tn;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name your-ministry-domain.tn;

    ssl_certificate /etc/ssl/certs/ministry-cert.crt;
    ssl_certificate_key /etc/ssl/private/ministry-key.key;

    root /var/www/research-app/frontend/build;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 50M;
    }
}
```
```bash
sudo ln -s /etc/nginx/sites-available/researchapp /etc/nginx/sites-enabled/
sudo nginx -t        # must say "ok"
sudo systemctl restart nginx
```

---

## AI Layer on Ministry Servers

The ministry server may block outbound calls to api.anthropic.com.

**Option A — Request firewall exception:**
Ask IT to whitelist `api.anthropic.com` on port 443 only.

**Option B — Local Ollama (no external calls, full privacy):**
```bash
# Requires ≥ 8GB RAM on the server
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.2

# In .env, set:
USE_LOCAL_AI=true
OLLAMA_URL=http://localhost:11434
```

---

## Supabase → PostgreSQL Migration

When moving from Supabase to the ministry's PostgreSQL:

1. Export Supabase data:
   `Settings → Database → Backups → Download`

2. Import to ministry PostgreSQL:
   `psql -U appuser -d researchapp < supabase_backup.sql`

3. Replace Supabase client in `analytics/tracker.py` with `asyncpg` or `psycopg2`
   (only ~20 lines need changing — all in the tracker file)

---

## Post-Migration Checklist

```
□ SSH access confirmed
□ Python 3.12+ installed (python3 --version)
□ Node.js 18+ installed (node --version)
□ PostgreSQL running (systemctl status postgresql)
□ Database and user created
□ .env file populated with all secrets
□ Backend service running (systemctl status researchapp)
□ Frontend built successfully (no build errors)
□ Nginx configured and running
□ SSL certificates in place
□ HTTPS redirect working (http:// → https://)
□ Health check responds: GET /health returns {"status":"ok"}
□ File upload works (test with small CSV)
□ A t-test runs and returns APA output
□ Admin dashboard loads (verify no research data visible)
□ AI toggle works or shows "unavailable" gracefully
□ PDF/Word export downloads correctly
□ No-Save Mode session clears on tab close
```
