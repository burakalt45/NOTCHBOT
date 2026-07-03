import random
import requests
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import ayarlar

# ==========================================
# 🌐 KÜRESEL DİL DESTEĞİ SÖZLÜĞÜ (DİNAMİK)
# ==========================================
METINLER = {
    "TR": {
        "start": "Selam {} kanka! Ben çok işlevli robotun. 😎",
        "hava_hata": "Kanka şehir yazmadın! Örnek: /hava istanbul",
        "kumar_hata": "❌ Bakiyen bu bahis için yetersiz kanka!",
        "dil_degisti": "✅ Botun dili başarıyla **Türkçe** olarak ayarlandı!",
        "dil_secin": "🌐 Lütfen bot için bir dil seçin kanka:",
        "aktifler_hata": "📊 Henüz istatistik yok kanka.",
        "aktifler_baslik": "🏆 **En Aktif Üyeler:**\n\n",
        "kripto_hata": "⚠️ Kanka analiz edilecek coini yazmadın! Örnek: `/kripto BTC`"
    },
    "EN": {
        "start": "Hello {} bro! I am your multi-functional bot. 😎",
        "hava_hata": "Bro you didn't write a city! Example: /hava london",
        "kumar_hata": "❌ Your balance is insufficient for this bet bro!",
        "dil_degisti": "✅ Bot language has been successfully set to **English**!",
        "dil_secin": "🌐 Please select a language for the bot bro:",
        "aktifler_hata": "📊 No stats available yet bro.",
        "aktifler_baslik": "🏆 **Most Active Members:**\n\n",
        "kripto_hata": "⚠️ Bro you didn't write a coin to analyze! Example: `/kripto BTC`"
    }
}

# ==========================================
# 🛠️ YÖNETİCİ VE LİSANS KOMUTLARI
# ==========================================
async def kufur_ekle_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ayarlar.BOT_SAHIBI_ID:
        await update.message.reply_text("❌ Kanka bu komutu sadece botun sahibi kullanabilir!")
        return
    if not context.args:
        await update.message.reply_text("⚠️ Örnek kullanım: `/kufurekle kelime`")
        return
    yeni_kelime = " ".join(context.args)
    if ayarlar.yasakli_ekle(yeni_kelime):
        await update.message.reply_text(f"✅ '{yeni_kelime}' yasaklılar listesine eklendi.")
    else:
        await update.message.reply_text("ℹ️ Bu kelime zaten listede var.")

async def kufur_sil_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ayarlar.BOT_SAHIBI_ID: return
    if not context.args:
        await update.message.reply_text("⚠️ Örnek kullanım: `/kufursil kelime`")
        return
    silinecek_kelime = " ".join(context.args)
    if ayarlar.yasakli_sil(silinecek_kelime):
        await update.message.reply_text(f"🗑️ '{silinecek_kelime}' yasaklı listesinden silindi.")
    else:
        await update.message.reply_text("❓ Bu kelime zaten listede yok.")

async def kufur_listesi_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    liste = ayarlar.yasakli_listesi_getir()
    if not liste:
        await update.message.reply_text("📋 Yasaklı kelime listesi temiz kanka!")
        return
    await update.message.reply_text("🚫 **Yasaklı Kelimeler:**\n\n" + "\n".join([f"- {k}" for k in liste]), parse_mode="Markdown")

async def grup_ekle_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ayarlar.BOT_SAHIBI_ID: return
    if not context.args:
        await update.message.reply_text("⚠️ Örnek kullanım: `/grupekle -100123456`")
        return
    try:
        grup_id = int(context.args)
        ayarlar.grup_onayla(grup_id, "Onaylı Müşteri")
        await update.message.reply_text(f"✅ {grup_id} ID'li grup onaylandı! Bot aktif.")
    except ValueError:
        await update.message.reply_text("⚠️ Geçerli bir sayısal ID gir kanka.")

async def grup_cikar_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ayarlar.BOT_SAHIBI_ID: return
    if not context.args:
        await update.message.reply_text("⚠️ Örnek kullanım: `/grupcikar -100123456`")
        return
    try:
        grup_id = int(context.args)
        if ayarlar.grup_sil(grup_id):
            await update.message.reply_text(f"🗑️ {grup_id} ID'li grubun lisansı iptal edildi.")
        else:
            await update.message.reply_text("❓ Bu grup onaylı listesinde yok.")
    except ValueError:
        await update.message.reply_text("⚠️ Geçerli bir sayısal ID gir kanka.")
