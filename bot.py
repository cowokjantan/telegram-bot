import os
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message

API_URL = "https://soneium.blockscout.com/api?module=account&action=txlist&address={}"  # API untuk fetch transaksi
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Simpan daftar address dan hash transaksi yang sudah dikirim
tracked_addresses = {}
sent_transactions = set()

@dp.message(commands=["start"])
async def start_handler(message: Message):
    await message.answer("Selamat datang! Kirimkan alamat yang ingin Anda lacak.")

@dp.message()
async def add_address_handler(message: Message):
    address = message.text.strip()
    if address.startswith("0x") and len(address) == 42:
        tracked_addresses[address] = "Address " + address[-4:]  # Bisa diberi nama custom
        await message.answer(f"Alamat {address} ditambahkan ke daftar pelacakan.")
    else:
        await message.answer("Alamat tidak valid. Harap masukkan alamat Ethereum yang benar.")

async def fetch_transactions(address):
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL.format(address)) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("result", [])
            return []

async def check_transactions():
    while True:
        for address in list(tracked_addresses.keys()):
            transactions = await fetch_transactions(address)
            for tx in transactions:
                tx_hash = tx["hash"]
                if tx_hash not in sent_transactions:
                    sent_transactions.add(tx_hash)
                    message = f"🚀 Transaksi terdeteksi untuk {tracked_addresses[address]}\n"
                    message += f"Tx Hash: {tx_hash}\n"
                    await bot.send_message(chat_id=os.getenv("TELEGRAM_CHAT_ID"), text=message)
        await asyncio.sleep(30)  # Cek setiap 30 detik

async def main():
    asyncio.create_task(check_transactions())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
