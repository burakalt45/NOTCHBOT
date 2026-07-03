import time
import datetime
import logging
import os
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from google import genai
import ayarlar
import komutlar

# Yapay Zeka Istemci Kurulumu
ayarlar.ai_client = genai.Client(api_key=ayarlar.GEMINI_API_KEY)

# 🔄 CAPTCHA BUTON TIKLAMALARINI YAKALAYAN FONKSIYON
async def captcha_buton_tiklama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    
    if data.startswith("captcha_"):
        hedef_id = int(data.split("_")[1])
        if user_id != hedef_id:
            await query.answer("❌ Bu buton senin icin degil kanka!", show_alert=True)
            return
            
        chat = query.message.chat
        await chat.restrict_member(user_id=user_id, permissions=ChatPermissions(can_send_messages=True))
        await query.message.delete()
        dil = ayarlar.dil_getir(chat.id)
        onay_msg = f"✅ Dogrulama basarili! Hoş geldin @{query.from_user.username} kanka." if dil == "TR" else f"✅ Verification successful! Welcome @{query.from_user.username} bro."
        await context.bot.send_message(chat_id=chat.id, text=onay_msg)
        await query.answer()

# 🌐 DIL DEGISTIRME BUTON TIKLAMASINI YAKALAYAN FONKSIYON
async def dil_buton_yonetimi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    data = query.data

    if data.startswith("setlang_"):
        yeni_dil = data.split("_")[1]
        ayarlar.dil_guncelle(chat_id, yeni_dil)
        await query.message.edit_text(komutlar.METINLER[yeni_dil]["dil_degisti"], parse_mode="Markdown")
        await query.answer()

# 🎰 BLACKJACK OYUN BUTONLARINI YONETEN MOTOR
async def blackjack_buton_yonetimi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if data.startswith("bj_"):
        _, eylem, hedef_str = data.split("_")
        hedef_id = int(hedef_str)

        if user_id != hedef_id:
            await query.answer("❌ Bu masa senin degil kanka! 🎲", show_alert=True)
            return

        if user_id not in ayarlar.BLACKJACK_OYUNLAR:
            await query.message.edit_text("❌ Oyun suresi dolmus kanka.")
            await query.answer()
            return

        oyun = ayarlar.BLACKJACK_OYUNLAR[user_id]
        chat_id = oyun["chat_id"]
        bahis = oyun["bahis"]
        oyuncu = oyun["oyuncu_kartlar"]
        kasa = oyun["kasa_kartlar"]
        deste = oyun["deste"]

        if eylem == "hit":
            oyuncu.append(deste.pop())
            o_toplam = ayarlar.blackjack_kart_degeri(oyuncu)

            if o_toplam > 21:
                ayarlar.bakiye_guncelle(chat_id, user_id, -bahis)
                del ayarlar.BLACKJACK_OYUNLAR[user_id]
                await query.message.edit_text(f"💥 **YANDIN KANKA!** (Bust)\n🫵 Kartlarin: {', '.join(oyuncu)} ({o_toplam})\n💸 **-{bahis} KankaCoin** kaybettin.")
            else:
                klavye = [[InlineKeyboardButton("🃏 Kart Cek", callback_data=f"bj_hit_{user_id}"), InlineKeyboardButton("🛑 Kal", callback_data=f"bj_stand_{user_id}")]]
                await query.message.edit_text(f"🃏 **BLACKJACK**\n🫵 Kartlarin: {', '.join(oyuncu)} ({o_toplam})\n🕵️‍♂️ Kasa: {kasa[0]}, [ Gizli ]", reply_markup=InlineKeyboardMarkup(klavye))

        elif eylem == "stand":
            o_toplam = ayarlar.blackjack_kart_degeri(oyuncu)
            k_toplam = ayarlar.blackjack_kart_degeri(kasa)

            while k_toplam < 17:
                kasa.append(deste.pop())
                k_toplam = ayarlar.blackjack_kart_degeri(kasa)

            if k_toplam > 21:
                ayarlar.bakiye_guncelle(chat_id, user_id, bahis)
                m = f"🥳 **KASA YANDI!**\n🕵️‍♂️ Kasa: {', '.join(kasa)} ({k_toplam})\n🎉 **+{bahis} KankaCoin** kazandin!"
            elif o_toplam > k_toplam:
                ayarlar.bakiye_guncelle(chat_id, user_id, bahis)
                m = f"🏆 **KAZANDIN KANKA!**\n🫵 Sen: {o_toplam} | 🕵️‍♂️ Kasa: {k_toplam}\n🔥 **+{bahis} KankaCoin** cebe indi."
            elif o_toplam < k_toplam:
                ayarlar.bakiye_guncelle(chat_id, user_id, -bahis)
                m = f"☠️ **KASA KAZANDI!**\n🕵️‍♂️ Kasa: {k_toplam} | 🫵 Sen: {o_toplam}\n💸 **-{bahis} KankaCoin** kaybettin."
            else:
                m = f"🤝 **BERABERE!**\n💰 Parani geri aldin kanka, kayip yok."

            del ayarlar.BLACKJACK_OYUNLAR[user_id]
            await query.message.edit_text(m)
        await query.answer()

