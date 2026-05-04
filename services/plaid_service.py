"""
plaid_service.py — Plaid Sandbox API Entegrasyonu
====================================================
Bu modül, Plaid Sandbox ortamına bağlanarak kullanıcının banka
işlemlerini (transaction) çeker.

Sandbox Modu:
- Gerçek banka hesabı gerekmez.
- Plaid'in test verileri (sahte işlemler) kullanılır.
- institution_id: "ins_109508" (Sandbox test bankası)

Akış:
    1. sandbox/public_token/create → Test public token üretilir
    2. item/public_token/exchange → Access token'a çevrilir
    3. transactions/get → Belirli tarih aralığındaki işlemler çekilir

Kullanım:
    from services.plaid_service import PlaidService

    plaid = PlaidService()
    transactions = plaid.get_transactions(period="month")
    # → [{"name": "Starbucks", "amount": 4.50, "date": "2026-04-28", ...}, ...]
"""

from datetime import datetime, timedelta
from typing import Any
import time

import plaid
from plaid.api import plaid_api
from plaid.model.sandbox_public_token_create_request import (
    SandboxPublicTokenCreateRequest,
)
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import (
    TransactionsGetRequestOptions,
)
from plaid.model.products import Products
from plaid.model.country_code import CountryCode

from config import settings