async def start_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    ayarlar.kullanici_kaydet(user.id, user.username, user.first_name)
    dil = ayarlar.dil_getir(chat.id)
    mesaj = METINLER[dil]["start"].format(user.first_name) + "\n\n🌤️ /hava [şehir]\n💰 /doviz\n🤖 /analiz\n🌐 /dil\n📋 /banlist"
    await update.message.reply_text(mesaj)

async def dil_degistir_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        uye = await chat.get_member(update.effective_user.id)
        if uye.status not in ["creator", "administrator"] and update.effective_user.id != ayarlar.BOT_SAHIBI_ID:
            return
    dil = ayarlar.dil_getir(chat.id)
    klavye = [[InlineKeyboardButton("🇹🇷 Türkçe", callback_data="setlang_TR"),
                InlineKeyboardButton("🇺🇸 English", callback_data="setlang_EN")]]
    await update.message.reply_text(METINLER[dil]["dil_secin"], reply_markup=InlineKeyboardMarkup(klavye))

async def hava_durumu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    dil = ayarlar.dil_getir(chat.id)
    if not context.args:
        await update.message.reply_text(METINLER[dil]["hava_hata"])
        return
    sehir = " ".join(context.args)
    try:
        res = requests.get(f"https://wttr.in{sehir}?format=%C+%t")
        if res.status_code == 200 and "💡" not in res.text:
            await update.message.reply_text(f"🌤️ {sehir.capitalize()}: {res.text.strip()}")
    except: pass

async def doviz_kuru(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = requests.get("https://er-api.com").json()
        try_kuru = res["rates"]["TRY"]
        eur_try = try_kuru / res["rates"]["EUR"]
        mesaj = f"💰 **Anlık Döviz Kurları:**\n\n💵 1 Dolar: {try_kuru:.2f} TL\n💶 1 Euro: {eur_try:.2f} TL"
        await update.message.reply_text(mesaj, parse_mode="Markdown")
    except: pass

async def kripto_analiz_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    dil = ayarlar.dil_getir(chat.id)
    if not context.args:
        await update.message.reply_text(METINLER[dil]["kripto_hata"], parse_mode="Markdown")
        return
    coin = context.args.upper()
    await update.message.reply_text(f"📊 {coin} için piyasa verileri inceleniyor, bekle kanka...")
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"https://binance.com{coin}USDT")
            data = res.json()
        fiyat, degisim = float(data['lastPrice']), float(data['priceChangePercent'])
        istemi = (
            f"Sen profesyonel finansal veri özetleyicisisin. {coin} verileri: Fiyat: {fiyat} USDT, Değişim: %{degisim}. "
            f"Al-sat sinyali vermeden durum özeti yaz. Dil/Tarz: {dil} modunda samimi arkadaş dili olsun. Sonuna YALNIZCA TR ise 'Yatırım tavsiyesi değildir' ekle."
        )
        response = ayarlar.ai_client.models.generate_content(model='gemini-2.5-flash', contents=istemi)
        await update.message.reply_text(response.text)
    except:
        await update.message.reply_text("❌ API veya Veri Hatası.")

async def iddaa_analiz_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    mac_bilgisi = " ".join(context.args)
    await update.message.reply_text("⚽ Yapay zeka takımları analiz ediyor, bekleyin...")
    try:
        istemi = f"Kullanıcı şu maç hakkında yorum istiyor: {mac_bilgisi}. Kesin kupon vaat etmeden samimi, kanka tarzı eğlenceli 2 tahmin yürüt. Sonuna sorumluluk reddi ekle."
        response = ayarlar.ai_client.models.generate_content(model='gemini-2.5-flash', contents=istemi)
        await update.message.reply_text(response.text)
    except: pass
async def ban_listesi_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private": return
    uye = await chat.get_member(update.effective_user.id)
    if uye.status not in ["creator", "administrator"] and update.effective_user.id != ayarlar.BOT_SAHIBI_ID: return
    liste = ayarlar.banlanan_listesi_getir(chat.id)
    if not liste:
        await update.message.reply_text("📋 Bot tarafından banlanmış kimse yok.")
        return
    mesaj = "🚷 **Banlananlar Listesi:**\n\n"
    for uid, uname, tarih in liste:
        ulink = f"@{uname}" if uname else f"ID: {uid}"
        mesaj += f"👤 {ulink}\n📅 Tarih: {tarih}\n🔓 Kaldırmak için: `/unban {uid}`\n\n"
    await update.message.reply_text(mesaj, parse_mode="Markdown")

async def unban_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private": return
    try:
        hedef_id = int(context.args)
        await chat.unban_member(user_id=hedef_id)
        ayarlar.banlanan_sil(hedef_id, chat.id)
        await update.message.reply_text(f"✅ ID: {hedef_id} engeli kaldırıldı.")
    except: pass

