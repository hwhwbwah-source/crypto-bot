import telebot
import time
import requests
from threading import Thread

# ===== НАСТРОЙКИ (ЗАМЕНИ НА СВОИ) =====
TOKEN = "ТВОЙ_ТОКЕН_ОТ_BOTFATHER"
ADMIN_ID = 123456789
WALLET = "TВаш_адрес_USDT"
TRONGRID_API_KEY = "твой_ключ_от_trongrid"
FILE_URL = "https://ссылка_на_товар"
PRICE = 10
# ======================================

bot = telebot.TeleBot(TOKEN)
processed_txs = set()

def check_usdt_payment():
    headers = {"TRON-PRO-API-KEY": TRONGRID_API_KEY}
    url = f"https://api.trongrid.io/v1/accounts/{WALLET}/transactions/trc20"
    try:
        resp = requests.get(url, headers=headers, params={"limit": 20, "only_confirmed": True})
        if resp.status_code == 200:
            for tx in resp.json().get("data", []):
                if tx.get("token_info", {}).get("symbol") != "USDT":
                    continue
                tx_id = tx["transaction_id"]
                if tx_id in processed_txs:
                    continue
                amount = int(tx.get("value", 0)) / 10**6
                if abs(amount - PRICE) < 0.01:
                    processed_txs.add(tx_id)
                    return True, tx_id, amount
    except Exception as e:
        print("Ошибка:", e)
    return False, None, 0

def background_checker(user_id):
    for _ in range(30):
        time.sleep(30)
        success, tx_id, amount = check_usdt_payment()
        if success:
            bot.send_message(user_id, f"✅ Оплачено {amount} USDT!\nТовар: {FILE_URL}")
            bot.send_message(ADMIN_ID, f"💰 Продажа! {amount} USDT от {user_id}")
            return
    bot.send_message(user_id, "⏰ Время вышло. Напишите /check")

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
        f"🛒 Цена: {PRICE} USDT\n💳 Кошелёк: `{WALLET}`\n\nПосле оплаты товар придёт сам.",
        parse_mode='Markdown')
    Thread(target=background_checker, args=(message.chat.id,)).start()

@bot.message_handler(commands=['check'])
def manual_check(message):
    success, tx_id, amount = check_usdt_payment()
    if success:
        bot.send_message(message.chat.id, f"✅ Товар: {FILE_URL}")
    else:
        bot.send_message(message.chat.id, f"❌ Платёж не найден")

print("Бот запущен!")
bot.infinity_polling()
