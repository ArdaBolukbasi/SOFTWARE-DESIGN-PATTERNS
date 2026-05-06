"""
main.py — AI Budget Tracker FastAPI Uygulama Giriş Noktası
==============================================================
Bu dosya, uygulamanın ana giriş noktasıdır. FastAPI uygulamasını
oluşturur, CORS middleware'ini yapılandırır ve router'ları dahil eder.

Çalıştırma:
    uvicorn main:app --reload

Swagger UI:
    http://localhost:8000/docs

ReDoc:
    http://localhost:8000/redoc

Mimari Özet:
    ┌─────────────────────────────────────────────────────────────┐
    │                      main.py (FastAPI)                      │
    │                                                             │
    │  ┌─────────────────┐     ┌──────────────────────────────┐  │
    │  │ /health          │     │ /api/analyze-spending        │  │
    │  │ Health Check     │     │ Ana Pipeline Endpoint'i      │  │
    │  └─────────────────┘     └──────────┬───────────────────┘  │
    │                                      │                      │
    │              ┌───────────────────────┼──────────────┐       │
    │              ▼                       ▼              ▼       │
    │  ┌──────────────────┐  ┌───────────────┐  ┌────────────┐  │
    │  │  PlaidService     │  │ GeminiService │  │ FirebaseDB │  │
    │  │  (Banka Verisi)   │  │ (AI Analiz)   │  │ (Singleton)│  │
    │  └──────────────────┘  └───────────────┘  └────────────┘  │
    │                              │                              │
    │                              ▼                              │
    │                   ┌──────────────────┐                     │
    │                   │  ExpenseFactory   │                     │
    │                   │  (Factory Pattern)│                     │
    │                   └──────────────────┘                     │
    └─────────────────────────────────────────────────────────────┘
"""

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers.spending import router as spending_router
from routers.user import router as user_router

# ============================================================
# FastAPI Uygulama Oluşturma
# ============================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI Budget Tracker — Yapay zeka destekli kişisel finans analiz API'si. "
        "Plaid ile banka verilerini çeker, Google Gemini AI ile analiz eder, "
        "Firebase Firestore'a kaydeder. "
        "Singleton ve Factory tasarım kalıpları kullanılmıştır."
    ),
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc
    openapi_url="/openapi.json",
)

# ============================================================
# CORS Middleware — Frontend erişimi için
# ============================================================
# Frontend farklı bir port/domain'de çalıştığı için CORS gerekli.
# Geliştirme ortamında tüm originlere izin verilir.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Tüm originlere izin ver (geliştirme)
    allow_credentials=True,
    allow_methods=["*"],           # Tüm HTTP metotlarına izin ver
    allow_headers=["*"],           # Tüm header'lara izin ver
)

# ============================================================
# Router'ları Dahil Et
# ============================================================

app.include_router(spending_router)
app.include_router(user_router)

# ============================================================
# Kök (Root) Endpoint'ler
# ============================================================


@app.get("/", tags=["Root"])
async def root() -> dict:
    """
    API kök endpoint'i — Hoş geldiniz mesajı ve temel bilgiler.

    Frontend veya geliştiriciler için API'nin aktif olduğunu
    doğrulayan basit bir endpoint.

    Returns:
        dict: API adı, versiyonu ve dokümantasyon bağlantıları.
    """
    return {
        "message": f"🚀 {settings.APP_NAME} API'sine hoş geldiniz!",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "register_user": "POST /api/register-user",
            "analyze_spending": "GET /api/analyze-spending?user_id=xxx&period=month",
            "categories": "GET /api/categories",
            "health": "GET /health",
        },
    }


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """
    Sağlık kontrolü (Health Check) endpoint'i.

    Uygulamanın çalışır durumda olduğunu doğrular.
    Load balancer'lar ve monitoring araçları tarafından kullanılır.

    Returns:
        dict: Uygulama durumu ve zaman damgası.
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# Uygulama Başlangıç/Bitiş Olayları
# ============================================================


@app.on_event("startup")
async def startup_event() -> None:
    """
    Uygulama başladığında çalışan olay işleyicisi.

    ASCII banner ve yapılandırma bilgilerini konsola yazdırır.
    """
    banner = """
    ╔══════════════════════════════════════════════════════╗
    ║                🏦  BudgerAI  🏦                       ║
    ║          AI Powered Finance API                      ║
    ╠══════════════════════════════════════════════════════╣
    ║  Framework  : FastAPI                                ║
    ║  Database   : Firebase Firestore (Singleton)         ║
    ║  Bank API   : Plaid Sandbox                          ║
    ║  AI Engine  : Google Gemini                          ║
    ║  Patterns   : Singleton + Factory                    ║
    ╠══════════════════════════════════════════════════════╣
    ║  Swagger UI : http://localhost:8000/docs              ║
    ║  ReDoc      : http://localhost:8000/redoc             ║
    ╚══════════════════════════════════════════════════════╝
    """
    print(banner)

    # Konfigürasyon durumunu kontrol et
    checks = {
        "Plaid Client ID": bool(settings.PLAID_CLIENT_ID),
        "Plaid Secret": bool(settings.PLAID_SECRET),
        "Gemini API Key": bool(settings.GEMINI_API_KEY),
        "Firebase Creds": bool(settings.FIREBASE_CREDENTIALS_PATH),
    }

    print("  🔧 Konfigürasyon Durumu:")
    for key, ok in checks.items():
        status = "✅" if ok else "❌ EKSIK"
        print(f"     {status}  {key}")
    print()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """
    Uygulama kapanırken çalışan olay işleyicisi.
    Temizlik işlemleri burada yapılabilir.
    """
    print("\n👋 AI Budget Tracker kapatılıyor...")
