"""
spending.py — Harcama Analizi API Endpoint'i
================================================
Bu modül, AI Budget Tracker'ın ana endpoint'ini içerir:

    GET /api/analyze-spending?user_id=xxx&period=week|month

Bu endpoint çağrıldığında tam Data Pipeline çalışır:
    1. Plaid Sandbox'tan banka işlemleri çekilir
    2. Gemini AI ile işlemler kategorize edilir ve analiz edilir
    3. Factory Pattern ile Expense nesneleri üretilir
    4. Singleton Firebase bağlantısı ile Firestore'a kaydedilir
    5. Frontend'e yapılandırılmış JSON yanıt döndürülür
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from database.firebase_client import FirebaseDB
from models.expense import ExpenseFactory
from services.plaid_service import PlaidService
from services.gemini_service import GeminiService

# FastAPI router tanımı
router = APIRouter(
    prefix="/api",
    tags=["Spending Analysis"],
    responses={
        200: {"description": "Analiz başarıyla tamamlandı"},
        400: {"description": "Geçersiz parametreler"},
        500: {"description": "Sunucu hatası"},
    },
)


@router.get("/analyze-spending")
async def analyze_spending(
    user_id: str = Query(
        ...,
        description="Kullanıcı ID'si (Frontend tarafından sağlanır)",
        example="user_123",
        min_length=1,
    ),
    period: str = Query(
        default="month",
        description="Analiz dönemi: 'week' (son 7 gün) veya 'month' (son 30 gün)",
        pattern="^(week|month)$",
    ),
) -> dict[str, Any]:
    """
    Kullanıcının harcamalarını analiz eden ana endpoint.

    Bu endpoint, tam veri işleme hattını (data pipeline) çalıştırır:

    1. **Plaid API** → Sandbox'tan banka işlemlerini çeker
    2. **Gemini AI** → İşlemleri kategorize eder, istatistik hesaplar, tavsiye üretir
    3. **Factory Pattern** → Kategorize edilmiş verileri OOP nesnelerine dönüştürür
    4. **Firebase Singleton** → Sonuçları Firestore'a kaydeder
    5. **HTTP Response** → Frontend'e JSON formatında yanıt döner

    Args:
        user_id: Kullanıcıyı tanımlayan benzersiz ID.
        period: Analiz dönemi ("week" veya "month").

    Returns:
        dict: Analiz sonuçları:
            - status: "success"
            - data:
                - user_id, period, total_spending, currency
                - categories: [{name, icon, total, percentage, transaction_count}, ...]
                - ai_advice: Türkçe finansal tavsiye
                - analyzed_at: ISO 8601 zaman damgası

    Raises:
        HTTPException 400: Geçersiz period parametresi.
        HTTPException 500: Pipeline hatası (Plaid, Gemini veya Firebase).
    """
    print(f"\n{'='*60}")
    print(f"📍 Yeni analiz isteği: user_id={user_id}, period={period}")
    print(f"{'='*60}")

    try:
        # ============================================================
        # ADIM 0: Kullanıcı Doğrulama (Firebase Singleton)
        # ============================================================
        print("\n👤 ADIM 0: Kullanıcı kaydı kontrol ediliyor...")

        firebase_db = FirebaseDB()

        if firebase_db.is_connected:
            user_doc = firebase_db.get_document("users", user_id)

            if user_doc:
                print(f"   ✅ Kullanıcı bulundu: {user_id}")
                print(f"   📋 Kayıt tarihi: {user_doc.get('registered_at', 'bilinmiyor')}")
            else:
                # Kullanıcı kayıtlı değilse otomatik oluştur
                print(f"   ℹ️  Kullanıcı bulunamadı, otomatik kayıt oluşturuluyor...")
                firebase_db.save_document(
                    "users",
                    {
                        "user_id": user_id,
                        "display_name": "",
                        "email": "",
                        "registered_at": datetime.now(timezone.utc).isoformat(),
                    },
                    document_id=user_id,
                )
                print(f"   ✅ Kullanıcı otomatik kaydedildi: {user_id}")
        else:
            print("   ⚠️  Firebase bağlantısı yok, kullanıcı doğrulama atlandı.")

        # ============================================================
        # ADIM 1: Plaid Sandbox'tan Banka Verisi Çekme
        # ============================================================
        # Her zaman önce Plaid Sandbox API'yi dene.
        # Sandbox token otomatik oluşturulur, gerçek sandbox verileri çekilir.
        # Sadece Plaid boş dönerse mock data devreye girer (güvenlik ağı).
        # ============================================================
        print(f"\n📥 ADIM 1: Plaid Sandbox API'den banka işlemleri çekiliyor...")

        plaid_service = PlaidService()
        raw_transactions = plaid_service.get_transactions(period=period)
        data_source = "plaid_sandbox"

        # get_transactions zaten içinde fallback var ama burada da kontrol edelim
        if raw_transactions:
            print(f"   🏦 Veri kaynağı: PLAID SANDBOX API")
        else:
            print(f"   ⚠️  Plaid boş döndü, bu olmamalı (fallback zaten devrede).")
            data_source = "mock"

        print(f"   📊 Toplam {len(raw_transactions)} işlem hazır.")

        # ============================================================
        # ADIM 2: Gemini AI ile Analiz
        # ============================================================
        print("\n🤖 ADIM 2: Gemini AI ile harcamalar analiz ediliyor...")

        gemini_service = GeminiService()
        ai_analysis = gemini_service.analyze_spending(raw_transactions)

        # ============================================================
        # ADIM 3: Factory Pattern ile Nesne Üretimi
        # ============================================================
        print("\n🏭 ADIM 3: Factory Pattern ile Expense nesneleri üretiliyor...")
        print(f"   ℹ️  Gemini {len(ai_analysis.get('categories', []))} kategori döndürdü.")

        all_expenses = []

        for category_data in ai_analysis.get("categories", []):
            category_name = category_data.get("name", "Diğer")

            for txn in category_data.get("transactions", []):
                # Factory Pattern: Kategori adına göre doğru sınıf üretilir
                expense = ExpenseFactory.create(
                    category=category_name,
                    merchant_name=txn.get("merchant_name", "Bilinmeyen"),
                    amount=float(txn.get("amount", 0)),
                    date=txn.get("date", ""),
                    original_description=txn.get("original_description", ""),
                )
                all_expenses.append(expense)

                # Her nesne üretimini logla — Factory Pattern'in çalıştığını kanıtlar
                print(
                    f"      🔨 ExpenseFactory.create(\"{category_name}\") "
                    f"→ {type(expense).__name__} | "
                    f"{expense.merchant_name} | "
                    f"${expense.amount:.2f} | "
                    f"{expense.icon}"
                )

        print(f"\n   ✅ Toplam {len(all_expenses)} adet Expense nesnesi üretildi.")

        # Üretilen nesnelerin sınıf dağılımını göster (debug)
        class_counts = {}
        for exp in all_expenses:
            cls_name = type(exp).__name__
            class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
        print("   📊 Sınıf Dağılımı:")
        for cls_name, count in class_counts.items():
            print(f"      → {cls_name}: {count} adet")

        # ============================================================
        # ADIM 4: Firebase'e Kayıt (Singleton Bağlantı)
        # ============================================================
        print("\n💾 ADIM 4: Firebase Firestore'a kaydediliyor (Singleton)...")

        # Singleton pattern ile Firebase bağlantısı alınır
        firebase_db = FirebaseDB()
        # Singleton doğrulaması — her çağrıda aynı nesne döner
        firebase_db_2 = FirebaseDB()
        print(f"   🔷 Singleton Doğrulama: FirebaseDB() is FirebaseDB() → {firebase_db is firebase_db_2}")
        print(f"   🔷 Instance ID: {id(firebase_db)}")
        print(f"   🔷 Bağlantı Durumu: {'✅ Aktif' if firebase_db.is_connected else '❌ Bağlantı Yok'}")

        if firebase_db.is_connected:
            # Her expense nesnesini dict'e çevirip Firestore'a kaydet
            expense_dicts = [exp.to_dict() for exp in all_expenses]
            collection_path = f"users/{user_id}/expenses"

            print(f"\n   📝 Firestore yazılıyor: {collection_path}")
            for i, exp_dict in enumerate(expense_dicts, 1):
                print(
                    f"      💾 [{i}/{len(expense_dicts)}] "
                    f"{exp_dict['category']} | {exp_dict['merchant_name']} | "
                    f"${exp_dict['amount']:.2f}"
                )

            saved_ids = firebase_db.save_batch(collection_path, expense_dicts)
            print(f"\n   ✅ {len(saved_ids)} kayıt Firestore'a yazıldı!")
            for doc_id in saved_ids:
                print(f"      📄 Document ID: {doc_id}")

            # Analiz özetini de ayrı bir döküman olarak kaydet
            summary_data = {
                "user_id": user_id,
                "period": period,
                "total_spending": ai_analysis.get("total_spending", 0),
                "category_count": len(ai_analysis.get("categories", [])),
                "transaction_count": len(all_expenses),
                "ai_advice": ai_analysis.get("advice", ""),
                "data_source": data_source,
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
            }
            summary_path = f"users/{user_id}/analysis_history"
            summary_id = firebase_db.save_document(summary_path, summary_data)
            print(f"\n   📊 Analiz özeti kaydedildi: {summary_path}/{summary_id}")
        else:
            print("   ⚠️  Firebase bağlantısı yok, kayıt atlandı.")

        # ============================================================
        # ADIM 5: Frontend'e Yanıt Hazırlama
        # ============================================================
        print("\n📤 ADIM 5: Frontend yanıtı hazırlanıyor...")

        # Kategorileri frontend-friendly formata dönüştür
        response_categories = []
        for cat in ai_analysis.get("categories", []):
            response_categories.append(
                {
                    "name": cat.get("name", "Diğer"),
                    "icon": _get_category_icon(cat.get("name", "Diğer")),
                    "total": round(float(cat.get("total", 0)), 2),
                    "percentage": round(float(cat.get("percentage", 0)), 1),
                    "transaction_count": int(cat.get("transaction_count", 0)),
                }
            )

        response_data = {
            "status": "success",
            "data": {
                "user_id": user_id,
                "period": period,
                "total_spending": round(
                    float(ai_analysis.get("total_spending", 0)), 2
                ),
                "currency": "USD",
                "categories": response_categories,
                "ai_advice": ai_analysis.get("advice", ""),
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
                "data_source": data_source,
            },
        }

        print(f"\n{'─'*60}")
        print(f"✅ ANALİZ TAMAMLANDI!")
        print(f"   💰 Toplam Harcama: ${response_data['data']['total_spending']}")
        print(f"   📂 Kategori Sayısı: {len(response_categories)}")
        print(f"   🧾 İşlem Sayısı: {len(all_expenses)}")
        print(f"   🎭 Veri Kaynağı: {data_source.upper()}")
        print(f"   🔷 Design Patterns: Singleton ✓ | Factory ✓")
        print(f"{'='*60}\n")

        return response_data

    except Exception as e:
        print(f"\n❌ Pipeline hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Harcama analizi sırasında bir hata oluştu: {str(e)}",
                "error_type": type(e).__name__,
            },
        )


def _get_category_icon(category_name: str) -> str:
    """
    Kategori adına göre emoji ikonunu döner.

    Factory Pattern'deki sınıflarla tutarlı ikonlar sağlar.
    Router seviyesinde yardımcı fonksiyon olarak kullanılır.

    Args:
        category_name: Türkçe kategori adı.

    Returns:
        str: Kategoriyi temsil eden emoji.
    """
    icons = {
        "Yeme & İçme": "🍔",
        "Ulaşım": "🚗",
        "Fatura": "📄",
        "Alışveriş": "🛒",
        "Eğlence": "🎬",
        "Sağlık": "💊",
        "Diğer": "📦",
    }
    return icons.get(category_name, "📦")


@router.get("/categories")
async def get_categories() -> dict[str, Any]:
    """
    Desteklenen harcama kategorilerini listeler.

    Frontend'in kategori filtresi, renk kodlaması veya ikon
    gösterimi için bu bilgilere ihtiyacı olabilir.

    Returns:
        dict: Kategori listesi:
            {
                "status": "success",
                "categories": [
                    {"name": "Yeme & İçme", "icon": "🍔", "key": "yeme_icme"},
                    ...
                ]
            }
    """
    categories = ExpenseFactory.get_supported_categories()
    return {
        "status": "success",
        "categories": categories,
    }
