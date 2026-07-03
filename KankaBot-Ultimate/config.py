from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID"))

IBAN = os.getenv("IBAN")

ALICI = os.getenv("ALICI")
