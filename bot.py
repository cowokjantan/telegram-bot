import asyncio
import os
import requests
from aiogram import Bot, Dispatcher, types

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Token bot dari Railway
API_URL = "https://soneium.blockscout.com/api"  # API Blockscout Soneium

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Database sementara: menyimpan chat_id dan alamat yang ingin dilacak
tracked_addresses = {}

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.answer("Halo! Kirimkan alamat wallet yang ingin kamu lacak.")

@dp.message_handler(commands=["track"])
async def track_address(message: types.Message):
    address = message.text.split(" ")[1] if len(message.text.split()) > 1 else None

    if not address:
        await message.answer("Gunakan perintah: `/track <alamat_wallet>`")
        return

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
                        value = int(last_tx["value"]) / (10**18)  # Ubah dari Wei ke SONE

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
    asyncio.create_task(check_transactions())  # Jalankan pemantauan transaksi
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