# 🛠️ GRUP ADMIN PANEL BUTON TIKLAMALARINI YAKALAYAN FONKSIYON
async def panel_buton_yonetimi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    chat = query.message.chat
    data = query.data

    if data.startswith("panel_"):
        uye = await chat.get_member(user_id)
        if uye.status not in ["creator", "administrator"] and user_id != ayarlar.BOT_SAHIBI_ID:
            await query.answer("❌ Bu paneli sadece grup yoneticileri sekillendirebilir kanka!", show_alert=True)
            return

        eylem = data.replace("panel_", "")
        if eylem == "kapat":
            await query.message.delete()
            await query.answer()
            return

        reklam, kufur, rpg, kumar = ayarlar.grup_ayar_getir(chat.id)
        if eylem == "reklam_filtresi": reklam = not reklam; ayarlar.grup_ayar_guncelle(chat.id, "reklam_filtresi", reklam)
        elif eylem == "kufur_filtresi": kufur = not kufur; ayarlar.grup_ayar_guncelle(chat.id, "kufur_filtresi", kufur)
        elif eylem == "rpg_aktif": rpg = not rpg; ayarlar.grup_ayar_guncelle(chat.id, "rpg_aktif", rpg)
        elif eylem == "kumar_aktif": kumar = not kumar; ayarlar.grup_ayar_guncelle(chat.id, "kumar_aktif", kumar)

        r_emo = "🟢 ACIK" if reklam else "🔴 KAPALI"
        k_emo = "🟢 ACIK" if kufur else "🔴 KAPALI"
        rpg_emo = "🟢 ACIK" if rpg else "🔴 KAPALI"
        kmr_emo = "🟢 ACIK" if kumar else "🔴 KAPALI"

        yeni_klavye = [
            [InlineKeyboardButton(f"🔗 Reklam Engel: {r_emo}", callback_data="panel_reklam_filtresi")],
            [InlineKeyboardButton(f"🤬 Kufur Engel: {k_emo}", callback_data="panel_kufur_filtresi")],
            [InlineKeyboardButton(f"⚔️ RPG Oyunu: {rpg_emo}", callback_data="panel_rpg_aktif")],
            [InlineKeyboardButton(f"🎰 Kumar/Casino: {kmr_emo}", callback_data="panel_kumar_aktif")],
            [InlineKeyboardButton("❌ Paneli Kapat", callback_data="panel_kapat")]
        ]
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(yeni_klavye))
        await query.answer("✅ Ayar guncellendi kanka!")
