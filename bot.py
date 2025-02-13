import asyncio
import os
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Ambil token dari Railway
API_URL = "https://soneium.blockscout.com/api"  # API Blockscout Soneium

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Database sementara: menyimpan chat_id dan alamat yang ingin dilacak
tracked_addresses = {}

async def start_handler(message: Message):
    await message.answer("Halo! Kirimkan alamat wallet yang ingin kamu lacak.")

async def track_address(message: Message):
    args = message.text.split(" ")
    if len(args) < 2:
        await message.answer("Gunakan perintah: `/track <alamat_wallet>`")
        return

    address = args[1]
    chat_id = message.chat.id

    if chat_id not in tracked_addresses:
        tracked_addresses[chat_id] = set()
    
    tracked_addresses[chat_id].add(address)
    await message.answer(f"✅ Alamat {address} telah ditambahkan untuk dilacak!")

async def check_transactions():
    while True:
        for chat_id, addresses in tracked_addresses.items():
            for address in addresses:
                try:
                    response = requests.get(f"{API_URL}?module=account&action=txlist&address={address}")
                    data = response.json()

                    if "result" in data and data["result"]:
                        last_tx = data["result"][0]  # Ambil transaksi terbaru
                        tx_hash = last_tx["hash"]
                        from_addr = last_tx["from"]
                        to_addr = last_tx["to"]
                        value = int(last_tx["value"]) / (10**18)  # Konversi dari Wei ke SONE

                        message = (f"🚀 **Transaksi Baru Ditemukan** 🚀\n"
                                   f"🔹 **TX Hash:** {tx_hash}\n"
                                   f"🔹 **Dari:** {from_addr}\n"
                                   f"🔹 **Ke:** {to_addr}\n"
                                   f"🔹 **Jumlah:** {value} SONE")
                        
                        await bot.send_message(chat_id, message, parse_mode="Markdown")

                except Exception as e:
                    print(f"Error saat mengambil transaksi: {e}")

        await asyncio.sleep(60)  # Cek transaksi setiap 60 detik

async def main():
    dp.message.register(start_handler, Command("start"))
    dp.message.register(track_address, Command("track"))

    asyncio.create_task(check_transactions())  # Jalankan pemantauan transaksi
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