class PlaidService:
    """
    Plaid API ile banka işlemlerini çeken servis sınıfı.

    Sandbox ortamında çalışarak gerçekçi test verileri sağlar.
    Frontend entegrasyonu gerekmeden doğrudan API üzerinden
    token oluşturma ve işlem çekme işlemlerini yönetir.

    Attributes:
        _client: Plaid API istemcisi.
        _access_token: Sandbox erişim token'ı (lazy initialization).
        _is_sandbox_mode: Sandbox/mock modunda mı çalışıyor.
    """

    # Sandbox test bankası institution ID'si
    SANDBOX_INSTITUTION_ID = "ins_109508"

    def __init__(self, access_token: str | None = None) -> None:
        """
        Plaid API istemcisini yapılandırır.

        Args:
            access_token: Opsiyonel. Kullanıcının Firebase'de kayıtlı
                          Plaid access_token'ı. Verilirse doğrudan kullanılır,
                          verilmezse Sandbox token oluşturulur.
        """
        configuration = plaid.Configuration(
            host=plaid.Environment.Sandbox,
            api_key={
                "clientId": settings.PLAID_CLIENT_ID,
                "secret": settings.PLAID_SECRET,
            },
        )
        api_client = plaid.ApiClient(configuration)
        self._client = plaid_api.PlaidApi(api_client)
        self._access_token: str | None = access_token
        self._is_sandbox_mode: bool = access_token is None

    @property
    def is_sandbox_mode(self) -> bool:
        """Sandbox (mock) modunda mı çalışıyor."""
        return self._is_sandbox_mode

    def get_mock_transactions(self) -> list[dict[str, Any]]:
        """
        Sandbox mock verileri döner — access_token olmadan çalışır.

        Kullanıcı henüz Plaid Link ile bankasını bağlamamışsa,
        bu metod doğrudan çağrılarak mock veriler üretilir.
        Plaid API'ye hiç istek atmaz.

        Returns:
            list[dict]: 6 adet gerçekçi sahte banka işlemi.
        """
        print("🔄 Sandbox modu aktif → Mock veriler üretiliyor (Plaid API atlanıyor)...")
        mock_data = self._get_fallback_transactions()
        print(f"📊 {len(mock_data)} sahte işlem üretildi.")
        return mock_data

    def _create_sandbox_token(self) -> str:
        """
        Sandbox ortamında test amaçlı bir public token oluşturur.

        Bu token, gerçek bir kullanıcının Plaid Link üzerinden
        banka hesabını bağlamasını simüle eder.

        Returns:
            str: Sandbox public token.
        """
        request = SandboxPublicTokenCreateRequest(
            institution_id=self.SANDBOX_INSTITUTION_ID,
            initial_products=[Products("transactions")],
        )
        response = self._client.sandbox_public_token_create(request)
        return response["public_token"]

    def _exchange_token(self, public_token: str) -> str:
        """
        Public token'ı kalıcı bir access token'a çevirir.

        Access token, kullanıcının banka hesabına erişim için
        kullanılır ve güvenli bir şekilde saklanmalıdır.

        Args:
            public_token: Plaid Link veya Sandbox'tan alınan public token.

        Returns:
            str: Kalıcı access token.
        """
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = self._client.item_public_token_exchange(request)
        return response["access_token"]

    def _ensure_access_token(self) -> None:
        """
        Access token'ın mevcut olduğundan emin olur.

        Lazy initialization: Token sadece ilk ihtiyaç duyulduğunda
        oluşturulur. Sonraki çağrılarda mevcut token kullanılır.
        """
        if self._access_token is None:
            print("🔑 Plaid Sandbox token oluşturuluyor...")
            public_token = self._create_sandbox_token()
            self._access_token = self._exchange_token(public_token)
            print("✅ Plaid access token başarıyla alındı.")

    def _get_fallback_transactions(self) -> list[dict[str, Any]]:
        """
        Güvenlik Ağı (Fallback) — Plaid boş döndüğünde devreye giren sahte veri.

        Plaid Sandbox bazen yeni oluşturulan test hesapları için boş işlem
        listesi döner. Bu durumda Gemini'nin analiz yapabilmesi ve pipeline'ın
        uçtan uca test edilebilmesi için gerçekçi sahte işlemler üretilir.

        Returns:
            list[dict]: 6 adet gerçekçi sahte banka işlemi.
        """
        today = datetime.now()
        return [
            {
                "name": "STARBUCKS COFFEE",
                "merchant_name": "Starbucks",
                "amount": 145.50,
                "date": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
                "category": ["Food and Drink", "Coffee Shop"],
            },
            {
                "name": "MIGROS MARKET",
                "merchant_name": "Migros",
                "amount": 892.30,
                "date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
                "category": ["Food and Drink", "Groceries"],
            },
            {
                "name": "UBER TRIP",
                "merchant_name": "Uber",
                "amount": 67.80,
                "date": (today - timedelta(days=3)).strftime("%Y-%m-%d"),
                "category": ["Transportation", "Ride Share"],
            },
            {
                "name": "NETFLIX.COM",
                "merchant_name": "Netflix",
                "amount": 129.99,
                "date": (today - timedelta(days=5)).strftime("%Y-%m-%d"),
                "category": ["Entertainment", "Streaming"],
            },
            {
                "name": "VODAFONE FATURA",
                "merchant_name": "Vodafone",
                "amount": 350.00,
                "date": (today - timedelta(days=7)).strftime("%Y-%m-%d"),
                "category": ["Utilities", "Phone Bill"],
            },
            {
                "name": "GRATIS KOZMETIK",
                "merchant_name": "Gratis",
                "amount": 215.75,
                "date": (today - timedelta(days=4)).strftime("%Y-%m-%d"),
                "category": ["Shopping", "Personal Care"],
            },
        ]

    def get_transactions(self, period: str = "month") -> list[dict[str, Any]]:
        """
        Belirtilen döneme ait banka işlemlerini Plaid'den çeker.

        Plaid Transactions Get API (/transactions/get) kullanılarak
        belirli bir tarih aralığındaki işlemler çekilir. Bu endpoint,
        Sandbox ortamında historical (geçmiş) test verilerini döner.

        NOT: Eski /transactions/sync endpoint'i yeni oluşturulan
        sandbox hesaplarında boş liste döndürüyordu. /transactions/get
        ise start_date/end_date parametreleri ile geçmiş verileri
        zorla çekebilir.

        Güvenlik Ağı: Plaid boş liste döndürürse veya bir hata oluşursa,
        otomatik olarak sahte (mock) veriler devreye girer.

        Args:
            period: İşlem dönemi. "week" (son 7 gün) veya "month" (son 30 gün).

        Returns:
            list[dict]: İşlem listesi. Her işlem şu formatta:
                {
                    "name": "Starbucks",
                    "merchant_name": "Starbucks",
                    "amount": 4.50,
                    "date": "2026-04-28",
                    "category": ["Food and Drink", "Restaurants"]
                }
        """
        processed = []

        try:
            self._ensure_access_token()

            # Dönem filtresine göre tarih aralığı belirle
            end_date = datetime.now().date()

            if period == "week":
                start_date = end_date - timedelta(days=7)
            else:  # month — 90 gün geriye git, sandbox'ın tüm historical verisini al
                start_date = end_date - timedelta(days=90)

            print(f"   📅 Tarih aralığı: {start_date} → {end_date}")

            # /transactions/get endpoint'ini kullan (tarih aralığı destekler)
            # Sandbox'ta yeni oluşturulan item'lar PRODUCT_NOT_READY hatası
            # verebilir. Bu durumda birkaç saniye bekleyip tekrar deneriz.
            max_retries = 3
            retry_wait = 5  # saniye

            raw_transactions = []
            total_available = 0

            for attempt in range(1, max_retries + 1):
                try:
                    request = TransactionsGetRequest(
                        access_token=self._access_token,
                        start_date=start_date,
                        end_date=end_date,
                        options=TransactionsGetRequestOptions(
                            count=100,
                            offset=0,
                        ),
                    )
                    response = self._client.transactions_get(request)

                    raw_transactions = response.get("transactions", [])
                    total_available = response.get("total_transactions", 0)
                    print(f"   📦 Plaid toplam işlem: {total_available}, çekilen: {len(raw_transactions)}")
                    break  # Başarılı, döngüden çık

                except plaid.ApiException as api_err:
                    error_body = api_err.body if hasattr(api_err, "body") else str(api_err)
                    if "PRODUCT_NOT_READY" in str(error_body) and attempt < max_retries:
                        print(f"   ⏳ Ürün henüz hazır değil (deneme {attempt}/{max_retries}), {retry_wait}s bekleniyor...")
                        time.sleep(retry_wait)
                    else:
                        raise  # Son denemede veya farklı hatada yukarı fırlat

            # İşlemleri standart formata dönüştür
            for txn in raw_transactions:
                # Plaid transaction nesnesinden gerekli alanları çıkar
                txn_date = txn.get("date")

                # date alanı datetime.date veya string olabilir
                if hasattr(txn_date, "isoformat"):
                    txn_date_str = txn_date.isoformat()
                else:
                    txn_date_str = str(txn_date)

                processed.append(
                    {
                        "name": txn.get("name", "Bilinmeyen"),
                        "merchant_name": txn.get("merchant_name")
                        or txn.get("name", "Bilinmeyen"),
                        "amount": abs(float(txn.get("amount", 0))),
                        "date": txn_date_str,
                        "category": txn.get("category", []),
                    }
                )

        except Exception as e:
            print(f"⚠️  Plaid API hatası: {e}")
            print("   Fallback verilere geçiliyor...")

        # ── Güvenlik Ağı (Fallback) ──────────────────────────────
        # Plaid boş döndüyse veya hata oluştuysa mock data devreye girer
        if not processed:
            print("🔄 Plaid boş liste döndü → Fallback (mock) veriler devreye giriyor...")
            processed = self._get_fallback_transactions()
            print(f"📊 Fallback'ten {len(processed)} sahte işlem üretildi (dönem: {period}).")
        else:
            print(f"📊 Plaid'den {len(processed)} GERÇEK sandbox işlem çekildi (dönem: {period}).")

        return processed