# ⚽ IDDAA TARA BUTONUNA BASILDIGINDA TETIKLENEN ANALIZ MOTORU
async def iddaa_buton_yonetimi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    data = query.data

    if data.startswith("iddaa_tara_"):
        mac_bilgisi = data.replace("iddaa_tara_", "")
        await query.answer("⚽ Analiz motoru baslatildi kanka!", show_alert=False)
        await query.message.edit_text(f"🔄 **{mac_bilgisi}** maci yapay zeka tarafindan taraniyor... Lutfen bekleyin kanka...")
        try:
            istemi = (
                f"Sen profesyonel bir bahis ve futbol analistisin. Kullanici su macin taranip analiz edilmesini istedi: {mac_bilgisi}. "
                "Bu mactaki takimlarin genel form durumunu samimi, 'kanka' hitapli derin bir analiz cikar. "
                "Ysek ihtilli 2 adet iddaa bahis onerisi sun (Orn: KG VAR, 2.5 UST). "
                "Sonuna 'Bahis oynamak risklidir, sorumluluk size aittir' uyarisi ekle."
            )
            response = ayarlar.ai_client.models.generate_content(model='gemini-2.5-flash', contents=istemi)
            await query.message.edit_text(f"✅ **MAÇ TARAMA SONUCU TAMAMLANDI** ✅\n🏟️ **Analiz Edilen:** {mac_bilgisi}\n\n{response.text}", parse_mode="Markdown")
        except:
            await query.message.edit_text("❌ Mac taranirken yapay zeka motorunda bir hata olustu kanka.")
        await query.answer()

# 🛡️ BOT BAŞKA BIR GRUBA EKLENDIGINDE LISANS ISTEYEN ALAN
async def bot_gruba_eklendi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not update.message.new_chat_members: return
    for yeni_uye in update.message.new_chat_members:
        if yeni_uye.username == context.bot.username:
            if ayarlar.grup_onayli_mi(chat.id):
                await update.message.reply_text("Selam kankalar! Bu grupta aktifim. 😎")
                return
            iban_mesaji = (
                f"👋 Selam! Beni bu gruba eklediniz ama bu grup için aktif bir lisans bulunmuyor.\n\n🔒 **Satın Almak Icin:**\n"
                f"🏦 **IBAN:** {ayarlar.IBAN_BILGISI}\nAlıcı: {ayarlar.ALICI_ADI}\n\n"
                f"🆔 **Grup ID:** `{chat.id}`\n*(Acıklamaya bu ID'yi yaz kanka)*"
            )
            await update.message.reply_text(iban_mesaji, parse_mode="Markdown")

# 🧠 YAPAY ZEKALI TEHDIT KORUMASI VE CAPTCHA BASLATMA
async def yeni_uye_karsilama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not ayarlar.grup_onayli_mi(chat.id) or not update.message.new_chat_members: return
    for yeni_uye in update.message.new_chat_members:
        if yeni_uye.is_bot: continue
        
        tarama = f"Ad: {yeni_uye.first_name}, Username: {yeni_uye.username}"
        istemi = f"Su Telegram uye ismini analiz et: {tarama}. Eger reklam botu kalibi, illegal bahis, pornografik kelimeler varsa SADECE 'TEHLIKELI' yaz, temizse SADECE 'TEMIZ' yaz."
        try:
            res = ayarlar.ai_client.models.generate_content(model='gemini-2.5-flash', contents=istemi)
            if "TEHLIKELI" in res.text.upper():
                await chat.ban_member(user_id=yeni_uye.id)
                await update.message.reply_text(f"🚨 **Yapay Zeka Koruması:** @{yeni_uye.username} supheli profil nedeniyle gruba alinmadan **BANLANDI!** 🚷")
                return
        except: pass

        await chat.restrict_member(user_id=yeni_uye.id, permissions=ChatPermissions(can_send_messages=False))
        klavye = [[InlineKeyboardButton("🤖 Ben Insanim", callback_data=f"captcha_{yeni_uye.id}")]]
        await update.message.reply_text(f"🚨 **GUVENLIK KORUMASI** 🚨\n\nHos geldin {yeni_uye.first_name} kanka! Konusmak icin butona basmalisin.", reply_markup=InlineKeyboardMarkup(klavye))
