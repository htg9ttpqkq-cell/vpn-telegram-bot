"""UI texts for VPN bot.

Russian is the default language. English is provided for the optional toggle.
"""

texts = {
    "ru": {
        "home_title": "⚡ VPN Панель управления",
        "status_label": "Статус",
        "status_active": "🟢 Защищён",
        "status_inactive": "🔴 Не активен",
        "btn_install": "📲 Установить VPN",
        "btn_profile": "👤 Профиль",
        "btn_invite": "🎁 Пригласить друга",
        "btn_tariffs": "💳 Тарифы",
        "btn_faq": "❓ Вопросы",
        "btn_switch_en": "🌐 English",
        "btn_switch_ru": "🌐 Русский",
        "btn_menu": "☰ Меню",
        "btn_back": "🔙 Назад",
        "install_title": "📲 Установка VPN\n\nВыберите приложение:",
        "btn_get_config": "📥 Получить конфиг",
        "config_title": "📲 Конфиг",
        "profile_title": "👤 Профиль",
        "profile_status": "Статус",
        "profile_plan": "Тариф",
        "profile_expiry": "Истекает",
        "profile_active": "Активен",
        "profile_inactive": "Не активен",
        "btn_renew": "🔄 Продлить",
        "btn_usage": "📊 Статистика",
        "usage_stub": "📊 Статистика\n\nСкоро.",
        "invite_title": "🎁 Реферальная система",
        "invite_reward": "Бонус: +3 дня за приглашение",
        "faq_title": "❓ Часто задаваемые вопросы",
        "faq_body": "Как подключиться? Откройте Установить VPN.\nОплата: ручная проверка.",
        "btn_support": "🆘 Поддержка",
        "support_title": "🆘 Поддержка",
        "choose_plan": "💳 Выберите план:",
        "checkout": "💳 Безопасная оплата",
        "duration": "Срок",
        "price": "Цена",
        "secure_sbp": "🔐 Безопасная оплата через СБП",
        "btn_pay": "💳 Оплатить",
        "payment_pending": "⏳ Платёж получен\n\nОжидает проверки.",
        "not_active": "🔴 Не активен\n\nКупите тариф для подключения.",
        "activation_intro": (
            "⚡ Доступ открыт\n\n"
            "⚡ Скорость: высокая\n"
            "🔐 Статус: активен"
        ),
        "btn_setup_guide": "📖 Инструкция по установке",
        "install_steps": (
            "1. Установите приложение\n"
            "2. Откройте ссылку или отсканируйте QR\n"
            "3. Нажмите «Подключить»"
        ),
        "invite_link_label": "Ваша ссылка:",
        "unknown_plan": "Неизвестный тариф",
        "trial_granted_notice": (
            "🎁 Вам начислен тестовый период 7 дней. "
            "Откройте «Установить VPN» или «Профиль», чтобы получить конфиг."
        ),
    },
    "en": {
        "home_title": "⚡ VPN Control Panel",
        "status_label": "Status",
        "status_active": "🟢 Protected",
        "status_inactive": "🔴 Not active",
        "btn_install": "📲 Install VPN",
        "btn_profile": "👤 Profile",
        "btn_invite": "🎁 Invite Friend",
        "btn_tariffs": "💳 Tariffs",
        "btn_faq": "❓ FAQ",
        "btn_switch_en": "🌐 Switch to English",
        "btn_switch_ru": "🌐 Switch to Russian",
        "btn_menu": "☰ Menu",
        "btn_back": "🔙 Back",
        "install_title": "📲 Install VPN\n\nChoose your app:",
        "btn_get_config": "📥 Get Config",
        "config_title": "📲 Config",
        "profile_title": "👤 Profile",
        "profile_status": "Status",
        "profile_plan": "Plan",
        "profile_expiry": "Expiry",
        "profile_active": "Active",
        "profile_inactive": "Not active",
        "btn_renew": "🔄 Renew",
        "btn_usage": "📊 Usage",
        "usage_stub": "📊 Usage\n\nSoon.",
        "invite_title": "🎁 Referral system",
        "invite_reward": "Reward: +3 days per invite",
        "faq_title": "❓ Frequently Asked Questions",
        "faq_body": "How to connect? Open Install VPN.\nPayment check: manual review.",
        "btn_support": "🆘 Support",
        "support_title": "🆘 Support",
        "choose_plan": "💳 Choose plan:",
        "checkout": "💳 Secure Checkout",
        "duration": "Duration",
        "price": "Price",
        "secure_sbp": "🔐 Secure payment via SBP",
        "btn_pay": "💳 Pay",
        "payment_pending": "⏳ Payment received\n\nAwaiting secure review.",
        "not_active": "🔴 Not active\n\nUnlock a plan to connect.",
        "activation_intro": (
            "⚡ Access granted\n\n"
            "⚡ Speed: high\n"
            "🔐 Status: active"
        ),
        "btn_setup_guide": "📖 Setup guide",
        "install_steps": (
            "1. Install the app\n"
            "2. Open the link or scan the QR code\n"
            "3. Tap Connect"
        ),
        "invite_link_label": "Your link:",
        "unknown_plan": "Unknown plan",
        "trial_granted_notice": (
            "🎁 Your 7-day trial is active. "
            "Open Install VPN or Profile to get your config."
        ),
    },
}

# Подписи периода для кнопок тарифов, профиля и уведомлений (RU/EN).
_plan_period_labels = {
    "ru": {
        "trial": "Тест 7 дней",
        "1m": "1 месяц",
        "3m": "3 месяца",
        "12m": "12 месяцев",
    },
    "en": {
        "trial": "7-day trial",
        "1m": "1 month",
        "3m": "3 months",
        "12m": "12 months",
    },
}

plan_titles = _plan_period_labels
plan_durations = _plan_period_labels
