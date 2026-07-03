import logging
import sqlite3
import random
import datetime

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==========================================
# 🔐 AYARLAR VE ŞİFRELER (Buraları Doldur)
# ==========================================
TELEGRAM_TOKEN = "BURAYA_BOTFATHER_TOKENINI_YAZ"
GEMINI_API_KEY = "BURAYA_GEMINI_API_KEY_YAZ"
BOT_SAHIBI_ID = 123456789  # Kendi sayısal Telegram ID'n
IBAN_BILGISI = "TR00 1234 5678 9012 3456 7890"
ALICI_ADI = "Adın Soyadın"

# RAM Üzerinde Tutulacak Geçici Sözlükler
BLACKJACK_OYUNLAR = {}
KULLANICI_TAKIP = {}

def baglanti():
    # PostgreSQL / Neon entegrasyonu için burayı psycopg2 bağlantısına çevirebilirsin kanka.
    # Şimdilik lokal testlerin ve Render kurulumun sorunsuz çalışsın diye SQLite standartlarındadır.
    return sqlite3.connect("bot_data.db")

def veritabani_kur():
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS kullanicilar 
                      (user_id BIGINT PRIMARY KEY, username TEXT, ad TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS yasakli_kelimeler 
                      (kelime TEXT PRIMARY KEY)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS banlananlar 
                      (user_id BIGINT, username TEXT, chat_id BIGINT, tarih TEXT, PRIMARY KEY (user_id, chat_id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS onayli_gruplar 
                      (chat_id BIGINT PRIMARY KEY, grup_adi TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS mesaj_istatistik
                      (chat_id BIGINT, user_id BIGINT, username TEXT, ad TEXT, mesaj_sayisi INTEGER, PRIMARY KEY (chat_id, user_id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS kullanici_ekonomi 
                      (chat_id BIGINT, user_id BIGINT, bakiye INTEGER DEFAULT 1000, PRIMARY KEY (chat_id, user_id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS grup_ayarlar 
                      (chat_id BIGINT PRIMARY KEY, gece_modu_aktif BOOLEAN DEFAULT FALSE, dil TEXT DEFAULT 'TR',
                       reklam_filtresi BOOLEAN DEFAULT TRUE, kufur_filtresi BOOLEAN DEFAULT TRUE,
                       rpg_aktif BOOLEAN DEFAULT TRUE, kumar_aktif BOOLEAN DEFAULT TRUE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS grup_mesaj_log 
                      (chat_id BIGINT, user_name TEXT, mesaj TEXT, tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS referanslar 
                      (chat_id BIGINT, davet_eden BIGINT, katilan BIGINT PRIMARY KEY)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS rpg_karakterler 
                      (chat_id BIGINT, user_id BIGINT, isim TEXT, meslek TEXT, seviye INTEGER DEFAULT 1, xp INTEGER DEFAULT 0, can INTEGER DEFAULT 100, PRIMARY KEY (chat_id, user_id))''')
    conn.commit()
    conn.close()

def kullanici_kaydet(user_id, username, ad):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO kullanicilar VALUES (?, ?, ?)", (user_id, username, ad))
    conn.commit()
    conn.close()
def yasakli_ekle(kelime):
    conn = baglanti()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO yasakli_kelimeler VALUES (?)", (kelime.lower().strip(),))
        conn.commit()
        durum = True
    except: durum = False
    conn.close()
    return durum

def yasakli_sil(kelime):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM yasakli_kelimeler WHERE kelime = ?", (kelime.lower().strip(),))
    silindi = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return silindi

def yasakli_listesi_getir():
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("SELECT kelime FROM yasakli_kelimeler")
    kelimeler = [row for row in cursor.fetchall()]
    conn.close()
    return kelimeler

def banlanan_kaydet(user_id, username, chat_id, tarih):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO banlananlar VALUES (?, ?, ?, ?)", (user_id, username, chat_id, tarih))
    conn.commit()
    conn.close()

def banlanan_sil(user_id, chat_id):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM banlananlar WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
    silindi = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return silindi

def banlanan_listesi_getir(chat_id):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, tarih FROM banlananlar WHERE chat_id = ?", (chat_id,))
    veriler = cursor.fetchall()
    conn.close()
    return veriler

def grup_onayla(chat_id, grup_adi="Bilinmeyen Grup"):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO onayli_gruplar VALUES (?, ?)", (chat_id, grup_adi))
    conn.commit()
    conn.close()

def grup_sil(chat_id):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM onayli_gruplar WHERE chat_id = ?", (chat_id,))
    silindi = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return silindi

def grup_onayli_mi(chat_id):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM onayli_gruplar WHERE chat_id = ?", (chat_id,))
    veri = cursor.fetchone()
    conn.close()
    return veri is not None

def mesaj_sayisi_arttir(chat_id, user_id, username, ad):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO mesaj_istatistik VALUES (?, ?, ?, ?, 1)
                      ON CONFLICT(chat_id, user_id) DO UPDATE SET 
                      mesaj_sayisi = mesaj_istatistik.mesaj_sayisi + 1, username = ?, ad = ?''', (chat_id, user_id, username, ad, username, ad))
    conn.commit()
    conn.close()

def en_aktifleri_getir(chat_id):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("SELECT ad, username, mesaj_sayisi FROM mesaj_istatistik WHERE chat_id = ? ORDER BY mesaj_sayisi DESC LIMIT 10", (chat_id,))
    veriler = cursor.fetchall()
    conn.close()
    return veriler

def bakiye_getir(chat_id, user_id):
    conn = baglanti()
    cursor = conn.cursor()
    cursor.execute("SELECT bakiye FROM kullanici_ekonomi WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
    veri = cursor.fetchone()
    if not veri:
        cursor.execute("INSERT OR IGNORE INTO kullanici_ekonomi VALUES (?, ?, 1000)", (chat_id, user_id))
        conn.commit()
        bakiye = 1000
    else: bakiye = veri
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
    return veri if veri else False

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
    return veri if veri else "TR"

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

def blackjack_kart_degeri(kartlar):
    toplam = 0
    as_sayisi = 0
    for kart in kartlar:
        deger = kart.split()
        if deger in ["J", "Q", "K"]: toplam += 10
        elif deger == "A": as_sayisi += 1; toplam += 11
        else: toplam += int(deger)
    while toplam > 21 and as_sayisi > 0:
        toplam -= 10
        as_sayisi -= 1
    return toplam
