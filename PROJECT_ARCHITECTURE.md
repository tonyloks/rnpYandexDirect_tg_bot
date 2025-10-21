
# Архитектура проекта: telegram-yandex-direct-bot (single-tenant, allowlist)

## 0. Резюме

**Цель:** открытый репозиторий Telegram‑бота, который каждый пользователь разворачивает у себя форком и Docker Compose (например, TimeWeb Cloud). Бот подключается к аккаунтам Яндекс.Директа, по запросу показывает бюджеты и статистику, а также отправляет ежедневное уведомление «стата+бюджеты за сегодня».

**Режим эксплуатации:** *single‑tenant* — каждая инсталляция обслуживает владельца и небольшой список допущенных пользователей. Доступ управляется владельцем через allowlist.

---

## 1. Требования и границы

* **Простота развёртывания:** форк → указать репозиторий в провайдере → заполнить ENV → `docker compose up`.
* **Обновления:** git pull форка + redeploy; миграции БД выполняются автоматически при старте.
* **Интеграция с Яндекс.Директ:** использовать предоставленный модуль (адаптер), минимум — методы `getBudgets`, `getStats`.
* **Функции:**
  * Управление несколькими аккаунтами Я.Директа на одного Telegram‑пользователя.
  * Статистика+бюджеты в одном сообщении для периодов: сегодня / вчера / последняя неделя (выбор периода только внутри потока «Получить статистику»).
  * «Только бюджеты» без выбора периода.
  * Расписание: одна задача — «ежедневно: стата+бюджеты за сегодня».
  * Агрегирование по аккаунтам + итоговая сводка.
* **Single‑tenant упрощения:**
  * Нет per‑user/per‑account rate‑лимитов и антифлуда. Оставляем лишь таймауты и мягкие ретраи к Я.Директ.
  * Доступ только владельцу и allowlist.

---

## 2. Технологический стек

* **Язык:** Python 3.12
* **Telegram:** `aiogram 3.x` (FSM, роутеры, middlewares)
* **Web/Health:** `FastAPI` (эндпоинт `/healthz` и, при необходимости, OAuth‑callback)
* **БД:** PostgreSQL 15; ORM: `SQLAlchemy 2.x` (async) + `alembic`
* **Кэш (опционально):** таблицы БД для короткого кэша; Redis не обязателен
* **Планировщик:** `APScheduler` (внутри процесса)
* **Логи:** `structlog`/`loguru` в JSON
* **Криптография:** `cryptography` (AES‑GCM/Fernet) для шифрования токенов

---

## 3. Конфигурация и ENV

`.env.example` (минимум):

```
TELEGRAM_BOT_TOKEN=123456:ABC...
DATABASE_URL=postgresql+asyncpg://bot:bot@db:5432/bot
APP_TIMEZONE=Europe/Moscow
LOG_LEVEL=INFO
APP_KMS_KEY=base64:...

# Доступ
OWNER_TG_ID=123456789
ALLOWED_TG_IDS=111111111,222222222   # опционально
ACCESS_MODE=allowlist               # owner-only | allowlist
ALLOW_GROUP_CHATS=false             # запрет на групповые чаты по умолчанию

# (если требуется OAuth к Я.Директ)
YANDEX_CLIENT_ID=
YANDEX_CLIENT_SECRET=
YANDEX_REDIRECT_URL=
```

**Поведение:**

* `owner-only` — бот доступен только владельцу.
* `allowlist` — владелец + перечисленные в ENV + добавленные через `/allow`.

---

## 4. Дерево проекта

```
telegram-yandex-direct-bot/
├─ app/
│  ├─ main.py                 # entrypoint: инициализация DI, миграции, dp.run_polling
│  ├─ config.py               # чтение ENV, pydantic Settings
│  ├─ bot/
│  │  ├─ router.py            # корневой Router, регистрация саб-роутеров и middleware
│  │  ├─ middlewares.py       # AccessMiddleware, logging
│  │  ├─ keyboards.py         # кнопки и разметка
│  │  ├─ handlers/
│  │  │  ├─ start.py          # /start, /help, /privacy
│  │  │  ├─ connect.py        # /connect — мастер подключения аккаунта Я.Директ
│  │  │  ├─ accounts.py       # /accounts — список/отвязка
│  │  │  ├─ stats.py          # /stats — выбор периода → ответ (стата+бюджеты)
│  │  │  ├─ budgets.py        # /budgets — только бюджеты
│  │  │  ├─ schedule.py       # /schedule — включить/выключить ежедневную рассылку
│  │  │  └─ allow.py          # /allow — list/add/del (только владелец)
│  │  └─ formatting.py        # форматирование строк и итогов
│  ├─ domain/
│  │  ├─ periods.py           # расчёт today/yesterday/last_week в TZ
│  │  ├─ models.py            # DTO pydantic: AccountsDTO/StatsDTO/BudgetsDTO
│  │  └─ services.py          # сценарии: connect/get_stats/get_budgets/schedule
│  ├─ infra/
│  │  ├─ db.py                # engine/session, alembic upgrade
│  │  ├─ repos.py             # репозитории (accounts, schedules, access, cache)
│  │  ├─ crypto.py            # шифрование/дешифрование токенов
│  │  ├─ yd_adapter.py        # адаптер к модулю Я.Директ, ретраи/таймауты
│  │  ├─ cache.py             # БД-кэш (опционально)
│  │  └─ health.py            # FastAPI /healthz
│  ├─ sched/
│  │  └─ scheduler.py         # APScheduler: загрузка джоб из БД, запуск
│  └─ api/health.py           # монтирование FastAPI
├─ migrations/                # alembic
├─ tests/                     # unit/integration
├─ Dockerfile
├─ docker-compose.yml
├─ .env.example
└─ README.md
```