async def en_aktifler_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    dil = ayarlar.dil_getir(chat.id)
    if chat.type == "private": return
    liste = ayarlar.en_aktifleri_getir(chat.id)
    if not liste:
        await update.message.reply_text(METINLER[dil]["aktifler_hata"])
        return
    mesaj = METINLER[dil]["aktifler_baslik"]
    madalya = ["🥇", "🥈", "🥉"] + ["▫️"] * 7
    for i, (ad, uname, sayi) in enumerate(liste):
        isim = f"@{uname}" if uname else ad
        mesaj += f"{madalya[i]} {isim} — {sayi} mesaj\n"
    await update.message.reply_text(mesaj, parse_mode="Markdown")

async def bakiye_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private": return
    bakiye = ayarlar.bakiye_getir(chat.id, user.id)
    await update.message.reply_text(f"💰 {user.first_name}, bakiyen: **{bakiye} KankaCoin**", parse_mode="Markdown")

async def slot_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    dil = ayarlar.dil_getir(chat.id)
    if chat.type == "private" or not context.args: return
    try:
        bahis = int(context.args)
        if bahis <= 0: return
    except: return
    bakiye = ayarlar.bakiye_getir(chat.id, user.id)
    if bakiye < bahis:
        await update.message.reply_text(METINLER[dil]["kumar_hata"])
        return
    emojis = ["🍒", "🍋", "🍇", "🔔", "💎"]
    s1, s2, s3 = random.choice(emojis), random.choice(emojis), random.choice(emojis)
    if s1 == s2 == s3:
        ayarlar.bakiye_guncelle(chat.id, user.id, bahis * 5)
        m = f"🎰 **SLOT** 🎰\n| {s1} | {s2} | {s3} |\n\n🎉 MÜKEMMEL! 3'te 3! **+{bahis*5} KankaCoin**"
    elif s1 == s2 or s2 == s3 or s1 == s3:
        ayarlar.bakiye_guncelle(chat.id, user.id, bahis * 2)
        m = f"🎰 **SLOT** 🎰\n| {s1} | {s2} | {s3} |\n\n🥳 Güzel! 2'li yakaladın. **+{bahis*2} KankaCoin**"
    else:
        ayarlar.bakiye_guncelle(chat.id, user.id, -bahis)
        m = f"🎰 **SLOT** 🎰\n| {s1} | {s2} | {s3} |\n\n💸 Ah be kanka tutmadı! **-{bahis} KankaCoin**"
    await update.message.reply_text(m, parse_mode="Markdown")

async def gecemodu_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private" or not context.args: return
    uye = await chat.get_member(update.effective_user.id)
    if uye.status not in ["creator", "administrator"] and update.effective_user.id != ayarlar.BOT_SAHIBI_ID: return
    durum = context.args.lower()
    if durum == "ac":
        ayarlar.gece_modu_guncelle(chat.id, True)
        await update.message.reply_text("🔒 **Gece Modu Aktif!** Yöneticiler hariç chat kilitlendi kanka.")
    elif durum == "kapat":
        ayarlar.gece_modu_guncelle(chat.id, False)
        await update.message.reply_text("🔓 **Gece Modu Kapatıldı!** Chat herkese açıldı.")

async def chati_ozetle_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private": return
    await update.message.reply_text("📝 Son mesajlar taranıyor ve yapay zeka özetiniz çıkarılıyor...")
    mesajlar = ayarlar.son_mesajlari_getir(chat.id)
    if not mesajlar: return
    sohbet_metni = "\n".join([f"{yazar}: {msg}" for yazar, msg in mesajlar])
    istemi = f"Aşağıdaki konuşmaları oku ve konuşulan ana konuları samimi kanka diliyle maddeler halinde özetle:\n\n{sohbet_metni}"
    try:
        response = ayarlar.ai_client.models.generate_content(model='gemini-2.5-flash', contents=istemi)
        await update.message.reply_text(response.text)
    except: pass

async def davetler_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private": return
    liste = ayarlar.en_cok_davet_edenler(chat.id)
    if not liste: return
    mesaj = "🎁 **Davet Yarışması Liderliği:**\n\n"
    for i, (ad, uname, adet) in enumerate(liste):
        link = f"@{uname}" if uname else ad
        mesaj += f"{i+1}. 👤 {link} ➡️ **{adet} Davet**\n"
    await update.message.reply_text(mesaj, parse_mode="Markdown")

