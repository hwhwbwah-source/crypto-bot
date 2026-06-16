import telebot
import time
import requests
from threading import Thread

TOKEN = "8812392613:AAGMo5-fq1zmT2VMCYeU7K9J8dZwVw8tI4k"
ADMIN_ID = 7377776553
WALLET = "TFPCcRJiikiyZYVZdrSXHzVcHuwQVcFXRd"
TRONGRID_API_KEY = "fefb216e-ce6a-4658-a940-f5deb90a1d5c"

# ТОВАРЫ (меняй цены и ссылки)
products = {
    "1": {"price": 5, "file": "https://canva.link/h2qinj1vvqfhmqf"},
    "2": {"price": 5, "file": "https://canva.link/khthwn88h4xmaud"},
}

bot = telebot.TeleBot(TOKEN)
processed_txs = set()

def check_usdt_payment(price):
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
                if abs(amount - price) < 0.01:
                    processed_txs.add(tx_id)
                    return True, tx_id, amount
    except Exception as e:
        print("Ошибка:", e)
    return False, None, 0

def background_checker(user_id, product_key):
    p = products[product_key]
    for _ in range(30):
        time.sleep(30)
        success, tx_id, amount = check_usdt_payment(p["price"])
        if success:
            bot.send_message(user_id, f"✅ Оплачено {amount} USDT!\n📥 {p['file']}")
            bot.send_message(ADMIN_ID, f"💰 Продажа {product_key}! {amount} USDT от {user_id}")
            return
    bot.send_message(user_id, "⏰ Время вышло. Напишите /check")

@bot.message_handler(commands=['start'])
def start(message):
    parts = message.text.split()
    product_key = parts[1] if len(parts) > 1 else None
    
    if product_key and product_key in products:
        p = products[product_key]
        bot.send_message(message.chat.id,
            f"🛒 Товар: {product_key}\n💰 Цена: {p['price']} USDT\n💳 Кошелёк: `{WALLET}`\n\nПосле оплаты товар придёт сам",
            parse_mode='Markdown')
        Thread(target=background_checker, args=(message.chat.id, product_key)).start()
    else:
        bot.send_message(message.chat.id, "❌ Товар не найден")

@bot.message_handler(commands=['check'])
def manual_check(message):
    bot.send_message(message.chat.id, "Напишите /start с названием товара")

print("Бот запущен!")
bot.infinity_polling()
