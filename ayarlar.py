import logging
import sqlite3
from google import genai

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- KENDİ BİLGİLERİNİ BURAYA YAZ ---
TELEGRAM_TOKEN = "BURAYA_BOTFATHER_TOKENINI_YAZ"
GEMINI_API_KEY = "BURAYA_GEMINI_API_KEY_YAZ"
BOT_SAHIBI_ID = 123456789  
IBAN_BILGISI = "TR00 1234 5678 9012 3456 7890"
ALICI_ADI = "Adın Soyadın"

ai_client = genai.Client(api_key=GEMINI_API_KEY)
KULLANICI_TAKIP = {}

def veritabani_kur():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS kullanicilar (user_id INTEGER PRIMARY KEY, username TEXT, ad TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS yasakli_kelimeler (kelime TEXT PRIMARY KEY)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS banlananlar (user_id INTEGER, username TEXT, chat_id INTEGER, tarih TEXT, PRIMARY KEY (user_id, chat_id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS onayli_gruplar (chat_id INTEGER PRIMARY KEY, grup_adi TEXT)''')
    conn.commit()
    conn.close()

def kullanici_kaydet(user_id, username, ad):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO kullanicilar VALUES (?, ?, ?)", (user_id, username, ad))
    conn.commit()
    conn.close()

def yasakli_ekle(kelime):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO yasakli_kelimeler VALUES (?)", (kelime.lower().strip(),))
        conn.commit()
        durum = True
    except sqlite3.IntegrityError:
        durum = False
    conn.close()
    return durum

def yasakli_sil(kelime):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM yasakli_kelimeler WHERE kelime = ?", (kelime.lower().strip(),))
    silindi = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return silindi

def yasakli_listesi_getir():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT kelime FROM yasakli_kelimeler")
    kelimeler = [row for row in cursor.fetchall()]
    conn.close()
    return kelimeler

def banlanan_kaydet(user_id, username, chat_id, tarih):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO banlananlar VALUES (?, ?, ?, ?)", (user_id, username, chat_id, tarih))
    conn.commit()
    conn.close()

def banlanan_sil(user_id, chat_id):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM banlananlar WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
    silindi = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return silindi

def banlanan_listesi_getir(chat_id):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, tarih FROM banlananlar WHERE chat_id = ?", (chat_id,))
    veriler = cursor.fetchall()
    conn.close()
    return veriler

def grup_onayla(chat_id, grup_adi="Bilinmeyen Grup"):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO onayli_gruplar VALUES (?, ?)", (chat_id, grup_adi))
    conn.commit()
    conn.close()

def grup_sil(chat_id):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM onayli_gruplar WHERE chat_id = ?", (chat_id,))
    silindi = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return silindi

def grup_onayli_mi(chat_id):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM onayli_gruplar WHERE chat_id = ?", (chat_id,))
    veri = cursor.fetchone()
    conn.close()
    return veri is not None