---

## 5. База данных и модели

### Таблицы

* **users** — создаётся на первый вход владельца (или любого допущенного):
  * `tg_user_id bigint PK`, `locale text default 'ru'`, `created_at timestamptz`.
* **yd_accounts** — аккаунты Я.Директа пользователя:
  * `id uuid PK`, `tg_user_id bigint FK users`, `login text not null`, `account_id text null`,
  * `goals_csv text not null`, `goals_json jsonb not null default '[]'`,
  * `token_ciphertext bytea not null`, `token_nonce bytea not null`,
  * `is_active bool default true`, `created_at`, `updated_at`, `last_ok_at`.
  * Уникальность: `(tg_user_id, login, coalesce(account_id,''))`.
* **schedules** — одна ежедневная рассылка на пользователя:
  * `id uuid PK`, `tg_user_id bigint FK`, `kind text` (= `daily_today_stats`),
  * `tz text`, `hour int`, `minute int`, `enabled bool` default true,
  * уникальный ключ `(tg_user_id, kind)`.
* **cache_budgets**  *(опционально)* :
  * `account_ref uuid FK`, `data jsonb`, `valid_until timestamptz`, PK `(account_ref)`.
* **cache_stats**  *(опционально)* :
  * `account_ref uuid FK`, `period_key text`, `data jsonb`, `valid_until timestamptz`, PK `(account_ref, period_key)`.
* **allowed_users** — allowlist управляемый из бота:
  * `tg_user_id bigint PK`, `username text`, `added_by bigint not null`, `created_at timestamptz`.

### DDL (эскиз)

```sql
create table if not exists users(
  tg_user_id bigint primary key,
  locale text not null default 'ru',
  created_at timestamptz not null default now()
);

create table if not exists yd_accounts(
  id uuid primary key,
  tg_user_id bigint not null references users(tg_user_id) on delete cascade,
  login text not null,
  account_id text,
  goals_csv text not null,
  goals_json jsonb not null default '[]'::jsonb,
  token_ciphertext bytea not null,
  token_nonce bytea not null,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  last_ok_at timestamptz
);
create unique index if not exists ux_acc on yd_accounts(tg_user_id, login, coalesce(account_id,''));

create table if not exists schedules(
  id uuid primary key,
  tg_user_id bigint not null references users(tg_user_id) on delete cascade,
  kind text not null,
  tz text not null,
  hour int not null,
  minute int not null,
  enabled boolean not null default true,
  created_at timestamptz not null default now()
);
create unique index if not exists ux_sched on schedules(tg_user_id, kind);

create table if not exists allowed_users(
  tg_user_id bigint primary key,
  username text,
  added_by bigint not null,
  created_at timestamptz not null default now()
);

-- опциональные кэши
create table if not exists cache_budgets(
  account_ref uuid not null references yd_accounts(id) on delete cascade,
  data jsonb not null,
  valid_until timestamptz not null,
  primary key(account_ref)
);
create index if not exists ix_cb_valid on cache_budgets(valid_until);

create table if not exists cache_stats(
  account_ref uuid not null references yd_accounts(id) on delete cascade,
  period_key text not null,
  data jsonb not null,
  valid_until timestamptz not null,
  primary key(account_ref, period_key)
);
create index if not exists ix_cs_valid on cache_stats(valid_until);
```

---

## 6. Периоды и таймзона

* Все расчёты периодов ведутся в `APP_TIMEZONE` (по умолчанию `Europe/Moscow`).
* Периоды:
  * **today** : `[сегодня 00:00; сейчас)`
  * **yesterday** : `[вчера 00:00; сегодня 00:00)`
  * **last_week** : `[сейчас − 7 дней; сейчас)`
* При обращении к Я.Директ передаём явные границы (UTC timestamps + TZ или локальные, в зависимости от клиента).

