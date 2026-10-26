import random
import os
import telebot

# Бот будет безопасно брать токен из настроек сервера Render
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8706024761:AAEiHBbTLsNdGKyJT4vaurzdop34uZeDvlk')
bot = telebot.TeleBot(BOT_TOKEN)

# Наша база данных в памяти телефона
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
        "👉 `К [ставка]` (или `казино`) — сыграть на монеты\n"
        "👉 `магазин` — купить бизнес или ферму\n"
        "👉 `ферма сбор` — собрать доход с ферм"
    )

# Обработка всех текстовых команд
@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    text = message.text.lower().strip() # Этот метод делает ЛЮБУЮ букву маленькой для проверки!

    # Если пользователя нет в базе, регистрируем
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {'balance': 5000, 'farms': 0}

    # 1. КОМАНДА: БАЛАНС (сработает на Б, б, баланс, Баланс)
    if text in ["баланс", "/баланс", "б"]:
        balance = USER_DATA[user_id]['balance']
        farms = USER_DATA[user_id]['farms']
        bot.send_message(
            message.chat.id, 
            f"💳 **Ваш профиль:**\n\n"
            f"💰 Баланс: {balance} монет\n"
            f"🚜 Майнинг-фермы: {farms} шт. (приносят доход!)"
        )

    # 2. КОМАНДА: МАГАЗИН
    elif text in ["магазин", "/магазин"]:
        bot.send_message(
            message.chat.id,
            f"🏪 **Магазин бизнесов:**\n\n"
            f"🚜 **Майнинг-ферма**\n"
            f"├ Цена: 3000 монет\n"
            f"└ Доход: 500 монет за каждый сбор\n\n"
            f"Для покупки напишите: `купить ферму`"
        )

    # 3. КОМАНДА: КУПИТЬ ФЕРМУ
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

    # 4. КОМАНДА: СБОР ДОХОДА
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

    # 5. КОМАНДА: КАЗИНО (сработает на казино, Казино, К 100, к 100)
    elif text.startswith("казино") or text.startswith("к "):
        args = text.split()
        if len(args) < 2:
            return bot.send_message(message.chat.id, "❌ Напиши ставку через пробел! Пример: `К 100`")
        try:
            bet = int(args[1])
        except ValueError:
            return bot.send_message(message.chat.id, "❌ Ставка должна быть числом!")
        if bet <= 0:
            return bot.send_message(message.chat.id, "❌ Ставка должна быть больше нуля!")
        if bet > USER_DATA[user_id]['balance']:
            return bot.send_message(message.chat.id, f"❌ Недостаточно монет! Баланс: {USER_DATA[user_id]['balance']}")

        if random.choice([True, False]):
            USER_DATA[user_id]['balance'] += bet
            bot.send_message(message.chat.id, f"🎰 **ВЫИГРЫШ!** 🎉\nТы поднял {bet} монет!\n💰 Баланс: {USER_DATA[user_id]['balance']}")
        else:
            USER_DATA[user_id]['balance'] -= bet
            bot.send_message(message.chat.id, f"🎰 **ПРОИГРЫШ...** 💥\nКазино забрало {bet} монет.\n💰 Остаток: {USER_DATA[user_id]['balance']}")

print("Бот успешно обновлен и запущен...")
bot.infinity_polling()
      