async def rpg_profil_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private": return
    ad, meslek, seviye, xp, can = ayarlar.rpg_karakter_getir(chat.id, user.id, user.first_name)
    m = f"🎮 **Karakter Profilin:**\n\n🎭 Sınıf: {meslek}\n🎖️ Seviye: {seviye}\n✨ XP: {xp}/{seviye*100}\n❤️ Can: %{can}"
    await update.message.reply_text(m, parse_mode="Markdown")

async def rpg_saldir_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    saldiran = update.effective_user
    if chat.type == "private" or not update.message.reply_to_message: return
    hedef = update.message.reply_to_message.from_user
    if hedef.id == saldiran.id or hedef.is_bot: return
    s_ad, s_meslek, s_lvl, _, s_can = ayarlar.rpg_karakter_getir(chat.id, saldiran.id, saldiran.first_name)
    h_ad, h_meslek, h_lvl, _, h_can = ayarlar.rpg_karakter_getir(chat.id, hedef.id, hedef.first_name)
    if s_can < 20 or h_can <= 0: return
    if random.randint(1, 100) > (100 - (50 + (s_lvl - h_lvl) * 5)):
        hasar = random.randint(15, 35) + s_lvl
        para = random.randint(50, 200)
        ayarlar.rpg_karakter_guncelle(chat.id, hedef.id, -hasar, 0)
        ayarlar.rpg_karakter_guncelle(chat.id, saldiran.id, 0, 25)
        ayarlar.bakiye_guncelle(chat.id, saldiran.id, para)
        ayarlar.bakiye_guncelle(chat.id, hedef.id, -para)
        await update.message.reply_text(f"⚔️ **BAŞARILI SALDIRI!**\n\n💥 @{hedef.username} kullanıcısına **{hasar} HASAR** vurdun ve cebinden **{para} KankaCoin** çaldın!")
    else:
        hasar = random.randint(10, 25)
        ayarlar.rpg_karakter_guncelle(chat.id, saldiran.id, -hasar, 0)
        await update.message.reply_text(f"🛡️ **ISKALADIN!**\n\n⚠️ Karşı taraf kontra atakla sana **{hasar} HASAR** bıraktı kanka!")

SERI = ["♠", "♥️", "♦", "♣"]
KARTLAR = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

async def blackjack_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private" or user.id in ayarlar.BLACKJACK_OYUNLAR or not context.args: return
    try:
        bahis = int(context.args)
        if bahis <= 0 or ayarlar.bakiye_getir(chat.id, user.id) < bahis: return
    except: return
    deste = [f"{k} {s}" for k in KARTLAR for s in SERI]
    random.shuffle(deste)
    oyuncu, kasa = [deste.pop(), deste.pop()], [deste.pop(), deste.pop()]
    ayarlar.BLACKJACK_OYUNLAR[user.id] = {"bahis": bahis, "oyuncu_kartlar": oyuncu, "kasa_kartlar": kasa, "chat_id": chat.id, "deste": deste}
    o_toplam = ayarlar.blackjack_kart_degeri(oyuncu)
    if o_toplam == 21:
        ayarlar.bakiye_guncelle(chat.id, user.id, int(bahis * 1.5))
        del ayarlar.BLACKJACK_OYUNLAR[user.id]
        await update.message.reply_text("😎 **BLACKJACK!** İlk elden 21 yaptın kanka!")
        return
    klavye = [[InlineKeyboardButton("🃏 Kart Çek", callback_data=f"bj_hit_{user.id}"), InlineKeyboardButton("🛑 Kal", callback_data=f"bj_stand_{user.id}")]]
    await update.message.reply_text(f"🃏 **BLACKJACK**\n💰 Bahis: {bahis}\n🫵 Kartların: {', '.join(oyuncu)} ({o_toplam})\n🕵️‍♂️ Kasa Kartı: {kasa}, [ Gizli ]", reply_markup=InlineKeyboardMarkup(klavye))

async def kullanici_analiz_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private": return
    hedef = update.message.reply_to_message.from_user if update.message.reply_to_message else user
    if hedef.is_bot: return
    await update.message.reply_text("🔍 Yapay zeka gruptaki tüm verilerinizi inceliyor, bekleyin...")
    try:
        bakiye = ayarlar.bakiye_getir(chat.id, hedef.id)
        ad, meslek, lvl, _, _ = ayarlar.rpg_karakter_getir(chat.id, hedef.id, hedef.first_name)
        istemi = f"Şu üyeyi eğlenceli bir psikolog gibi analiz et ve tatlıca dalga geçerek gruptaki rolünü söyle. Ad: {hedef.first_name}, KankaCoin: {bakiye}, RPG: {meslek} Seviye {lvl}."
        response = ayarlar.ai_client.models.generate_content(model='gemini-2.5-flash', contents=istemi)
        await update.message.reply_text(response.text)
    except: pass
