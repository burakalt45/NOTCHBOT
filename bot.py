import time
import datetime
import logging
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import ayarlar
import komutlar

async def bot_gruba_eklendi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not update.message.new_chat_members: return
    for yeni_uye in update.message.new_chat_members:
        if yeni_uye.username == context.bot.username:
            if ayarlar.grup_onayli_mi(chat.id):
                await update.message.reply_text("Selam kankalar! Bu grupta aktifim. 😎")
                return
            iban_mesaji = (
                f"👋 Selam! Bu grup için aktif bir lisans bulunmuyor.\n\n"
                f"🔒 **Satın Almak İçin:**\n🏦 **IBAN:** {ayarlar.IBAN_BILGISI}\nAlıcı: {ayarlar.ALICI_ADI}\n\n"
                f"🆔 **Grup ID:** `{chat.id}`\n*(Açıklamaya bu ID'yi yaz kanka)*"
            )
            await update.message.reply_text(iban_mesaji, parse_mode="Markdown")

async def yeni_uye_karsilama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not ayarlar.grup_onayli_mi(chat.id) or not update.message.new_chat_members: return
    for yeni_uye in update.message.new_chat_members:
        if not yeni_uye.is_bot:
            ayarlar.kullanici_kaydet(yeni_uye.id, yeni_uye.username, yeni_uye.first_name)
            await update.message.reply_text(f"🌟 Hoş geldin {yeni_uye.first_name} kanka! Yardım için: /start")

async def ana_mesaj_yoneticisi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    gelen_metin = update.message.text
    if user.is_bot or not gelen_metin: return

    if chat.type in ["group", "supergroup"]:
        if not ayarlar.grup_onayli_mi(chat.id): return
        
        # Link Filtresi
        if "http://" in gelen_metin.lower() or "https://" in gelen_metin.lower() or ".com" in gelen_metin.lower():
            try:
                await update.message.delete()
                await chat.ban_member(user_id=user.id)
                simdi = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                ayarlar.banlanan_kaydet(user.id, user.username, chat.id, simdi)
                await update.message.reply_text(f"🚨 @{user.username} reklam sebebiyle BANLANDI!")
                return
            except: return

        # Spam Filtresi
        simdi = time.time()
        if user.id not in ayarlar.KULLANICI_TAKIP:
            ayarlar.KULLANICI_TAKIP[user.id] = {"zamanlar": [], "ihlal_sayisi": 0}
        ayarlar.KULLANICI_TAKIP[user.id]["zamanlar"].append(simdi)
        ayarlar.KULLANICI_TAKIP[user.id]["zamanlar"] = [z for z in ayarlar.KULLANICI_TAKIP[user.id]["zamanlar"] if simdi - z < 3]
        
        if len(ayarlar.KULLANICI_TAKIP[user.id]["zamanlar"]) >= 4:
            ayarlar.KULLANICI_TAKIP[user.id]["ihlal_sayisi"] += 1
            ihlal = ayarlar.KULLANICI_TAKIP[user.id]["ihlal_sayisi"]
            if ihlal == 1:
                await update.message.reply_text(f"⚠️ Yavaş yaz @{user.username} kanka!")
            elif ihlal == 2:
                try: await chat.restrict_member(user_id=user.id, permissions=ChatPermissions(can_send_messages=False), until_date=int(simdi + 1800))
                except: pass
            elif ihlal >= 3:
                try: 
                    await chat.ban_member(user_id=user.id)
                    tarih_s = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                    ayarlar.banlanan_kaydet(user.id, user.username, chat.id, tarih_s)
                except: pass
            return

    # Yapay Zeka
    if chat.type == "private" or context.bot.username in gelen_metin:
        temiz = gelen_metin.replace(f"@{context.bot.username}", "").strip()
        try:
            res = ayarlar.ai_client.models.generate_content(
                model='gemini-2.5-flash', contents=temiz,
                config={'system_instruction': "Sen 'kanka' diye hitap eden samimi bir Telegram botusun. Kısa cevap ver."}
            )
            await update.message.reply_text(res.text)
        except: pass

def main():
    ayarlar.veritabani_kur()
    app = Application.builder().token(ayarlar.TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("kufurekle", komutlar.kufur_ekle_komutu))
    app.add_handler(CommandHandler("kufursil", komutlar.kufur_sil_komutu))
    app.add_handler(CommandHandler("kufurler", komutlar.kufur_listesi_komutu))
    app.add_handler(CommandHandler("grupekle", komutlar.grup_ekle_komutu))
    app.add_handler(CommandHandler("grupcikar", komutlar.grup_cikar_komutu))
    app.add_handler(CommandHandler("banlist", komutlar.ban_listesi_komutu))
    app.add_handler(CommandHandler("unban", komutlar.unban_komutu))
    app.add_handler(CommandHandler("start", komutlar.start_komutu))
    app.add_handler(CommandHandler("hava", komutlar.hava_durumu))
    app.add_handler(CommandHandler("doviz", komutlar.doviz_kuru))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, bot_gruba_eklendi), group=-1)
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, yeni_uye_karsilama), group=0)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ana_mesaj_yoneticisi))

    print("Bot 3 parçalı modüler sistemle çalışıyor kanka...")
    app.run_polling()

if __name__ == '__main__':
    main()
