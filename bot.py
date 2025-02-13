import os
import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils.markdown import hlink
from aiogram.enums import ParseMode
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = "https://soneium.blockscout.com/api"
CHECK_INTERVAL = 10  # Cek transaksi setiap 10 detik

# Cek apakah token bot tersedia
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN tidak ditemukan! Pastikan sudah diatur di Railway Variables atau .env.")

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Data penyimpanan address & transaksi
addresses = {}  # {address: "nama"}
last_tx_hashes = set()  # Set untuk menyimpan hash transaksi yang sudah dikirim

# Handler untuk /start
@dp.message(commands=["start"])
async def start_handler(message: Message):
    await message.answer("👋 Selamat datang! Kirim alamat untuk mulai melacak transaksi.")

# Handler untuk menyimpan alamat
@dp.message(lambda message: message.text.startswith("add "))
async def add_address_handler(message: Message):
    try:
        _, address, name = message.text.split(" ", 2)
        addresses[address.lower()] = name
        await message.answer(f"✅ Alamat {name} ({address}) berhasil ditambahkan!")
    except ValueError:
        await message.answer("❌ Format salah! Gunakan: `add <address> <nama>`")

# Handler untuk melihat alamat yang tersimpan
@dp.message(commands=["list"])
async def list_addresses(message: Message):
    if not addresses:
        await message.answer("🚫 Belum ada alamat yang disimpan.")
    else:
        text = "\n".join([f"{name}: {addr}" for addr, name in addresses.items()])
        await message.answer(f"📌 Alamat yang dilacak:\n{text}")

# Fungsi untuk mendapatkan transaksi terbaru
async def get_transactions(address):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}?module=account&action=txlist&address={address}") as response:
            if response.status == 200:
                return await response.json()
    return None

# Fungsi untuk cek transaksi baru
async def check_transactions():
    while True:
        for address, name in addresses.items():
            data = await get_transactions(address)
            if data and "result" in data:
                for tx in data["result"]:
                    tx_hash = tx["hash"]
                    if tx_hash not in last_tx_hashes:
                        last_tx_hashes.add(tx_hash)
                        action = "🔄 Transaksi"
                        if tx["to"].lower() == address:
                            action = "📥 Menerima"
                        elif tx["from"].lower() == address:
                            action = "📤 Mengirim"
                        tx_link = hlink("🔗 Tx Hash", f"https://soneium.blockscout.com/tx/{tx_hash}")
                        await bot.send_message(
                            chat_id=message.chat.id,
                            text=f"{action} oleh {name}:\n{tx_link}"
                        )
        await asyncio.sleep(CHECK_INTERVAL)

# Jalankan bot
async def main():
    asyncio.create_task(check_transactions())
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
