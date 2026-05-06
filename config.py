"""
config.py — Uygulama Konfigürasyonu
====================================
.env dosyasından ortam değişkenlerini yükler ve tip-güvenli
bir Settings nesnesi olarak uygulamanın geri kalanına sunar.

Kullanım:
    from config import settings
    print(settings.PLAID_CLIENT_ID)
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# .env dosyasını yükle (proje kök dizininden)
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """
    Uygulama ayarlarını tutan immutable (değiştirilemez) veri sınıfı.

    Tüm hassas bilgiler (API anahtarları, kimlik bilgileri) ortam
    değişkenlerinden okunur. Varsayılan değerler sadece geliştirme
    ortamı içindir.
    """

    # --- Plaid Sandbox API ---
    PLAID_CLIENT_ID: str = os.getenv("PLAID_CLIENT_ID", "")
    PLAID_SECRET: str = os.getenv("PLAID_SECRET", "")
    PLAID_ENV: str = "sandbox"  # Sandbox ortamı (test verisi)

    # --- Google Gemini API ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-2.5-flash"  # Kullanılacak model

    # --- Firebase ---
    FIREBASE_CREDENTIALS_PATH: str = os.getenv(
        "FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json"
    )

    # --- Uygulama ---
    APP_NAME: str = "BudgerAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"


# Tekil (global) settings nesnesi — her yerde import edilerek kullanılır
settings = Settings()
