"""UI texts for VPN bot — EDELIA | Закрытый клуб.

Бренд-гайдлайн:
  — Никакого технического жаргона («конфиг», «ключ», «токен»).
  — Только статусные символы: 💎 📍 💳 👤 ✨ ✉️ 📅 📱.
  — Запрещены: ⚡ 🔥 🚀 🎁 ❓ 🆘 — заменены на нейтральные.
  — Кнопки: 1–3 слова, без суеты.
"""

texts = {
    "ru": {
        # --- Главный экран ---
        "home_title": "EDELIA | Закрытый VPN-клуб",
        "home_welcome": (
            "Добро пожаловать в <b>EDELIA | Закрытый VPN-клуб</b>.\n\n"
            "Мы обеспечиваем безупречную скорость, абсолютную конфиденциальность "
            "и премиальный уровень стабильности для ваших устройств.\n\n"
            "Воспользуйтесь меню ниже для управления вашим доступом."
        ),
        "status_label": "Статус доступа",
        "status_active": "💎 Доступ активен",
        "status_inactive": "📍 Требует активации",

        # --- Кнопки главного меню ---
        "btn_install": "💎 Подключить VPN",
        "btn_profile": "👤 Профиль",
        "btn_invite": "✨ Реферальный клуб",
        "btn_tariffs": "💳 Оплата доступа",
        "btn_faq": "✉️ Поддержка",
        "btn_switch_en": "🌐 English",
        "btn_switch_ru": "🌐 Русский",
        "btn_docs": "📄 Документы",
        "btn_menu": "☰ Меню",
        "btn_back": "← Назад",

        # --- Раздел «Подключение» ---
        "install_title": (
            "💎 <b>EDELIA | Подключение</b>\n\n"
            "Выберите приложение для настройки вашего доступа:"
        ),
        "btn_get_config": "💎 Получить доступ",
        "config_title": "💎 Ваш персональный доступ",

        # --- Профиль / Личный кабинет ---
        "profile_title": "👤 <b>EDELIA | Ваш персональный профиль</b>",
        "profile_status": "✨ Статус",
        "profile_plan": "📍 Тариф",
        "profile_expiry": "📅 Доступ открыт до",
        "profile_active": "<b>Активен</b>",
        "profile_inactive": "<b>Требует продления</b>",
        "btn_renew": "💳 Продлить доступ",
        "btn_usage": "📊 Детали подписки",

        # --- Реферальный клуб ---
        "invite_title": "✨ <b>EDELIA | Привилегии для своих</b>",
        "invite_reward": (
            "Разделите безупречное качество EDELIA с вашим окружением. "
            "Перешлите вашу персональную ссылку приглашения: за первое пополнение "
            "баланса вашим гостем мы начислим <b>30 дней премиального доступа</b> "
            "на ваш аккаунт."
        ),
        "invite_bonus_received": (
            "✨ Ваш гость активировал доступ EDELIA.\n\n"
            "На ваш аккаунт начислено <b>+30 дней</b> премиального доступа."
        ),
        "invite_link_label": "🔗 Ваша персональная ссылка приглашения:",

        # --- Поддержка ---
        "faq_title": "✉️ <b>EDELIA | Служба заботы</b>",
        "faq_body": (
            "Если у вас возникли вопросы по настройке, смене локации или оплате, "
            "наш консьерж-сервис всегда на связи."
        ),
        "btn_support": "✉️ Консьерж-сервис",
        "support_title": "✉️ <b>EDELIA | Служба заботы</b>",

        # --- Документы ---
        "docs_title": (
            "📄 <b>Документы EDELIA</b>\n\n"
            "Ознакомьтесь с нашими условиями и политикой:"
        ),
        "btn_privacy": "Политика конфиденциальности",
        "btn_terms": "Пользовательское соглашение",

        # --- Оплата ---
        "choose_plan": "💳 <b>EDELIA | Выберите тариф доступа:</b>",
        "checkout": "💳 <b>EDELIA | Оформление доступа</b>",
        "duration": "Период",
        "price": "Стоимость",
        "secure_sbp": "Безопасная оплата через СБП:",
        "btn_pay": "💎 Подтвердить активацию",
        "payment_pending": (
            "💳 <b>Заявка принята.</b>\n\n"
            "Ваш платёж передан на верификацию. "
            "Доступ будет активирован в течение нескольких минут."
        ),
        "not_active": (
            "📍 <b>Доступ не активирован</b>\n\n"
            "Выберите тариф, чтобы открыть премиальный доступ EDELIA."
        ),

        # --- Уведомление об активации ---
        "activation_intro": (
            "💎 <b>EDELIA | Доступ открыт</b>\n\n"
            "Ваша премиальная подписка успешно активирована.\n"
            "✨ Статус: активен"
        ),

        # --- Инструкция ---
        "btn_setup_guide": "📱 Инструкция по подключению",
        "install_steps": (
            "1. Установите приложение\n"
            "2. Нажмите «Получить доступ» и скопируйте вашу ссылку\n"
            "3. Вставьте ссылку в приложение → «Добавить подписку»"
        ),

        # --- Прочее ---
        "unknown_plan": "Тариф не найден",
        "trial_granted_notice": (
            "💎 Вам активирован пробный период — 7 дней премиального доступа. "
            "Нажмите «Подключить VPN», чтобы получить вашу персональную ссылку."
        ),

        # --- Детали подписки (Usage / Statistics) ---
        "stats_title": "📊 <b>EDELIA | Детали подписки</b>",
        "stats_plan": "Тариф",
        "stats_expires": "Доступ до",
        "stats_days_left": "Осталось дней",
        "stats_invited": "Приглашено гостей",
        "stats_bonuses": "Начислено бонусных месяцев",
    },

    "en": {
        # --- Home screen ---
        "home_title": "EDELIA | Private VPN Club",
        "home_welcome": (
            "Welcome to <b>EDELIA | Private VPN Club</b>.\n\n"
            "We deliver flawless speed, absolute privacy, and premium-grade "
            "stability for all your devices.\n\n"
            "Use the menu below to manage your access."
        ),
        "status_label": "Access status",
        "status_active": "💎 Access active",
        "status_inactive": "📍 Requires activation",

        # --- Main menu buttons ---
        "btn_install": "💎 Connect VPN",
        "btn_profile": "👤 Profile",
        "btn_invite": "✨ Referral Club",
        "btn_tariffs": "💳 Access Plans",
        "btn_faq": "✉️ Support",
        "btn_switch_en": "🌐 Switch to English",
        "btn_switch_ru": "🌐 Switch to Russian",
        "btn_docs": "📄 Documents",
        "btn_menu": "☰ Menu",
        "btn_back": "← Back",

        # --- Connection section ---
        "install_title": (
            "💎 <b>EDELIA | Connect</b>\n\n"
            "Choose an application to set up your access:"
        ),
        "btn_get_config": "💎 Get Access",
        "config_title": "💎 Your personal access",

        # --- Profile ---
        "profile_title": "👤 <b>EDELIA | Your Personal Profile</b>",
        "profile_status": "✨ Status",
        "profile_plan": "📍 Plan",
        "profile_expiry": "📅 Access open until",
        "profile_active": "<b>Active</b>",
        "profile_inactive": "<b>Requires renewal</b>",
        "btn_renew": "💳 Renew Access",
        "btn_usage": "📊 Subscription Details",

        # --- Referral club ---
        "invite_title": "✨ <b>EDELIA | Privileges for your circle</b>",
        "invite_reward": (
            "Share EDELIA's flawless quality with your circle. "
            "Forward your personal invitation link: upon your guest's first payment, "
            "we will credit <b>30 days of premium access</b> to your account."
        ),
        "invite_bonus_received": (
            "✨ Your guest has activated EDELIA access.\n\n"
            "Your account has been credited <b>+30 days</b> of premium access."
        ),
        "invite_link_label": "🔗 Your personal invitation link:",

        # --- Support ---
        "faq_title": "✉️ <b>EDELIA | Concierge Service</b>",
        "faq_body": (
            "If you have questions about setup, changing location, or billing, "
            "our concierge service is always available."
        ),
        "btn_support": "✉️ Concierge Service",
        "support_title": "✉️ <b>EDELIA | Concierge Service</b>",

        # --- Documents ---
        "docs_title": (
            "📄 <b>EDELIA Documents</b>\n\n"
            "Please review our terms and policies:"
        ),
        "btn_privacy": "Privacy Policy",
        "btn_terms": "Terms of Service",

        # --- Payment ---
        "choose_plan": "💳 <b>EDELIA | Choose your access plan:</b>",
        "checkout": "💳 <b>EDELIA | Access Checkout</b>",
        "duration": "Period",
        "price": "Price",
        "secure_sbp": "Secure payment via SBP:",
        "btn_pay": "💎 Confirm Activation",
        "payment_pending": (
            "💳 <b>Request received.</b>\n\n"
            "Your payment is being verified. "
            "Access will be activated within a few minutes."
        ),
        "not_active": (
            "📍 <b>Access not activated</b>\n\n"
            "Choose a plan to unlock EDELIA premium access."
        ),

        # --- Activation notification ---
        "activation_intro": (
            "💎 <b>EDELIA | Access Granted</b>\n\n"
            "Your premium subscription has been successfully activated.\n"
            "✨ Status: active"
        ),

        # --- Setup guide ---
        "btn_setup_guide": "📱 Connection guide",
        "install_steps": (
            "1. Install the application\n"
            "2. Tap 'Get Access' and copy your link\n"
            "3. Paste the link into the app → 'Add subscription'"
        ),

        # --- Misc ---
        "unknown_plan": "Plan not found",
        "trial_granted_notice": (
            "💎 Your 7-day premium trial has been activated. "
            "Tap 'Connect VPN' to receive your personal access link."
        ),

        # --- Subscription details ---
        "stats_title": "📊 <b>EDELIA | Subscription Details</b>",
        "stats_plan": "Plan",
        "stats_expires": "Access until",
        "stats_days_left": "Days remaining",
        "stats_invited": "Guests invited",
        "stats_bonuses": "Bonus months credited",
    },
}

# Статусные названия тарифов (Premium-стиль).
_plan_period_labels = {
    "ru": {
        "trial": "Пробный доступ — 7 дней",
        "test": "Тестовый доступ — 1 день (1 ₽)",
        "1m": "Premium Доступ — 1 месяц",
        "3m": "Premium Доступ — 3 месяца",
        "12m": "Premium Доступ — 12 месяцев",
    },
    "en": {
        "trial": "Trial Access — 7 days",
        "test": "Test Access — 1 day (1 RUB)",
        "1m": "Premium Access — 1 month",
        "3m": "Premium Access — 3 months",
        "12m": "Premium Access — 12 months",
    },
}

plan_titles = _plan_period_labels
plan_durations = _plan_period_labels
