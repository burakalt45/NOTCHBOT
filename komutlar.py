def bakiye_getir(chat_id, user_id):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("SELECT bakiye FROM kullanici_ekonomi WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
    veri = cursor.fetchone()
    if not veri:
        cursor.execute("INSERT OR IGNORE INTO kullanici_ekonomi VALUES (?, ?, 1000)", (chat_id, user_id))
        conn.commit()
        bakiye = 1000
    else: bakiye = veri[0]
    conn.close()
    return bakiye

def bakiye_guncelle(chat_id, user_id, miktar):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO kullanici_ekonomi VALUES (?, ?, ?)
                      ON CONFLICT(chat_id, user_id) DO UPDATE SET bakiye = kullanici_ekonomi.bakiye + ?''', (chat_id, user_id, miktar, miktar))
    conn.commit()
    conn.close()

def gece_modu_guncelle(chat_id, durum):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO grup_ayarlar (chat_id, gece_modu_aktif) VALUES (?, ?) ON CONFLICT(chat_id) DO UPDATE SET gece_modu_aktif = ?", (chat_id, durum, durum))
    conn.commit()
    conn.close()

def gece_modu_durum(chat_id):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("SELECT gece_modu_aktif FROM grup_ayarlar WHERE chat_id = ?", (chat_id,))
    veri = cursor.fetchone()
    conn.close()
    return veri[0] if veri else False

def dil_guncelle(chat_id, yeni_dil):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO grup_ayarlar (chat_id, dil) VALUES (?, ?) ON CONFLICT(chat_id) DO UPDATE SET dil = ?", (chat_id, yeni_dil, yeni_dil))
    conn.commit()
    conn.close()

def dil_getir(chat_id):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("SELECT dil FROM grup_ayarlar WHERE chat_id = ?", (chat_id,))
    veri = cursor.fetchone()
    conn.close()
    return veri[0] if veri else "TR"

def grup_ayar_getir(chat_id):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("SELECT reklam_filtresi, kufur_filtresi, rpg_aktif, kumar_aktif FROM grup_ayarlar WHERE chat_id = ?", (chat_id,))
    veri = cursor.fetchone()
    if not veri:
        cursor.execute("INSERT INTO grup_ayarlar (chat_id, reklam_filtresi, kufur_filtresi, rpg_aktif, kumar_aktif) VALUES (?, True, True, True, True)", (chat_id,))
        conn.commit()
        veri = (True, True, True, True)
    conn.close()
    return veri

def grup_ayar_guncelle(chat_id, sutun_adi, yeni_durum):
    conn = baglanti()
    cursor = conn.cursor()
    if sutun_adi in ["reklam_filtresi", "kufur_filtresi", "rpg_aktif", "kumar_aktif"]:
        cursor.execute(f"UPDATE grup_ayarlar SET {sutun_adi} = ? WHERE chat_id = ?", (yeni_durum, chat_id))
        conn.commit()
    conn.close()

def mesaj_logla(chat_id, user_name, mesaj):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO grup_mesaj_log (chat_id, user_name, mesaj) VALUES (?, ?, ?)", (chat_id, user_name, mesaj))
    conn.commit()
    conn.close()

def son_mesajlari_getir(chat_id):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("SELECT user_name, mesaj FROM grup_mesaj_log WHERE chat_id = ? ORDER BY tarih DESC LIMIT 150", (chat_id,))
    veriler = cursor.fetchall()
    conn.close()
    return veriler[::-1]

def en_cok_davet_edenler(chat_id):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute('''SELECT m.ad, m.username, COUNT(r.katilan) as adet FROM referanslar r 
                      JOIN mesaj_istatistik m ON r.davet_eden = m.user_id AND r.chat_id = m.chat_id 
                      WHERE r.chat_id = ? GROUP BY m.ad, m.username ORDER BY adet DESC LIMIT 10''', (chat_id,))
    veriler = cursor.fetchall()
    conn.close()
    return veriler

def rpg_karakter_getir(chat_id, user_id, varsayilan_isim):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("SELECT isim, meslek, seviye, xp, can FROM rpg_karakterler WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
    veri = cursor.fetchone()
    if not veri:
        meslekler = ["Mafya", "Siber Korsan", "Şövalye", "Fedai"]
        secilen_meslek = random.choice(meslekler)
        cursor.execute("INSERT INTO rpg_karakterler VALUES (?, ?, ?, ?, 1, 0, 100)", (chat_id, user_id, varsayilan_isim, secilen_meslek))
        conn.commit()
        veri = (varsayilan_isim, secilen_meslek, 1, 0, 100)
    conn.close()
    return veri

def rpg_karakter_guncelle(chat_id, user_id, can_degisim, xp_degisim, seviye_degisim=0):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute('''UPDATE rpg_karakterler SET can = MIN(100, MAX(0, can + ?)), xp = xp + ?, seviye = seviye + ? 
                      WHERE chat_id = ? AND user_id = ?''', (can_degisim, xp_degisim, seviye_degisim, chat_id, user_id))
    conn.commit()
    conn.close()

def en_cok_konusan_ikiliyi_bul(chat_id):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute('''
        WITH sirali_loglar AS (
            SELECT user_name, LEAD(user_name) OVER (ORDER BY tarih) as sonraki_yazar
            FROM grup_mesaj_log 
            WHERE chat_id = ?
        )
        SELECT user_name, sonraki_yazar, COUNT(*) as etkilesim_sayisi
        FROM sirali_loglar
        WHERE sonraki_yazar IS NOT NULL AND user_name != sonraki_yazar
        GROUP BY user_name, sonraki_yazar
        ORDER BY etkilesim_sayisi DESC
        LIMIT 1
    ''', (chat_id,))
    veri = cursor.fetchone()
    conn.close()
    return veri

def grup_reklam_guncelle(chat_id, reklam_metni):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("UPDATE grup_ayarlar SET grup_ozel_reklam = ? WHERE chat_id = ?", (reklam_metni, chat_id))
    conn.commit()
    conn.close()

def grup_reklam_getir(chat_id):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("SELECT grup_ozel_reklam FROM grup_ayarlar WHERE chat_id = ?", (chat_id,))
    veri = cursor.fetchone()
    conn.close()
    return veri[0] if veri and veri[0] else None

def kullanici_yetki_ayarla(chat_id, user_id, seviye):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO grup_komut_yetkileri VALUES (?, ?, ?)", (chat_id, user_id, seviye))
    conn.commit()
    conn.close()

def kullanici_yetki_kontrol(chat_id, user_id):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("SELECT komut_seviyesi FROM grup_komut_yetkileri WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
    veri = cursor.fetchone()
    conn.close()
    return veri[0] if veri else 0

def blackjack_kart_degeri(kartlar):
    toplam = 0
    as_sayisi = 0
    for kart in kartlar:
        deger = kart.split()[0]
        if deger in ["J", "Q", "K"]: toplam += 10
        elif deger == "A": as_sayisi += 1; toplam += 11
        else: toplam += int(deger)
    while toplam > 21 and as_sayisi > 0:
        toplam -= 10
        as_sayisi -= 1
    return toplam
async def start_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    ayarlar.kullanici_kaydet(user.id, user.username, user.first_name)
    dil = ayarlar.dil_getir(chat.id)
    mesaj = METINLER[dil]["start"].format(user.first_name) + "\n\n🌤️ /hava [şehir]\n💰 /doviz\n📊 /kripto\n⚽ /iddaa\n🌐 /dil\n📋 /banlist\n🛠️ /panel"
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
    if not context.args: return
    try:
        hedef_id = int(context.args)
        await chat.unban_member(user_id=hedef_id)
        ayarlar.banlanan_sil(hedef_id, chat.id)
        await update.message.reply_text(f"✅ ID: {hedef_id} engeli kaldırıldı.")
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
            f"Al-sat sinyali vermeden son 24 saati özetle. Dil/Tarz: {dil} modunda samimi arkadaş dili olsun. Sonuna YALNIZCA TR ise 'Buradaki bilgiler yatırım tavsiyesi değildir' ekle."
        )
        response = ayarlar.ai_client.models.generate_content(model='gemini-2.5-flash', contents=istemi)
        await update.message.reply_text(response.text)
    except:
        await update.message.reply_text("❌ Veri hatası kanka. Çifti doğru yazdığından emin ol (Örn: BTC, ETH).")

async def iddaa_analiz_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private": return
    if not context.args:
        await update.message.reply_text("⚠️ Kanka analiz edilecek maçları yazmadın! Örnek: `/iddaa Fenerbahçe - Galatasaray`")
        return
    mac_bilgisi = " ".join(context.args)
    klavye = [[InlineKeyboardButton("🔍 MAÇI TARA", callback_data=f"iddaa_tara_{mac_bilgisi[:40]}")]]
    await update.message.reply_text(
        f"⚽ **İDDAA MAÇ ANALİZ MASASI** ⚽\n\n🏟️ **Maç:** {mac_bilgisi}\n👤 **İsteyen:** @{update.effective_user.username}\n\n"
        f"Yapay zeka analiz motorunu çalıştırmak için aşağıdaki butona basın kanka! 👇",
        reply_markup=InlineKeyboardMarkup(klavye)
    )
async def start_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    ayarlar.kullanici_kaydet(user.id, user.username, user.first_name)
    dil = ayarlar.dil_getir(chat.id)
    mesaj = METINLER[dil]["start"].format(user.first_name) + "\n\n🌤️ /hava [şehir]\n💰 /doviz\n📊 /kripto\n⚽ /iddaa\n🌐 /dil\n📋 /banlist\n🛠️ /panel"
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
    if not context.args: return
    try:
        hedef_id = int(context.args)
        await chat.unban_member(user_id=hedef_id)
        ayarlar.banlanan_sil(hedef_id, chat.id)
        await update.message.reply_text(f"✅ ID: {hedef_id} engeli kaldırıldı.")
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
            f"Al-sat sinyali vermeden son 24 saati özetle. Dil/Tarz: {dil} modunda samimi arkadaş dili olsun. Sonuna YALNIZCA TR ise 'Buradaki bilgiler yatırım tavsiyesi değildir' ekle."
        )
        response = ayarlar.ai_client.models.generate_content(model='gemini-2.5-flash', contents=istemi)
        await update.message.reply_text(response.text)
    except:
        await update.message.reply_text("❌ Veri hatası kanka. Çifti doğru yazdığından emin ol (Örn: BTC, ETH).")

async def iddaa_analiz_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private": return
    if not context.args:
        await update.message.reply_text("⚠️ Kanka analiz edilecek maçları yazmadın! Örnek: `/iddaa Fenerbahçe - Galatasaray`")
        return
    mac_bilgisi = " ".join(context.args)
    klavye = [[InlineKeyboardButton("🔍 MAÇI TARA", callback_data=f"iddaa_tara_{mac_bilgisi[:40]}")]]
    await update.message.reply_text(
        f"⚽ **İDDAA MAÇ ANALİZ MASASI** ⚽\n\n🏟️ **Maç:** {mac_bilgisi}\n👤 **İsteyen:** @{update.effective_user.username}\n\n"
        f"Yapay zeka analiz motorunu çalıştırmak için aşağıdaki butona basın kanka! 👇",
        reply_markup=InlineKeyboardMarkup(klavye)
    )
async def rpg_profil_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private": return
    _, _, rpg_aktif, _ = ayarlar.grup_ayar_getir(chat.id)
    if not rpg_aktif:
        await update.message.reply_text("❌ Bu grupta RPG özellikleri admin tarafından kapatılmıştır kanka.")
        return
    ad, meslek, seviye, xp, can = ayarlar.rpg_karakter_getir(chat.id, user.id, user.first_name)
    m = f"🎮 **Karakter Profilin:**\n\n🎭 Sınıf: {meslek}\n🎖️ Seviye: {seviye}\n✨ XP: {xp}/{seviye*100}\n❤️ Can: %{can}"
    await update.message.reply_text(m, parse_mode="Markdown")

async def rpg_saldir_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    saldiran = update.effective_user
    if chat.type == "private" or not update.message.reply_to_message: return
    _, _, rpg_aktif, _ = ayarlar.grup_ayar_getir(chat.id)
    if not rpg_aktif:
        await update.message.reply_text("❌ Bu grupta RPG özellikleri admin tarafından kapatılmıştır kanka.")
        return
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
    _, _, _, kumar_aktif = ayarlar.grup_ayar_getir(chat.id)
    if not kumar_aktif:
        await update.message.reply_text("❌ Bu grupta kumar/casino özellikleri admin tarafından kapatılmıştır kanka.")
        return
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
    await update.message.reply_text("🔍 Yapay zeka verileri inceliyor, bekleyin...")
    try:
        bakiye = ayarlar.bakiye_getir(chat.id, hedef.id)
        ad, meslek, lvl, _, _ = ayarlar.rpg_karakter_getir(chat.id, hedef.id, hedef.first_name)
        istemi = f"Şu üyeyi eğlenceli bir psikolog gibi analiz et ve tatlıca dalga geçerek gruptaki rolünü söyle. Ad: {hedef.first_name}, KankaCoin: {bakiye}, RPG: {meslek} Seviye {lvl}."
        response = ayarlar.ai_client.models.generate_content(model='gemini-2.5-flash', contents=istemi)
        await update.message.reply_text(response.text)
    except: pass
async def eros_oku_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private": return
    if update.message.reply_to_message:
        hedef_user = update.message.reply_to_message.from_user
    elif context.args:
        hedef_username = context.args[0].replace("@", "")
        hedef_user = type('User', (object,), {'first_name': hedef_username, 'username': hedef_username, 'id': 0})()
    else: return
    if hedef_user.id == user.id: return
    ask_yuzdesi = random.randint(1, 100)
    istemi = f"Gruptaki {user.first_name}, {hedef_user.first_name} kişisine aşk oku fırlattı. Aşk uyumu %{ask_yuzdesi} çıktı. Eğlenceli, samimi kanka tarzı dalga geçen aşk falı yaz."
    try:
        response = ayarlar.ai_client.models.generate_content(model='gemini-2.5-flash', contents=istemi)
        kalp_bar = "❤️" * (ask_yuzdesi // 10) + "🖤" * (10 - (ask_yuzdesi // 10))
        await update.message.reply_text(f"💘 **EROS AŞK OKU** 💘\n\n👤 Aşık: {user.first_name}\n🎯 Hedef: {hedef_user.first_name}\n📈 Uyumluluk: %{ask_yuzdesi}\n| {kalp_bar} |\n\n{response.text}", parse_mode="Markdown")
    except: pass

async def giybet_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private": return
    await update.message.reply_text("🕵️‍♂️ Chattaki son dedikodular taranıyor kanka...")
    ikili = ayarlar.en_cok_konusan_ikiliyi_bul(chat.id)
    if not ikili:
        await update.message.reply_text("📋 Henüz yeterli dedikodu malzemesi yok kanka.")
        return
    yazar1, yazar2, etkilesim = ikili
    if etkilesim < 2:
        await update.message.reply_text("📋 Henüz yeterli dedikodu malzemesi yok kanka.")
        return
    istemi = f"Grupta son zamanlarda {yazar1} ve {yazar2} chati domine edip peş peşe {etkilesim} kez karşılıklı yazışmışlar. 'Hayırdır siz sevgili misiniz, chate oda tutun kanka' tarzı esprilerle gruptakileri coşturacak magazin gıybeti döktür."
    try:
        response = ayarlar.ai_client.models.generate_content(model='gemini-2.5-flash', contents=istemi)
        await update.message.reply_text(f"👀 **GRUPTA MAGAZİN HABERİ!** 👀\n\n🎯 Şüpheli İkili: {yazar1} 🤝 {yazar2}\n📈 Paslaşma: {etkilesim} Mesaj\n\n{response.text}", parse_mode="Markdown")
    except: pass

async def fal_bak_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private": return
    bakiye = ayarlar.bakiye_getir(chat.id, user.id)
    if bakiye < 100:
        await update.message.reply_text("❌ Kanka falcımızın eli bedava açılmıyor, en az 100 KankaCoin bakiyen olmalı!")
        return
    await update.message.reply_text(f"🔮 {user.first_name} kanka için fincanlar çevrildi, hisler taranıyor, bekle...")
    ad, meslek, lvl, _, _ = ayarlar.rpg_karakter_getir(chat.id, user.id, user.first_name)
    istemi = f"Sen gruptakilere fal bakan esprili bir falcısın. Kullanıcı adı: {user.first_name}, RPG mesleği: {meslek}, Seviyesi: {lvl}. Buna göre kanka tarzı eğlenceli, 'üç vakte kadar' gibi laflar içeren kahve falı yaz."
    try:
        response = ayarlar.ai_client.models.generate_content(model='gemini-2.5-flash', contents=istemi)
        ayarlar.bakiye_guncelle(chat.id, user.id, -100)
        await update.message.reply_text(f"🔮 **FALCINIZ GELDİ! (@{user.username})** 🔮\n✨ *Elinin körü değil, gözünün nuru falın çıktı...* (-100 KankaCoin)\n\n{response.text}", parse_mode="Markdown")
    except: pass

async def grup_paneli_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private": return
    uye = await chat.get_member(update.effective_user.id)
    if uye.status not in ["creator", "administrator"] and update.effective_user.id != ayarlar.BOT_SAHIBI_ID: return
    reklam, kufur, rpg, kumar = ayarlar.grup_ayar_getir(chat.id)
    r_emo = "🟢 AÇIK" if reklam else "🔴 KAPALI"
    k_emo = "🟢 AÇIK" if kufur else "🔴 KAPALI"
    rpg_emo = "🟢 AÇIK" if rpg else "🔴 KAPALI"
    kmr_emo = "🟢 AÇIK" if kumar else "🔴 KAPALI"
    klavye = [
        [InlineKeyboardButton(f"🔗 Reklam Engel: {r_emo}", callback_data="panel_reklam_filtresi")],
        [InlineKeyboardButton(f"🤬 Küfür Engel: {k_emo}", callback_data="panel_kufur_filtresi")],
        [InlineKeyboardButton(f"⚔️ RPG Oyunu: {rpg_emo}", callback_data="panel_rpg_aktif")],
        [InlineKeyboardButton(f"🎰 Kumar/Casino: {kmr_emo}", callback_data="panel_kumar_aktif")],
        [InlineKeyboardButton("📢 Grubun Özel Reklamını Ayarla", callback_data="panel_grup_reklam")],
        [InlineKeyboardButton("🔑 Komut İzinlerini / Yetkileri Ayarla", callback_data="panel_yetki_menusu")],
        [InlineKeyboardButton("❌ Paneli Kapat", callback_data="panel_kapat")]
    ]
    await update.message.reply_text(f"🛠️ **{chat.title} YÖNETİM PANELİ** 🛠️\n\nBot özelliklerini buradan şekillendirebilirsin kanka! 👇", reply_markup=InlineKeyboardMarkup(klavye))

async def grup_reklam_ayarla_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private": return
    uye = await chat.get_member(update.effective_user.id)
    if uye.status not in ["creator", "administrator"] and update.effective_user.id != ayarlar.BOT_SAHIBI_ID: return
    if not context.args:
        await update.message.reply_text("⚠️ Kanka reklam metnini yazmadın! Örnek: `/reklamayarla t.me/link`")
        return
    yeni_reklam = " ".join(context.args)
    ayarlar.grup_reklam_guncelle(chat.id, yeni_reklam)
    await update.message.reply_text("📢 Grubun özel reklamı başarıyla kaydedildi kanka!")

async def yetki_ver_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private" or not update.message.reply_to_message: return
    uye = await chat.get_member(update.effective_user.id)
    if uye.status != "creator" and update.effective_user.id != ayarlar.BOT_SAHIBI_ID: return
    if not context.args: return
    try:
        seviye = int(context.args[0])
        hedef_user = update.message.reply_to_message.from_user
        ayarlar.kullanici_yetki_ayarla(chat.id, hedef_user.id, seviye)
        await update.message.reply_text(f"✅ @{hedef_user.username} Seviye {seviye} yetkilisi yapıldı!")
    except: pass