# 📑 CHAT FILTRELERI, SES CEVIRICI VE YAPAY ZEKA SOHBET MOTORU
async def ana_mesaj_yoneticisi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if user.is_bot: return

    # 🎙️ SES KAYDINI METNE CEVIRME SISTEMI
    if update.message.voice and ayarlar.grup_onayli_mi(chat.id):
        try:
            voice_file = await update.message.voice.get_file()
            ses_yolu = "ses.ogg"
            await voice_file.download_to_drive(ses_yolu)
            with open(ses_yolu, "rb") as f: ses_veri = f.read()
            response = ayarlar.ai_client.models.generate_content(model='gemini-2.5-flash', contents=[{"mime_type": "audio/ogg", "data": ses_veri}, "Bu ses kaydinda ne konusuldugunu Turkce olarak metne dok."])
            await update.message.reply_text(f"🗣️ **Ses Kaydı Metni (@{user.username}):**\n\n*\"{response.text.strip()}\"*", parse_mode="Markdown")
            if os.path.exists(ses_yolu): os.remove(ses_yolu)
            return
        except: return

    gelen_metin = update.message.text
    if not gelen_metin: return

    if chat.type in ["group", "supergroup"]:
        if not ayarlar.grup_onayli_mi(chat.id): return
        
        reklam, kufur, rpg, _ = ayarlar.grup_ayar_getir(chat.id)

        if ayarlar.gece_modu_durum(chat.id):
            uye = await chat.get_member(user.id)
            if uye.status not in ["creator", "administrator"] and user.id != ayarlar.BOT_SAHIBI_ID:
                try: await update.message.delete()
                except: pass
                return

        # Reklam & Link Filtresi Kontrolu
        if reklam and ("http://" in gelen_metin.lower() or "https://" in gelen_metin.lower() or ".com" in gelen_metin.lower()):
            try:
                await update.message.delete()
                await chat.ban_member(user_id=user.id)
                ayarlar.banlanan_kaydet(user.id, user.username, chat.id, datetime.datetime.now().strftime("%d/%m/%Y %H:%M"))
                await update.message.reply_text(f"🚨 @{user.username} reklam sebebiyle BANLANDI!")
                return
            except: return

        ayarlar.mesaj_logla(chat.id, user.first_name, gelen_metin)
        ayarlar.mesaj_sayisi_arttir(chat.id, user.id, user.username, user.first_name)
        if rpg:
            ayarlar.rpg_karakter_guncelle(chat.id, user.id, 5, 5)

        # Kademeli Spam Filtresi
        simdi = time.time()
        if user.id not in ayarlar.KULLANICI_TAKIP: ayarlar.KULLANICI_TAKIP[user.id] = {"zamanlar": [], "ihlal_sayisi": 0}
        ayarlar.KULLANICI_TAKIP[user.id]["zamanlar"].append(simdi)
        ayarlar.KULLANICI_TAKIP[user.id]["zamanlar"] = [z for z in ayarlar.KULLANICI_TAKIP[user.id]["zamanlar"] if simdi - z < 3]
        if len(ayarlar.KULLANICI_TAKIP[user.id]["zamanlar"]) >= 4:
            ayarlar.KULLANICI_TAKIP[user.id]["ihlal_sayisi"] += 1
            ihlal = ayarlar.KULLANICI_TAKIP[user.id]["ihlal_sayisi"]
            if ihlal == 1: await update.message.reply_text(f"⚠️ Yavas yaz @{user.username} kanka!")
            elif ihlal == 2:
                try: await chat.restrict_member(user_id=user.id, permissions=ChatPermissions(can_send_messages=False), until_date=int(simdi + 1800))
                except: pass
            elif ihlal >= 3:
                try:
                    await chat.ban_member(user_id=user.id)
                    ayarlar.banlanan_kaydet(user.id, user.username, chat.id, datetime.datetime.now().strftime("%d/%m/%Y %H:%M"))
                except: pass
            return

    # Kufur Filtresi Kontrolu
    _, kufur_aktif, _, _ = ayarlar.grup_ayar_getir(chat.id)
    if kufur_aktif:
        yasakli_kelimeler = ayarlar.yasakli_listesi_getir()
        if any(kelime in gelen_metin.lower() for kelime in yasakli_kelimeler):
            try:
                await update.message.delete()
                if chat.type in ["group", "supergroup"]: await update.message.reply_text(f"⚠️ @{user.username} argo yasaktir!")
                return
            except: return

    # Yapay Zeka Sohbet Motoru
    if chat.type == "private" or context.bot.username in gelen_metin:
        temiz = gelen_metin.replace(f"@{context.bot.username}", "").strip()
        grup_dili = ayarlar.dil_getir(chat.id)
        talimat = "Türkçe ve samimi 'kanka' tarzında" if grup_dili == "TR" else "English and friendly 'bro' style"
        try:
            res = ayarlar.ai_client.models.generate_content(model='gemini-2.5-flash', contents=temiz, config={'system_instruction': f"You are a helpful Telegram bot. Reply in {talimat}. Keep it short."})
            await update.message.reply_text(res.text)
        except: pass

