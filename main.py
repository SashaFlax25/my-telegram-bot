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

@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.from_user.id
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {'balance': 5000, 'farms': 0, 'last_collect': 0, 'last_bonus': 0}
        
    bot.send_message(
        message.chat.id, 
        f"Привет, {message.from_user.first_name}!\n\n"
        "💰 Тебе начислено: **5000 монет**.\n\n"
        "💵 Доступные команды:\n"
        "👉 `Б` (или `баланс`) — проверить кошелек\n"
        "👉 `бонус` — получить ежедневную награду\n"
        "👉 `К [ставка]` (или `казино [ставка]`) — сыграть на монеты\n"
        "👉 `магазин` — купить бизнес или ферму\n"
        "👉 `ферма сбор` — собрать доход с ферм"
    )

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    text = message.text.lower().strip()

    if user_id not in USER_DATA:
        USER_DATA[user_id] = {'balance': 5000, 'farms': 0, 'last_collect': 0, 'last_bonus': 0}

    # Проверка ключей для старых профилей
    if 'last_collect' not in USER_DATA[user_id]:
        USER_DATA[user_id]['last_collect'] = 0
    if 'last_bonus' not in USER_DATA[user_id]:
        USER_DATA[user_id]['last_bonus'] = 0

    # --- КОМАНДА: БАЛАНС ---
    if text in ["баланс", "/баланс", "б"]:
        balance = USER_DATA[user_id]['balance']
        farms = USER_DATA[user_id]['farms']
        bot.send_message(
            message.chat.id, 
            f"💳 **Ваш профиль:**\n\n"
            f"💰 Баланс: {balance} монет\n"
            f"🚜 Майнинг-фермы: {farms} шт. (приносят доход!)"
        )

    # --- КОМАНДА: ЕЖЕДНЕВНЫЙ БОНУС (РОВНО 2000 МОНЕТ РАЗ В 24 ЧАСА) ---
    elif text in ["бонус", "/бонус"]:
        current_time = time.time()
        last_bonus = USER_DATA[user_id]['last_bonus']
        cooldown = 24 * 60 * 60  # 24 часа в секундах
        
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
        bot.send_message(
            message.chat.id,
            f"🏪 **Магазин бизнесов:**\n\n"
            f"🚜 **Майнинг-ферма**\n"
            f"├ Цена: 3000 монет\n"
            f"└ Доход: 500 монет (сбор раз в 1 час)\n\n"
            f"Для покупки напишите: `купить ферму`"
        )

    # --- КОМАНДА: КУПИТЬ ФЕРМУ ---
    elif text == "купить ферму":
        if USER_DATA[user_id]['balance'] >= 3000:
            USER_DATA[user_id]['balance'] -= 3000
            USER_DATA[user_id]['farms'] += 1
            bot.send_message(
                message.chat.id, 
                f"🎉 Поздравляем! Вы купили **Майнинг-ферму**!\n"
                f"💰 Остаток баланса: {USER_DATA[user_id]['balance']} монет."
            )
        else:
            bot.send_message(message.chat.id, "❌ У вас недостаточно монет! Ферма стоит 3000 монет.")

    # --- КОМАНДА: СБОР ДОХОДА С ЛИМИТОМ В 1 ЧАС ---
    elif text == "ферма сбор":
        farms = USER_DATA[user_id]['farms']
        if farms == 0:
            return bot.send_message(message.chat.id, "❌ У вас еще нет ферм для сбора дохода! Зайдите в `магазин`.")
        
        current_time = time.time()
        last_collect = USER_DATA[user_id]['last_collect']
        cooldown = 60 * 60
        
        if current_time - last_collect < cooldown:
            remaining_time = int(cooldown - (current_time - last_collect))
            minutes = remaining_time // 60
            seconds = remaining_time % 60
            return bot.send_message(
                message.chat.id, 
                f"⏳ **Рано для сбора!**\nВаши фермы еще генерируют монеты. Подождите еще **{minutes} мин. {seconds} сек.**"
            )
            
        profit = farms * 500
        USER_DATA[user_id]['balance'] += profit
        USER_DATA[user_id]['last_collect'] = current_time
        
        bot.send_message(
            message.chat.id, 
            f"🚜 Вы успешно собрали доход с {farms} ферм!\n"
            f"💵 Получено: +{profit} монет.\n"
            f"💰 Новый баланс: {USER_DATA[user_id]['balance']} монет."
        )

    # --- КОМАНДА: КАЗИНО ---
    elif text.startswith("казино") or text.startswith("к"):
        cmd_body = text.replace("казино", "").replace("к", "").strip()
        
        if not cmd_body:
            return bot.send_message(message.chat.id, "❌ Напишите ставку! Пример: `К 100` или `казино 100`")
            
        try:
            bet = int(cmd_body)
        except ValueError:
            return bot.send_message(message.chat.id, "❌ Ставка должна быть целым числом!")
            
        if bet <= 0:
            return bot.send_message(message.chat.id, "❌ Ставка должна быть больше нуля!")
        if bet > USER_DATA[user_id]['balance']:
            return bot.send_message(message.chat.id, f"❌ Недостаточно монет! Баланс: {USER_DATA[user_id]['balance']}")

        USER_DATA[user_id]['balance'] -= bet

        anim_message = bot.send_message(message.chat.id, "🎰 **Крутим слот-машину...**\n\n[ ⏳ | ⏳ | ⏳ ]")
        
        slots_frames = [
            "[ 🍒 | 🍋 | 💎 ]",
            "[ 🔔 | 🍒 | 🍇 ]",
            "[ 💎 | 💎 | 🍋 ]"
        ]
        
        for frame in slots_frames:
            time.sleep(0.6)
            try:
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=anim_message.message_id,
                    text=f"🎰 **Барабаны крутятся!**\n\n{frame}"
                )
            except Exception:
                pass
                
        time.sleep(0.6)

        multipliers = [0, 0.25, 0.5, 1.5, 2, 3, 4, 5, 10]
        weights = [35, 20, 15, 15, 10, 2, 1.5, 1, 0.5]
        
        chosen_multiplier = random.choices(multipliers, weights=weights, k=1)[0]
        
        win_amount = int(bet * chosen_multiplier)
        USER_DATA[user_id]['balance'] += win_amount

        if chosen_multiplier == 10:
            visual_slots = "[ 👑 | 👑 | 👑 ]"
            status_text = f"🚨 **МЕГА ДЖЕКПОТ x10!!!** 🎉\n🔥 Вы сорвали главный куш: +{win_amount} монет!"
        elif chosen_multiplier == 5:
            visual_slots = "[ 💎 | 💎 | 💎 ]"
            status_text = f"💎 **Крупный выигрыш x5!** 🎉\nВам крупно повезло: +{win_amount} монет!"
        elif chosen_multiplier == 4:
            visual_slots = "[ 🔔 | 🔔 | 🔔 ]"
            status_text = f"🔔 **Отличный выигрыш x4!** 🎉\nПрекрасный результат: +{win_amount} монет!"
        elif chosen_multiplier == 3:
            visual_slots = "[ 🍇 | 🍇 | 🍇 ]"
            status_text = f"🍇 **Хороший выигрыш x3!** 🎉\nУдача на вашей стороне: +{win_amount} монет!"
        elif chosen_multiplier in [1.5, 2]:
            visual_slots = "[ 🍒 | 🍒 | 🍒 ]"
            status_text = f"🎉 **Выигрыш x{chosen_multiplier}!**\nВы в плюсе: +{win_amount} монет!"
        elif chosen_multiplier in [0.25, 0.5]:
            visual_slots = "[ 🍋 | 🍋 | 🍉 ]"
            status_text = f"📉 **Проигрыш (Множитель x{chosen_multiplier})**\nКазино заколо часть ставки, но вернуло утешительные +{win_amount} монет."
        else:
            visual_slots = "[ 💀 | 🍫 | 🎰 ]"
            status_text = f"💥 **Полный проигрыш x0...**\nСтавка полностью сгорела в пользу заведения."

        final_text = (
            f"🎰 **РЕЗУЛЬТАТ:** {visual_slots}\n\n"
            f"{status_text}\n"
            f"💰 Ваш баланс: {USER_DATA[user_id]['balance']} монет."
        )

        try:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=anim_message.message_id,
                text=final_text
            )
        except Exception:
            bot.send_message(message.chat.id, final_text)

print("Бот успешно обновлен и запущен...")
bot.infinity_polling()
