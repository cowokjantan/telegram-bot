import os
import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

# Inisialisasi bot
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# File penyimpanan address
FILE_NAME = "tracked_addresses.json"

# Muat data jika ada, atau buat dictionary kosong
try:
    with open(FILE_NAME, "r") as file:
        tracked_addresses = json.load(file)
except FileNotFoundError:
    tracked_addresses = {}

# ✅ Fungsi untuk menyimpan data ke file JSON
def save_data():
    with open(FILE_NAME, "w") as file:
        json.dump(tracked_addresses, file, indent=4)

# ✅ Command untuk menambahkan address dengan nama
@dp.message(Command("add"))
async def add_address(message: Message):
    try:
        _, address, name = message.text.split(" ", 2)  # Format: /add 0x1234abcd Wallet1
        if address in tracked_addresses:
            await message.answer(f"⚠️ Address {address} sudah ada dengan nama '{tracked_addresses[address]}'!")
        else:
            tracked_addresses[address] = name
            save_data()
            await message.answer(f"✅ Address **{address}** telah ditambahkan sebagai **{name}**.")
    except ValueError:
        await message.answer("⚠️ Format salah! Gunakan: `/add 0x1234abcd NamaWallet`")

# ✅ Command untuk menampilkan daftar address
@dp.message(Command("list"))
async def list_addresses(message: Message):
    if not tracked_addresses:
        await message.answer("📭 Belum ada address yang dilacak.")
    else:
        response = "📌 **Daftar Address yang Dilacak:**\n"
        for address, name in tracked_addresses.items():
            response += f"🔹 **{name}**: `{address}`\n"
        await message.answer(response, parse_mode="Markdown")

# ✅ Command untuk menghapus address
@dp.message(Command("remove"))
async def remove_address(message: Message):
    try:
        _, address = message.text.split(" ", 1)  # Format: /remove 0x1234abcd
        if address in tracked_addresses:
            name = tracked_addresses.pop(address)
            save_data()
            await message.answer(f"❌ Address **{address}** ({name}) telah dihapus dari daftar.")
        else:
            await message.answer(f"⚠️ Address {address} tidak ditemukan!")
    except ValueError:
        await message.answer("⚠️ Format salah! Gunakan: `/remove 0x1234abcd`")

# ✅ Menjalankan bot
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
