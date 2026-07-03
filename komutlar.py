import requests
import time
import datetime
import logging
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
import ayarlar

async def kufur_ekle_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ayarlar.BOT_SAHIBI_ID:
        await update.message.reply_text("❌ Bu komutu sadece botun sahibi kullanabilir!")
        return
    if not context.args:
        await update.message.reply_text("⚠️ Örnek: `/kufurekle kelime`")
        return
    yeni = " ".join(context.args)
    if ayarlar.yasakli_ekle(yeni):
        await update.message.reply_text(f"✅ '{yeni}' yasaklılar listesine eklendi.")
    else:
        await update.message.reply_text("ℹ️ Bu kelime zaten listede var.")

async def kufur_sil_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ayarlar.BOT_SAHIBI_ID: return
    if not context.args: return
    silinecek = " ".join(context.args)
    if ayarlar.yasakli_sil(silinecek):
        await update.message.reply_text(f"🗑️ '{silinecek}' yasaklı listesinden silindi.")

async def kufur_listesi_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    liste = ayarlar.yasakli_listesi_getir()
    if not liste:
        await update.message.reply_text("📋 Yasaklı kelime listesi temiz kanka!")
        return
    await update.message.reply_text("🚫 **Yasaklı Kelimeler:**\n\n" + "\n".join([f"- {k}" for k in liste]), parse_mode="Markdown")

async def grup_ekle_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ayarlar.BOT_SAHIBI_ID: return
    try:
        grup_id = int(context.args[0])
        ayarlar.grup_onayla(grup_id, "Onaylı Müşteri")
        await update.message.reply_text(f"✅ {grup_id} ID'li grup onaylandı!")
    except:
        await update.message.reply_text("⚠️ Geçerli bir sayısal ID gir kanka.")

async def grup_cikar_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ayarlar.BOT_SAHIBI_ID: return
    try:
        grup_id = int(context.args[0])
        if ayarlar.grup_sil(grup_id):
            await update.message.reply_text(f"🗑️ {grup_id} ID'li grubun lisansı iptal edildi.")
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
        hedef_id = int(context.args[0])
        await chat.unban_member(user_id=hedef_id)
        ayarlar.banlanan_sil(hedef_id, chat.id)
        await update.message.reply_text(f"✅ ID: {hedef_id} olan kullanıcının engeli kaldırıldı.")
    except: pass

async def start_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ayarlar.kullanici_kaydet(user.id, user.username, user.first_name)
    await update.message.reply_text(f"Selam {user.first_name} kanka! Ben çok işlevli robotun. 😎\n\n🌤️ /hava [şehir]\n💰 /doviz\n🤖 Düz yazarsan yapay zeka cevaplar.\n📋 /banlist")

async def hava_durumu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    sehir = " ".join(context.args)
    try:
        res = requests.get(f"https://wttr.in{sehir}?format=%C+%t")
        await update.message.reply_text(f"🌤️ {sehir.capitalize()} Hava Durumu: {res.text.strip()}")
    except: pass

async def doviz_kuru(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = requests.get("https://er-api.com").json()
        try_kuru = res["rates"]["TRY"]
        await update.message.reply_text(f"💰 **Anlık Döviz Kurları:**\n\n💵 1 Dolar: {try_kuru:.2f} TL")
    except: pass
