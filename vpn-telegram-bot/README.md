# Telegram VPN Bot + YooKassa SBP

## Стек

- Python 3.11+
- aiogram 3.x
- SQLite
- python-dotenv
- httpx
- FastAPI + Uvicorn
- YooKassa API

## Быстрый старт

1. Создайте виртуальное окружение и установите зависимости:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r requirements.txt`
2. Создайте `.env` на основе `.env.example`.
3. Запустите Telegram-бот:
   - `python bot.py`
4. Запустите webhook сервер (в отдельном терминале):
   - `uvicorn web.webhook:app --host 0.0.0.0 --port 8000`

## Структура

- `bot.py` — точка входа
- `handlers/` — пользовательские и админские обработчики
- `services/db.py` — SQLite слой
- `services/yookassa_service.py` — создание/проверка платежей YooKassa
- `services/subscription_service.py` — активация подписки и отправка конфига
- `services/vpn_service.py` — генерация VLESS ссылок
- `web/webhook.py` — FastAPI webhook endpoint
- `config.py` — загрузка настроек

## Команды

- `/start` — открыть главное меню
- `/admin` — админ-панель

## Поток оплаты

1. Пользователь выбирает тариф в боте.
2. Бот создает платеж в YooKassa с методом `sbp`, метаданными `user_id` и `plan`.
3. Пользователь оплачивает по кнопке `Оплатить через СБП`.
4. YooKassa отправляет webhook на `/webhook/yookassa`.
5. Сервер повторно верифицирует платеж через API YooKassa.
6. При `succeeded` подписка активируется автоматически, конфиг отправляется пользователю.
