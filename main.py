import random
import os
import threading
import time
from flask import Flask
import telebot

# 1. Запуск фонового веб-сервера для Render
app = Flask('')

@app.route('/')
def home():
    return "Бот работает стабильно!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Запускаем сервер в отдельном потоке
threading.Thread(target=run_web_server).start()

# 2. Настройка самого Telegram-бота (Токен строго в настройках Render!)
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

USER_DATA = {}

# Грамотно рассчитанная экономика на 10 уровней для ОДНОЙ фермы
FARM_ECONOMY = {
    1: {'cost': 0, 'income': 500},
    2: {'cost': 4000, 'income': 900},
    3: {'cost': 6000, 'income': 1400},
    4: {'cost': 9000, 'income': 2000},
    5: {'cost': 13500, 'income': 3000},
    6: {'cost': 20000, 'income': 4500},
    7: {'cost': 30000, 'income': 6500},
    8: {'cost': 45000, 'income': 9500},
    9: {'cost': 65000, 'income': 14000},
    10: {'cost': 100000, 'income': 22000}
}

@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.from_user.id
    if user_id not in USER_DATA:
        # При старте ставим last_collect на текущее время
        USER_DATA[user_id] = {'balance': 5000, 'has_farm': 0, 'farm_lvl': 1, 'last_collect': time.time(), 'last_bonus': 0}
        
    bot.send_message(
        message.chat.id, 
        f"Привет, {message.from_user.first_name}!\n\n"
        "💰 Тебе начислено: **5000 монет**.\n\n"
        "💵 Доступные команды:\n"
        "👉 `профиль` — посмотреть свою статистику\n"
        "👉 `бонус` — получить ежедневную награду\n"
        "👉 `К [ставка]` (или `казино [ставка]`) — сыграть на монеты\n"
        "👉 `магазин` — купить или улучшить ферму\n"
        "👉 `ферма сбор` — собрать доход с фермы"
    )

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    text = message.text.lower().strip()

    if user_id not in USER_DATA:
        USER_DATA[user_id] = {'balance': 5000, 'has_farm': 0, 'farm_lvl': 1, 'last_collect': time.time(), 'last_bonus': 0}

    # Поддержка старых профилей
    if 'has_farm' not in USER_DATA[user_id]:
        USER_DATA[user_id]['has_farm'] = 0
    if 'farm_lvl' not in USER_DATA[user_id]:
        USER_DATA[user_id]['farm_lvl'] = 1
    if 'last_collect' not in USER_DATA[user_id] or USER_DATA[user_id]['last_collect'] == 0:
        USER_DATA[user_id]['last_collect'] = time.time()
    if 'last_bonus' not in USER_DATA[user_id]:
        USER_DATA[user_id]['last_bonus'] = 0

    # --- КОМАНДА: ПРОФИЛЬ ---
    if text in ["профиль", "/профиль"]:
        balance = USER_DATA[user_id]['balance']
        has_farm = USER_DATA[user_id]['has_farm']
        lvl = USER_DATA[user_id]['farm_lvl']
        current_time = time.time()
        
        if has_farm == 1:
            # Считаем, сколько накопилось прямо сейчас для показа в профиле
            time_passed = current_time - USER_DATA[user_id]['last_collect']
            hours_passed = time_passed / 3600
            if hours_passed > 4:
                hours_passed = 4 # Ограничение в 4 часа
                
            current_income = FARM_ECONOMY[lvl]['income']
            accumulated = int(hours_passed * current_income)
            max_storage = current_income * 4
            
            storage_status = f"📦 Накоплено: **{accumulated}** / **{max_storage}** монет"
            if hours_passed == 4:
                storage_status += " ⚠️ (Склад заполнен!)"
                
            farm_info = f"🚜 **Ферма:** {lvl} уровень\n{storage_status}\n👉 Собрать: `ферма сбор`"
        else:
            farm_info = "🚜 **Ферма:** ❌ Не куплена (купите в `магазин`)"

        # Считаем таймер для бонуса (24 часа)
        bonus_cooldown = 24 * 60 * 60
        last_bonus = USER_DATA[user_id]['last_bonus']
        if current_time - last_bonus < bonus_cooldown:
            rem_b = int(bonus_cooldown - (current_time - last_bonus))
            bonus_status = f"⏳ Будет через {rem_b // 3600} ч. {(rem_b % 3600) // 60} мин."
        else:
            bonus_status = "✅ Доступен (`бонус`)"

        bot.send_message(
            message.chat.id, 
            f"👤 **Профиль игрока:** {message.from_user.first_name}\n"
            f"🆔 **ID:** `{user_id}`\n\n"
            f"💰 **Баланс:** {balance} монет\n"
            f"───────────────────\n"
            f"{farm_info}\n"
            f"───────────────────\n"
            f"🎁 **Ежедневный бонус:** {bonus_status}"
        )

    # --- КОМАНДА: БАЛАНС ---
    elif text in ["баланс", "/баланс", "б"]:
        balance = USER_DATA[user_id]['balance']
        bot.send_message(message.chat.id, f"💳 **Ваш кошелек:**\n💰 Баланс: {balance} монет")

    # --- КОМАНДА: ЕЖЕДНЕВНЫЙ БОНУС ---
    elif text in ["бонус", "/бонус"]:
        current_time = time.time()
        last_bonus = USER_DATA[user_id]['last_bonus']
        cooldown = 24 * 60 * 60
        
        if current_time - last_bonus < cooldown:
            remaining_time = int(cooldown - (current_time - last_bonus))
            hours = remaining_time // 3600
            minutes = (remaining_time % 3600) // 60
            return bot.send_message(
                message.chat.id, 
                f"🎁 **Вы уже забирали бонус!**\nСледующий бонус будет доступен через: **{hours} ч. {minutes} мин.**"
            )
            
        bonus_reward = 2000
        USER_DATA[user_id]['balance'] += bonus_reward
        USER_DATA[user_id]['last_bonus'] = current_time
        
        bot.send_message(
            message.chat.id, 
            f"🎁 **Ежедневный бонус получен!**\n"
            f"💵 Вам начислено: +{bonus_reward} монет.\n"
            f"💰 Новый баланс: {USER_DATA[user_id]['balance']} монет."
        )

    # --- КОМАНДА: МАГАЗИН ---
    elif text in ["магазин", "/магазин"]:
        has_farm = USER_DATA[user_id]['has_farm']
        lvl = USER_DATA[user_id]['farm_lvl']
        
        if has_farm == 0:
            shop_text = "🚜 **Собственная Ферма**\n├ Цена: 3000 монет\n└ Доход: 500 монет/час (вмещает до 4 часов)\n\n👉 Для покупки напишите: `купить ферму`"
        else:
            if lvl < 10:
                next_lvl = lvl + 1
                upgrade_cost = FARM_ECONOMY[next_lvl]['cost']
                next_income = FARM_ECONOMY[next_lvl]['income']
                shop_text = f"🚜 Ваша ферма: **{lvl} уровня**\n\n📈 **Улучшение до {next_lvl} уровня:**\n├ Цена: {upgrade_cost} монет\n└ Новый доход: {next_income} монет/час\n└ Макс. склад (4ч): {next_income * 4} монет\n\n👉 Для улучшения напишите: `прокачать ферму`"
            else:
                shop_text = "🚜 Ваша ферма прокачана до **максимального 10 уровня**! 🎉"

        bot.send_message(message.chat.id, f"🏪 **Магазин фермерства:**\n\n{shop_text}")

    # --- КОМАНДА: КУПИТЬ ФЕРМУ ---
    elif text == "купить ферму":
        if USER_DATA[user_id]['has_farm'] == 1:
            return bot.send_message(message.chat.id, "❌ У вас уже есть ферма!")
            
        if USER_DATA[user_id]['balance'] >= 3000:
            USER_DATA[user_id]['balance'] -= 3000
            USER_DATA[user_id]['has_farm'] = 1
            USER_DATA[user_id]['farm_lvl'] = 1
            USER_DATA[user_id]['last_collect'] = time.time() # Начинаем отсчет дохода
            bot.send_message(
                message.chat.id, 
                f"🎉 Поздравляем! Вы приобрели **Собственную ферму**!\n"
                f"💰 Остаток баланса: {USER_DATA[user_id]['balance']} монет.\n"
                f"👉 Ферма начала копить доход. Собирайте его в любое время командой `ферма сбор`."
            )
        else:
            bot.send_message(message.chat.id, "❌ У вас недостаточно монет! Ферма стоит 3000 монет.")

    # --- КОМАНДА: ПРОКАЧАТЬ ФЕРМУ ---
    elif text == "прокачать ферму":
        if USER_DATA[user_id]['has_farm'] == 0:
            return bot.send_message(message.chat.id, "❌ Сначала купите ферму в `магазин`!")
            
        current_lvl = USER_DATA[user_id]['farm_lvl']
        if current_lvl >= 10:
            return bot.send_message(message.chat.id, "❌ Ваша ферма уже максимального 10 уровня!")
            
        next_lvl = current_lvl + 1
        cost = FARM_ECONOMY[next_lvl]['cost']
        
        if USER_DATA[user_id]['balance'] >= cost:
            # Перед апгрейдом принудительно собираем старый накопившийся доход, чтобы он не сгорел
            current_time = time.time()
            time_passed = current_time - USER_DATA[user_id]['last_collect']
            hours_passed = min(time_passed / 3600, 4.0)
            old_profit = int(hours_passed * FARM_ECONOMY[current_lvl]['income'])
            
            USER_DATA[user_id]['balance'] -= cost
            USER_DATA[user_id]['balance'] += old_profit
            USER_DATA[user_id]['farm_lvl'] = next_lvl
            USER_DATA[user_id]['last_collect'] = current_time # Сбрасываем таймер на новое время
            
            bot.send_message(
                message.chat.id,
                f"⚡ **Уровень фермы повышен до {next_lvl}!** 🎉\n"
                f"📥 Старый доход (+{old_profit} монет) автоматически собран в кошелек.\n"
                f"💵 Новый доход: {FARM_ECONOMY[next_lvl]['income']} монет/час.\n"
                f"💰 Остаток кошелька: {USER_DATA[user_id]['balance']} монет."
            )
        else:
            bot.send_message(message.chat.id, f"❌ Недостаточно монет для улучшения! Стоимость: {cost} монет.")

    # --- КОМАНДА: НАКОПИТЕЛЬНЫЙ СБОР ДОХОДА (МАКСИМУМ ЗА 4 ЧАСА) ---
    elif text == "ферма сбор":
        if USER_DATA[user_id]['has_farm'] == 0:
            return bot.send_message(message.chat.id, "❌ У вас еще нет фермы! Зайдите в `магазин`.")
        
        current_time = time.time()
        last_collect = USER_DATA[user_id]['last_collect']
        
        # Считаем, сколько времени прошло в часах
        time_passed = current_time - last_collect