---

## 7. Доступ и безопасность

* **Access modes:**
  * `owner-only` — доступ только `OWNER_TG_ID`.
  * `allowlist` — доступ владельцу + списку: `ALLOWED_TG_IDS` из ENV и/или занесённым через `/allow`.
* **Middleware:** проверяет тип чата (по умолчанию только `private`), режим доступа и allowlist.
* **Команда владельца `/allow`:** `list`, `add <id|@username>`, `del <id|@username>`.
* **Секреты:** только в ENV/секрет‑хранилище провайдера. Токены Я.Директ шифруются в БД (AES‑GCM/Fernet, ключ `APP_KMS_KEY`).
* **Логи:** без персональных и секретных данных.

---

## 8. Потоки и UX

### Главное меню

Кнопки: «Получить статистику», «Только бюджеты», «Настроить уведомление».

Отдельной кнопки выбора периода в главном меню  **нет** .

### `/connect` (мастер)

1. логин → 2) токен → 3) цели (CSV) → 4) account_id (опц.) → проверка быстрым вызовом → сохранение.

### `/stats`

1. Выбор периода: Сегодня / Вчера / Последняя неделя.
2. Запросы к API: для **всех активных аккаунтов** пользователя — `getStats(period, goals)` + `getBudgets()`.
3. Ответ одним сообщением: строки по аккаунтам + итог (суммы/средние).

### `/budgets`

Без выбора периода. Запрос `getBudgets()` по аккаунтам, один ответ с суммой бюджетов.

### `/schedule`

Одна задача `daily_today_stats`. Разрешить: включить (с временем, дефолт 09:00), отключить, показать статус.

### Формат сообщений (пример)

```
Сводка за СЕГОДНЯ (Europe/Moscow)
--------------------------------------------
login_1 (acc: 123) | Клики: 245 | Конв.: 12 | CTR: 3.1% | CPA: 420 ₽ | Расход: 5 040 ₽ | Бюджет: 20 000 ₽
login_2 (acc: —)   | Клики: 110 | Конв.: 5  | CTR: 2.8% | CPA: 390 ₽ | Расход: 1 950 ₽ | Бюджет: 10 000 ₽
--------------------------------------------
ИТОГО: Клики 355 | Конв. 17 | Ср. CPA 407 ₽ | Расход 6 990 ₽ | Бюджеты суммой: 30 000 ₽
```

---

## 9. Сценарии (сервисный слой)

### Получение статистики (эскиз)

1. Разрешить пользователя (middleware).
2. Определить период (границы в TZ).
3. Получить активные аккаунты.
4. Для каждого аккаунта запросить budgets и stats (параллельно), с таймаутами и мягкими ретраями.
5. Сформировать строки по аккаунтам и общий итог.
6. Отправить одно сообщение.

### Только бюджеты

Аналогично п.4–6, но без `getStats`.

### Подключение аккаунта

* Валидировать ввод. При сохранении токен шифровать.
* Сделать тестовый вызов (например, `getBudgets`) и зафиксировать `last_ok_at`.

### Расписание

* При включении создать/обновить запись в `schedules`.
* На старте процесса планировщик регистрирует все `enabled` задачи.
* В момент срабатывания: выполняется сценарий «Получение статистики» с периодом `today`.

---

## 10. Интеграция с Яндекс.Директ

**Адаптер** поверх предоставленного клиента (условный интерфейс):

```python
class YDAdapter:
    def __init__(self, raw, request_timeout=15, max_retries=2):
        ...
    async def get_budgets(self, acc) -> BudgetsDTO: ...
    async def get_stats(self, acc, period, goals: list[str]) -> StatsDTO: ...
```

* Таймауты: ~10–15s.
* Ретраи: 2 попытки на 429/5xx (+ backoff 0.5→1.5s, джиттер).
* Кэш (опционально): budgets 60–120s; stats 1–5 мин (особенно для yesterday/last_week).

---

## 11. Исключения и UX ошибок

Единый обработчик:

* Нет подключённых аккаунтов.
* Неверный токен/недостаточно прав.
* Лимит/недоступность API (попробовать позже).
* Частичные ошибки по отдельным аккаунтам не блокируют общую сводку: строка помечается ⚠️ и пропускается из итогов.

---

## 12. Логирование и наблюдаемость

* Уровни: DEBUG/INFO/WARN/ERROR через `LOG_LEVEL`.
* Структурированный JSON (timestamp, action, user_id, login/account_id, duration, outcome).
* Эндпоинт `/healthz` (FastAPI) для healthcheck контейнера.

---

## 13. Тестирование

* **Unit:** расчёт периодов (TZ!), форматирование сводок, CSV целей, крипто‑утилиты.
* **Интеграционные (mock Я.Директ):** успешные/ошибочные ответы, ретраи, кэш; потоки `/stats`, `/budgets`, `/schedule`.
* **Контейнерные:** compose‑поднятие, миграции на старте, healthcheck.