# ⚙️ BOTUN ATESLENDIGI ANA MOTOR
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
    app.add_handler(CommandHandler("kripto", komutlar.kripto_analiz_komutu))
    app.add_handler(CommandHandler("iddaa", komutlar.iddaa_analiz_komutu))
    app.add_handler(CommandHandler("aktifler", komutlar.en_aktifler_komutu))
    app.add_handler(CommandHandler("bakiye", komutlar.bakiye_komutu))
    app.add_handler(CommandHandler("slot", komutlar.slot_komutu))
    app.add_handler(CommandHandler("gecemodu", komutlar.gecemodu_komutu))
    app.add_handler(CommandHandler("ozet", komutlar.chati_ozetle_komutu))
    app.add_handler(CommandHandler("davetler", komutlar.davetler_komutu))
    app.add_handler(CommandHandler("profilim", komutlar.rpg_profil_komutu))
    app.add_handler(CommandHandler("saldir", komutlar.rpg_saldir_komutu))
    app.add_handler(CommandHandler("dil", komutlar.dil_degistir_komutu))
    app.add_handler(CommandHandler("blackjack", komutlar.blackjack_komutu))
    app.add_handler(CommandHandler("analiz", komutlar.kullanici_analiz_komutu))
    app.add_handler(CommandHandler("eros", komutlar.eros_oku_komutu))
    app.add_handler(CommandHandler("giybet", komutlar.giybet_komutu))
    app.add_handler(CommandHandler("fal", komutlar.fal_bak_komutu))
    app.add_handler(CommandHandler("panel", komutlar.grup_paneli_komutu))

    app.add_handler(CallbackQueryHandler(captcha_buton_tiklama, pattern=r"^captcha_"))
    app.add_handler(CallbackQueryHandler(dil_buton_yonetimi, pattern=r"^setlang_"))
    app.add_handler(CallbackQueryHandler(blackjack_buton_yonetimi, pattern=r"^bj_"))
    app.add_handler(CallbackQueryHandler(panel_buton_yonetimi, pattern=r"^panel_"))
    app.add_handler(CallbackQueryHandler(iddaa_buton_yonetimi, pattern=r"^iddaa_tara_"))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, bot_gruba_eklendi), group=-1)
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, yeni_uye_karsilama), group=0)
    app.add_handler(MessageHandler((filters.TEXT | filters.VOICE) & ~filters.COMMAND, ana_mesaj_yoneticisi))

    print("Yazılı süper botun şu an aktif kanka! Çalışıyor...")
    app.run_polling()

if __name__ == '__main__':
    main()

