# Процесс Трекер (Flet)

Асинхронное веб-приложение на **Flet** с серверной частью на **FastAPI** и БД на **SQLAlchemy 2 (async)**.
Проект поддерживает:
- ✅ Flet веб-клиент (SPA-навигация)
- ✅ FastAPI HTTP-роуты (`/api/*`) и WebSocket (`/ws/*`)
- ✅ Асинхронную БД (SQLAlchemy 2 + aiosqlite по умолчанию)
- ✅ Шифрование (bcrypt для паролей, Fernet для секретов)
- ✅ Логирование через structlog
- ✅ Конфигурацию через `.env` (pydantic-settings)

> Цель — отслеживание задач/процессов с live-обновлениями между клиентом и сервером.

---

## Стек
- **UI:** Flet
- **API:** FastAPI + Uvicorn
- **DB:** SQLAlchemy 2 Async + aiosqlite (можно заменить на Postgres/MySQL)
- **Config:** pydantic-settings (`.env`)
- **Crypto:** passlib[bcrypt], cryptography (Fernet)
- **Logs:** structlog (JSON)

---