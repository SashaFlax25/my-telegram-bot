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
        USER_DATA[user_id] = {'balance': 5000, 'farms': 0}
        
    bot.send_message(
        message.chat.id, 
        f"Привет, {message.from_user.first_name}!\n\n"
        "💰 Тебе начислено: **5000 монет**.\n\n"
        "💵 Доступные команды (можно большими и маленькими буквами):\n"
        "👉 `Б` (или `баланс`) — проверить кошелек\n"
        "👉 `К [ставка]` (или `казино [ставка]`) — сыграть на монеты\n"
        "👉 `магазин` — купить бизнес или ферму\n"
        "👉 `ферма сбор` — собрать доход с ферм"
    )

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    text = message.text.lower().strip()

    if user_id not in USER_DATA:
        USER_DATA[user_id] = {'balance': 5000, 'farms': 0}

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

    # --- КОМАНДА: МАГАЗИН ---
    elif text in ["магазин", "/магазин"]:
        bot.send_message(
            message.chat.id,
            f"🏪 **Магазин бизнесов:**\n\n"
            f"🚜 **Майнинг-ферма**\n"
            f"├ Цена: 3000 монет\n"
            f"└ Доход: 500 монет за каждый сбор\n\n"
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

    # --- КОМАНДА: СБОР ДОХОДА ---
    elif text == "ферма сбор":
        farms = USER_DATA[user_id]['farms']
        if farms == 0:
            bot.send_message(message.chat.id, "❌ У вас еще нет ферм для сбора дохода! Зайдите в `магазин`.")
        else:
            profit = farms * 500
            USER_DATA[user_id]['balance'] += profit
            bot.send_message(
                message.chat.id, 
                f"🚜 Вы успешно собрали доход с {farms} ферм!\n"
                f"💵 Получено: +{profit} монет.\n"
                f"💰 Новый баланс: {USER_DATA[user_id]['balance']} монет."
            )

    # --- КОМАНДА: КАЗИНО (С АНИМАЦИЕЙ СЛОТОВ) ---
    elif text.startswith("казино") or text.startswith("к"):
        # Извлекаем ставку из текста команды
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

        # Отправляем начальное анимационное сообщение
        anim_message = bot.send_message(message.chat.id, "🎰 **Крутим слот-машину...**\n\n[ ⏳ | ⏳ | ⏳ ]")
        
        # Списки смайликов для имитации вращения
        slots_frames = [
            "[ 🍒 | 🍋 | 💎 ]",
            "[ 🔔 | 🍒 | 🍇 ]",
            "[ 💎 | 💎 | 🍋 ]"
        ]
        
        # Крутим барабаны (меняем текст сообщения с микро-паузами)
        for frame in slots_frames:
            time.sleep(0.6)
            try:
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=anim_message.message_id,
                    text=f"🎰 **Барабаны крутятся!**\n\n{frame}"
                )
            except Exception:
                pass # Игнорируем редкие ошибки Telegram API при частом редактировании
                
        time.sleep(0.6)

        # Рассчитываем результат игры (Честный шанс 50/50)
        is_win = random.choice([True, False])
        
        if is_win:
            USER_DATA[user_id]['balance'] += bet
            final_text = f"🎰 **РЕЗУЛЬТАТ:** [ 💎 | 💎 | 💎 ]\n\n🎉 **ВЫИГРЫШ!**\nТы поднял +{bet} монет!\n💰 Баланс: {USER_DATA[user_id]['balance']} монет."
        else:
            USER_DATA[user_id]['balance'] -= bet
            final_text = f"🎰 **РЕЗУЛЬТАТ:** [ 🍒 | 🍋 | 🍇 ]\n\n💥 **ПРОИГРЫШ...**\nКазино забрало {bet} монет.\n💰 Остаток: {USER_DATA[user_id]['balance']} монет."

        # Выводим финальный результат игры
        try:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=anim_message.message_id,
                text=final_text
            )
        except Exception:
            # На случай сбоя редактирования — просто отправляем новое сообщение
            bot.send_message(message.chat.id, final_text)

print("Бот успешно обновлен и запущен...")
bot.infinity_polling()
