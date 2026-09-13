# Minedesso Infrastructure

Docker Compose setup for the Minedesso Minecraft server network.

## Architecture

```
Internet
│
├─ minedesso.dev              → Angular Frontend
├─ api.minedesso.dev          → Spring Backend API 1
├─ islewars-api.minedesso.dev → Spring Backend API 2 (IsleWars)
├─ auth.minedesso.dev         → Keycloak (OAuth2/OIDC)
├─ traefik.minedesso.dev      → Traefik Dashboard (BasicAuth)
│
└─ play.minedesso.dev:25565   → Velocity → Lobby → Citybuild / IsleWars
```

## Prerequisites

- Docker >= 24.0
- Docker Compose >= 2.20
- DNS records pointing to your VPS:
  - `minedesso.dev`
  - `api.minedesso.dev`
  - `islewars-api.minedesso.dev`
  - `auth.minedesso.dev`
  - `traefik.minedesso.dev`
  - `play.minedesso.dev`

## Setup

### 1. Clone

```bash
git clone https://github.com/Minedesso/minedesso-infra.git
cd minedesso-infra
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env` and set real values for all `changeme` entries.

### 3. Generate Secrets

```bash
# Traefik Dashboard BasicAuth password
# Install apache2-utils first: apt install apache2-utils
htpasswd -nbB admin <your-password> > secrets/dashboard-htpasswd

# Velocity Forwarding Secret
openssl rand -hex 32 > velocity/forwarding.secret
```

### 4. Deploy

```bash
chmod +x scripts/*.sh
./scripts/deploy.sh
```

### 5. Keycloak Setup (first time only)

1. Open `https://auth.minedesso.dev`
2. Login with `admin` / your `KEYCLOAK_ADMIN_PASSWORD`
3. Create realm `minedesso`
4. Create clients for `backend-api` and `islewars-api`
5. Configure JWT settings and roles

## Directory Structure

```
minedesso-infra/
├── compose.yml
├── .env.example
├── .gitignore
├── traefik/
│   ├── traefik.yml
│   └── dynamic/
│       └── middlewares.yml
├── velocity/
│   ├── velocity.toml
│   └── forwarding.secret
├── nginx/
│   └── default.conf
├── secrets/
│   └── dashboard-htpasswd
├── docker/
│   ├── lobby/
│   │   ├── Dockerfile
│   │   └── plugins/
│   ├── citybuild/
│   │   ├── Dockerfile
│   │   └── plugins/
│   └── islewars/
│       ├── Dockerfile
│       └── plugins/
└── scripts/
    ├── deploy.sh
    ├── backup.sh
    └── init-databases.sh
```

## Networks

| Network | Purpose |
|---|---|
| `proxy-net` | Traefik ↔ HTTP services |
| `backend-net` | APIs ↔ PostgreSQL ↔ Minecraft servers |
| `minecraft-net` | Velocity ↔ Minecraft servers |

## Services

| Service | Image | Networks | Healthcheck |
|---|---|---|---|
| traefik | traefik:v3.3 | proxy-net | ping |
| angular | ghcr.io/minedesso/frontend | proxy-net | HTTP 80 |
| backend-api | ghcr.io/minedesso/backend-api | proxy-net, backend-net | HTTP 8080 |
| islewars-api | ghcr.io/minedesso/islewars-api | proxy-net, backend-net | HTTP 8081 |
| postgres | postgres:17-alpine | backend-net | pg_isready |
| keycloak | keycloak:26.4 | proxy-net | HTTP health |
| velocity | papermc/velocity:3.3 | minecraft-net | - |
| lobby | ghcr.io/minedesso/lobby | backend-net, minecraft-net | mc-monitor |
| citybuild | ghcr.io/minedesso/citybuild | backend-net, minecraft-net | mc-monitor |
| islewars | ghcr.io/minedesso/islewars | backend-net, minecraft-net | mc-monitor |

## Deployment

```bash
./scripts/deploy.sh
```

## Backup

```bash
./scripts/backup.sh
```

Backups are stored in `/opt/minedesso/backups` by default. Override with `BACKUP_DIR`.

## Minecraft Server Plugins

| Server | Plugins |
|---|---|
| Lobby | lobby-plugin, ban-plugin |
| Citybuild | essential-plugin, ban-plugin |
| IsleWars | islewars-plugin, ban-plugin |

## Security

- Only ports 80, 443, 25565 exposed to the internet
- All internal communication via Docker service names
- Secrets stored in `.env` (not committed) and Docker secrets
- Traefik dashboard protected by BasicAuth
- Velocity Modern Forwarding with shared secret
