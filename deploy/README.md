# Deploying to a VPS (Biznet Gio NEO)

Stack: Caddy (automatic HTTPS) → FastAPI app (serves API + frontend) → Postgres, all in Docker Compose.
Chroma data lives in the `chroma_data` volume, Postgres in `pg_data`.

## 1. Create the server

- Biznet Gio NEO: Ubuntu 24.04 (or 22.04), **2 vCPU / 4 GB RAM** recommended (1 GB is too tight
  for Chroma + PyMuPDF + Postgres). Add your SSH public key at creation.
- In the NEO security group / firewall, allow inbound **22, 80, 443** only.

## 2. Point the domain

Create a DNS `A` record for your (sub)domain → the server's public IPv4. Verify:

```bash
dig +short rag.example.com
```

## 3. Harden and install Docker (on the server)

```bash
ssh root@SERVER_IP
adduser deploy && usermod -aG sudo deploy
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy      # copy your SSH key
# Log in as deploy from now on; then disable root/password SSH:
sudo sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/; s/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

sudo ufw allow OpenSSH && sudo ufw allow 80,443/tcp && sudo ufw enable
sudo apt-get update && sudo apt-get -y upgrade
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker deploy    # re-login for this to take effect
```

Test the second SSH session as `deploy` before closing the root one.

## 4. Get the code and configure

```bash
git clone -b staging https://github.com/Jasman123/multi-doc-rag.git && cd multi-doc-rag
cp deploy/.env.example deploy/.env
nano deploy/.env        # fill DOMAIN, POSTGRES_PASSWORD, SECRET_KEY, ENCRYPTION_KEY
chmod 600 deploy/.env
```

Generate values with the commands in `.env.example`. Store `ENCRYPTION_KEY` in a password manager too.

## 5. Start

```bash
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env up -d --build
docker compose -f deploy/docker-compose.prod.yml logs -f    # Ctrl-C to leave
```

Order: Postgres healthy → `migrate` runs `alembic upgrade head` → `app` starts → Caddy issues the certificate.
Then open `https://your-domain/health` (expect `{"status":"ok"}`) and `/login.html`.

## 6. First admin

Register an account in the UI, then promote it:

```bash
docker compose -f deploy/docker-compose.prod.yml exec postgres \
  psql -U postgres -d multi_doc_rag_auth -c "UPDATE users SET role = 'admin' WHERE email = 'you@example.com';"
```

The table (`users`) and role value (`admin`) match `backend/app/models/user.py`. Then log in and add provider keys at `/admin.html`.
Registration is open to anyone, and anyone who registers can query your documents using your provider keys. Consider restricting it before going public.

## 7. Update / redeploy

```bash
git pull
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env up -d --build
```

## 8. Backups (do this before storing real documents)

```bash
mkdir -p ~/backups
# Postgres (users + encrypted provider keys)
docker compose -f deploy/docker-compose.prod.yml exec -T postgres \
  pg_dump -U postgres multi_doc_rag_auth | gzip > ~/backups/pg-$(date +%F).sql.gz
# Chroma vector store (stop the app briefly for a consistent copy)
docker compose -f deploy/docker-compose.prod.yml stop app
docker run --rm -v multi-doc-rag_chroma_data:/data -v ~/backups:/out alpine \
  tar czf /out/chroma-$(date +%F).tgz -C /data .
docker compose -f deploy/docker-compose.prod.yml start app
```

The volume name prefix is the compose project name (the repo folder name by default) — check with `docker volume ls`.
Copy backups **off the server** (another machine or object storage); also enable Biznet Gio snapshots if offered.
Automate with cron once the commands work by hand.

## Notes

- Only Caddy exposes ports; Postgres is not reachable from the internet.
- The app currently allows CORS `*` (`backend/app/main.py`); tighten to your domain.
- Provider API keys are entered in `/admin.html`. Document text and queries are sent to whichever
  external LLM/embedding provider you configure — hosting in Jakarta does not change that.
