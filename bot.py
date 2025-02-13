import os
import asyncio
import logging
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Ambil token dari environment variable
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN or not TOKEN.strip():
    raise ValueError("❌ BOT_TOKEN tidak ditemukan! Pastikan sudah diatur di Railway Variables atau .env.")

# Inisialisasi bot dan dispatcher
bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher()

# API Blockscout Soneium
BLOCKSCOUT_API = "https://soneium.blockscout.com/api"

# Data tracking
tracked_addresses = {}
last_seen_tx = {}

# Perintah /start
@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("✅ Bot berjalan!\nKirim alamat wallet untuk mulai tracking.")

# Perintah untuk menambahkan alamat
@dp.message(Command("track"))
async def track_address(message: Message):
    address = message.text.split(" ")[1] if len(message.text.split(" ")) > 1 else None
    if not address:
        await message.answer("❌ Harap masukkan alamat setelah perintah /track")
        return

    chat_id = message.chat.id
    if chat_id not in tracked_addresses:
        tracked_addresses[chat_id] = set()
    
    tracked_addresses[chat_id].add(address)
    await message.answer(f"✅ Alamat <code>{address}</code> ditambahkan ke tracking!")

# Fungsi untuk mengambil transaksi dari Blockscout
async def fetch_transactions(address):
    try:
        url = f"{BLOCKSCOUT_API}?module=account&action=txlist&address={address}"
        response = requests.get(url)
        data = response.json()
        
        if data.get("status") == "1" and "result" in data:
            return data["result"]
        return []
    except Exception as e:
        logging.error(f"Error fetching transactions: {e}")
        return []

# Fungsi untuk menentukan jenis transaksi
def get_transaction_type(tx, address):
    from_addr = tx["from"].lower()
    to_addr = tx["to"].lower() if tx["to"] else None

    if to_addr is None:
        return "UNKNOWN"

    address = address.lower()

    # Jika address kita adalah pengirim
    if from_addr == address:
        if "input" in tx and tx["input"] != "0x":
            return "SELL"  # Kemungkinan transaksi jual NFT
        return "SEND"

    # Jika address kita adalah penerima
    if to_addr == address:
        if "input" in tx and tx["input"] != "0x":
            return "BUY"  # Kemungkinan transaksi beli NFT
        return "RECEIVED"

    return "UNKNOWN"

# Fungsi untuk memantau transaksi
async def check_transactions():
    while True:
        for chat_id, addresses in tracked_addresses.items():
            for address in addresses:
                transactions = await fetch_transactions(address)

                if not transactions:
                    continue
                
                for tx in transactions:
                    tx_hash = tx["hash"]
                    if address not in last_seen_tx:
                        last_seen_tx[address] = set()
                    
                    if tx_hash in last_seen_tx[address]:
                        continue  # Lewati jika sudah dikirim sebelumnya

                    last_seen_tx[address].add(tx_hash)
                    tx_link = f"<a href='https://soneium.blockscout.com/tx/{tx_hash}'>🔗 Lihat TX</a>"

                    # Tentukan jenis transaksi
                    tx_type = get_transaction_type(tx, address)
                    if tx_type == "SEND":
                        message = f"📤 <b>Send:</b> {tx_link}"
                    elif tx_type == "RECEIVED":
                        message = f"📥 <b>Received:</b> {tx_link}"
                    elif tx_type == "BUY":
                        message = f"🛒 <b>Buy NFT:</b> {tx_link}"
                    elif tx_type == "SELL":
                        message = f"💰 <b>Sell NFT:</b> {tx_link}"
                    else:
                        continue  # Jika tidak diketahui, skip

                    await bot.send_message(chat_id, message)

        await asyncio.sleep(30)  # Cek transaksi setiap 30 detik

# Fungsi utama untuk menjalankan bot
async def main():
    logging.basicConfig(level=logging.INFO)
    asyncio.create_task(check_transactions())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
