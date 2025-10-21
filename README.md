# Telegram Yandex.Direct Bot

[![CI](https://github.com/tonyloks/rnpYandexDirect_tg_bot/actions/workflows/ci.yml/badge.svg)](https://github.com/tonyloks/rnpYandexDirect_tg_bot/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Single-tenant Telegram bot for monitoring Yandex.Direct statistics and budgets. Designed for self-hosting with a simple fork-and-deploy workflow.

> **Status**: Phase 1 Foundation - Active Development 🚧

## Features

- 📊 **Statistics & Budgets**: Get comprehensive stats and budgets for all your Yandex.Direct accounts in one message
- 📅 **Period Selection**: Today / Yesterday / Last 7 days
- 🔔 **Daily Notifications**: Schedule automatic daily stats delivery
- 🔐 **Secure**: Token encryption with AES-GCM, allowlist-based access control
- 🚀 **Easy Deployment**: Fork → Configure ENV → Deploy with Docker Compose
- 🔄 **Multi-Account Support**: Manage multiple Yandex.Direct accounts per user
- 🌍 **Timezone Aware**: All calculations respect your configured timezone

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- PostgreSQL 15+ (included in docker-compose.yml)

### Deployment

1. **Fork this repository**

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/rnpYandexDirect_tg_bot.git
   cd rnpYandexDirect_tg_bot
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set at minimum:
   - `TELEGRAM_BOT_TOKEN` - Your bot token from @BotFather
   - `OWNER_TG_ID` - Your Telegram user ID (get from [@userinfobot](https://t.me/userinfobot))
   - `APP_KMS_KEY` - Generate with:
     ```bash
     python -c "import base64, os; print('base64:' + base64.b64encode(os.urandom(32)).decode())"
     ```

4. **Launch with Docker Compose**
   ```bash
   docker compose up -d
   ```

5. **Check health**
   ```bash
   curl http://localhost:8080/healthz
   ```

6. **Start using the bot** - Send `/start` to your bot in Telegram

## Bot Commands

- `/start` - Welcome message and main menu
- `/help` - Show available commands
- `/connect` - Connect a new Yandex.Direct account
- `/accounts` - Manage connected accounts
- `/stats` - Get statistics (with period selection)
- `/budgets` - Get current budgets for all accounts
- `/schedule` - Configure daily notifications
- `/allow` - Manage allowlist (owner only)
- `/privacy` - Privacy policy

## Usage Example

### Connecting an Account

1. Send `/connect` to the bot
2. Enter your Yandex.Direct login
3. Provide your API token
4. Specify conversion goals (comma-separated IDs)
5. Optionally provide account ID for multi-account logins
6. Bot will verify the connection and save it

### Getting Statistics

1. Click "Получить статистику" or send `/stats`
2. Select period: Today / Yesterday / Last 7 days
3. Receive a consolidated report with:
   - Clicks, conversions, CTR, CPA
   - Spend and budgets
   - Per-account breakdown
   - Total aggregated metrics

Example output:
```
Сводка за СЕГОДНЯ (Europe/Moscow)
--------------------------------------------
login_1 (acc: 123) | Клики: 245 | Конв.: 12 | CTR: 3.1% | CPA: 420 ₽ | Расход: 5 040 ₽ | Бюджет: 20 000 ₽
login_2 (acc: —)   | Клики: 110 | Конв.: 5  | CTR: 2.8% | CPA: 390 ₽ | Расход: 1 950 ₽ | Бюджет: 10 000 ₽
--------------------------------------------
ИТОГО: Клики 355 | Конв. 17 | Ср. CPA 407 ₽ | Расход 6 990 ₽ | Бюджеты суммой: 30 000 ₽
```

## Configuration

See `.env.example` for all available configuration options.

### Key Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | **Required** |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://bot:bot@db:5432/bot` |
| `APP_TIMEZONE` | Timezone for date calculations | `Europe/Moscow` |
| `OWNER_TG_ID` | Owner's Telegram user ID | **Required** |
| `ACCESS_MODE` | Access control mode | `allowlist` |
| `APP_KMS_KEY` | Encryption key for tokens | **Required** |

### Access Modes

- **owner-only**: Only the owner can use the bot
- **allowlist**: Owner + users in `ALLOWED_TG_IDS` + users added via `/allow`

## Architecture

The project follows a clean architecture pattern:

```
app/
├── bot/          # Telegram bot layer (handlers, keyboards, middlewares)
├── domain/       # Business logic (periods, DTOs, services)
├── infra/        # Infrastructure (database, Yandex.Direct adapter, crypto)
├── sched/        # APScheduler integration
├── api/          # FastAPI endpoints (healthcheck)
└── main.py       # Application entry point
```

See [PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) for detailed architecture documentation.

## Development

### Local Setup

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Set up pre-commit hooks:
   ```bash
   poetry run pre-commit install
   ```

3. Run linters:
   ```bash
   poetry run pre-commit run --all-files
   ```

4. Run tests:
   ```bash
   poetry run pytest
   ```

### Database Migrations

Migrations are applied automatically on container start. For manual control:

```bash
# Create a new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1
```

## Deployment to TimeWeb Cloud

1. Create a new app in TimeWeb Cloud
2. Connect your forked repository
3. Configure environment variables in TimeWeb dashboard
4. Deploy

The bot will automatically:
- Run database migrations
- Start in long polling mode
- Register scheduled jobs

## Security

- ✅ Tokens are encrypted in the database using AES-GCM
- ✅ Access control via owner ID and allowlist
- ✅ No secrets in logs
- ✅ Environment-based configuration
- ✅ Group chats disabled by default

## Limitations

This is a **single-tenant** bot designed for personal or small team use:
- No per-user rate limiting (relies on Yandex.Direct API limits)
- No distributed deployment support
- SQLite not supported (use PostgreSQL)

## Updates

To update your deployment:

```bash
git pull
docker compose down
docker compose up -d --build
```

Migrations will be applied automatically on startup.

## Troubleshooting

### Bot doesn't respond
- Check that `TELEGRAM_BOT_TOKEN` is correct
- Verify your user ID in `OWNER_TG_ID`
- Check logs: `docker compose logs bot`

### Database connection errors
- Ensure PostgreSQL is healthy: `docker compose ps`
- Check `DATABASE_URL` format

### API errors
- Verify Yandex.Direct token is valid
- Check account permissions
- Review retry/timeout settings

## Contributing

This is a personal project, but suggestions and bug reports are welcome via GitHub Issues.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Roadmap

See [PLAN.md](PLAN.md) for the detailed development roadmap.

Current phase: **Phase 1 - Foundation** ✅

## Support

For questions or issues:
- Open a [GitHub Issue](https://github.com/tonyloks/rnpYandexDirect_tg_bot/issues)
- Check [PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) for technical details

---

**Note**: This bot is designed for single-tenant use. Each user should deploy their own instance.
