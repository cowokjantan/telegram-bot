import os
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Token bot dari Railway
API_URL = "https://soneium.blockscout.com/api"  # API Blockscout Soneium

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Simpan daftar alamat yang akan dipantau
tracked_addresses = set()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("✅ Bot aktif! Kirim alamat Soneium untuk mulai tracking.")

@dp.message()
async def track_address(message: types.Message):
    """Menambahkan alamat untuk dipantau"""
    address = message.text.strip()
    if address.startswith("0x") and len(address) == 42:
        tracked_addresses.add(address)
        await message.answer(f"🔍 Alamat {address} ditambahkan untuk dipantau!")
    else:
        await message.answer("⚠️ Masukkan alamat Soneium yang valid.")

async def check_transactions():
    """Cek transaksi terbaru dari alamat yang dipantau"""
    while True:
        if tracked_addresses:
            async with aiohttp.ClientSession() as session:
                for address in tracked_addresses:
                    async with session.get(f"{API_URL}?module=account&action=txlist&address={address}") as response:
                        data = await response.json()
                        if "result" in data:
                            for tx in data["result"]:
                                tx_hash = tx["hash"]
                                from_addr = tx["from"]
                                to_addr = tx["to"]
                                value = int(tx["value"]) / 10**18  # Konversi ke satuan token
                                message = f"📢 Transaksi Baru!\n\n🔹 TX Hash: {tx_hash}\n🔹 Dari: {from_addr}\n🔹 Ke: {to_addr}\n🔹 Nilai: {value} SONE"
                                await bot.send_message(chat_id, message)
        await asyncio.sleep(30)  # Cek setiap 30 detik

async def main():
    asyncio.create_task(check_transactions())  # Mulai tracking
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