---

## 14. Docker/Compose

### Dockerfile (эскиз)

```dockerfile
# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN adduser --disabled-password --gecos "" app \
 && apt-get update && apt-get install -y curl \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml poetry.lock* /app/
RUN pip install --upgrade pip && pip install poetry \
 && poetry config virtualenvs.create false \
 && poetry install --only main
COPY . /app
USER app
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD curl -fsS http://127.0.0.1:8080/healthz || exit 1
CMD ["python", "-m", "app.main"]
```

### docker-compose.yml (без Redis/worker)

```yaml
version: "3.9"
services:
  db:
    image: postgres:15
    restart: unless-stopped
    environment:
      POSTGRES_DB: bot
      POSTGRES_USER: bot
      POSTGRES_PASSWORD: bot
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U bot -d bot"]
      interval: 10s
      timeout: 3s
      retries: 10

  bot:
    build: .
    depends_on:
      db:
        condition: service_healthy
    env_file: .env
    restart: unless-stopped
    # для long polling порты не требуются; раскомментируйте при необходимости healthz наружу
    # ports: ["8080:8080"]

volumes:
  pgdata:
```

---

## 15. Порядок запуска

1. Форк репозитория.
2. В TimeWeb Cloud указать форк как источник деплоя.
3. Заполнить `.env` (минимум: `TELEGRAM_BOT_TOKEN`, `DATABASE_URL`, `OWNER_TG_ID`).
4. Запустить `docker compose up -d`. Контейнер `bot` выполнит `alembic upgrade head` и начнёт long polling.

---

## 16. Обновления

* Версионирование образа — SemVer (при публикации в реестр).
* Обновление: `git pull` форка → redeploy; миграции выполняются автоматически на старте.

---

## 17. Критерии приёмки

* Форк → TimeWeb → ENV → запуск без правок кода.
* `/stats`: одно сообщение (стата+бюджеты) для выбранного периода.
* `/budgets`: одно сообщение без выбора периода.
* `/schedule`: ежедневно присылает «стата+бюджеты за сегодня».
* Доступ: `owner-only` или `allowlist`; команда `/allow` работает у владельца.

---

## 18. Эскизы реализаций (фрагменты)

### AccessMiddleware (упрощённо)

```python
class AccessMiddleware(BaseMiddleware):
    def __init__(self, owner_id:int, mode:str, allowed_env:set[int], repo):
        self.owner_id = owner_id; self.mode = mode
        self.allowed_env = allowed_env; self.repo = repo

    async def __call__(self, handler, event, data):
        m = event if isinstance(event, Message) else event.message
        if not data['config'].allow_group_chats and m.chat.type != 'private':
            return await m.answer('Бот доступен только в приватном чате.')
        uid = m.from_user.id
        if uid == self.owner_id: return await handler(event, data)
        if self.mode == 'owner-only':
            return await m.answer('Доступ ограничен владельцем.')
        allowed = uid in self.allowed_env or await self.repo.access.is_allowed(uid)
        if not allowed:
            return await m.answer('Доступ по приглашению. Обратитесь к владельцу бота.')
        return await handler(event, data)
```

### Периоды (TZ‑безопасно)

```python
def period_today(tz):
    now = datetime.now(tz)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, now

def period_yesterday(tz):
    start_today, _ = period_today(tz)
    start = start_today - timedelta(days=1)
    return start, start_today

def period_last_week(tz):
    now = datetime.now(tz)
    start = now - timedelta(days=7)
    return start, now
```

### Сценарий «/stats» (коротко)

```python
start, end = resolve_period(choice, tz)
accounts = await repo.accounts.for_user(tg_id)
rows = []
for acc in accounts:
    b = await yd.get_budgets(acc)
    s = await yd.get_stats(acc, (start, end), acc.goals)
    rows.append(format_row(acc, s, b))
msg = compose_summary(rows, tz, period_label)
await bot.send_message(chat_id=tg_id, text=msg, parse_mode='HTML')
```

### Расписание (APScheduler)

```python
# при старте: поднять джобы из schedules и зарегистрировать
if sched.enabled:
    scheduler.add_job(send_daily_today_stats, 'cron', hour=sched.hour, minute=sched.minute,
                      timezone=sched.tz, args=[tg_user_id])
```

---

## 19. Возможные расширения (после MVP)

* Отдельный `worker` и Redis для высокой нагрузки.
* Вебхуки Telegram вместо long polling.
* Детализация периодов (предустановки «пн-вс», месяцы, произвольные даты).
* Экспорт сводок в CSV/Google Sheets.
* Многоязычность и гибкая локализация форматов.
