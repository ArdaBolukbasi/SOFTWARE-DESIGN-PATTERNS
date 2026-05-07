"""
gemini_service.py — Google Gemini AI Analiz Servisi
======================================================
Bu modül, Plaid'den çekilen ham banka işlem verilerini Google Gemini
yapay zeka modeline gönderip akıllı finansal analiz yaptırır.

Gemini API'den İstenen Görevler:
    1. Harcamaları firma adına göre kategorilere ayırmak
    2. Toplam harcamayı hesaplamak
    3. Her kategorinin toplam harcama içindeki yüzdesini bulmak
    4. Kişiselleştirilmiş  finansal tavsiye üretmek

Kullanım:
    from services.gemini_service import GeminiService

    gemini = GeminiService()
    result = gemini.analyze_spending(transactions)
    # → {"total_spending": 4500, "categories": [...], "advice": "..."}
"""

import json
from typing import Any

from google import genai
from google.genai import types

from config import settings


class GeminiService:
 
    def __init__(self) -> None:
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self._model = settings.GEMINI_MODEL

    def _build_prompt(self, transactions: list[dict]) -> str:
        transactions_json = json.dumps(transactions, ensure_ascii=False, indent=2)

        prompt = f"""
You are a personal finance expert. Below is a list of a user's bank transactions in JSON format.

Analyze this data and perform the following tasks:

## TASK 1: Categorization
Categorize each transaction into exactly ONE of the following English categories, based on the merchant name:
- "Food & Dining" (restaurants, cafes, fast-food chains e.g., McDonald's, Starbucks, KFC, groceries)
- "Transportation" (taxi, bus, gas, parking, flights)
- "Bills & Utilities" (electricity, water, internet, phone)
- "Shopping" (clothing, electronics, home goods, cosmetics)
- "Entertainment" (movies, concerts, games, sports, hobbies)
- "Health & Wellness" (pharmacy, doctor, hospital)
- "Auto Payments" (automatic bills, subscriptions, e.g., AUTOMATIC PAYMENT)
- "Credit Card Payment" (credit card debt payments, e.g., CREDIT CARD 3333 PAYMENT)
- "Other" (anything that doesn't fit above)

## TASK 2: Calculate Statistics
- Calculate the total spending amount.
- Calculate the percentage of each category out of the total spending (1 decimal place).
- Count the number of transactions in each category.

## TASK 3: Personalized Advice
Based on the user's spending habits, write a constructive, personalized financial advice text. The advice MUST BE IN ENGLISH and include:
- Pointing out the category with the highest spending
- Offering savings recommendations
- Using a positive and motivating tone

## HARCAMA VERİLERİ:
{transactions_json}

## ÇIKTI FORMATI:
Yanıtını MUTLAKA aşağıdaki JSON formatında ver, başka hiçbir metin ekleme:

{{
    "total_spending": <toplam_tutar_sayı>,
    "categories": [
        {{
            "name": "<kategori_adı>",
            "total": <kategori_toplam_tutar>,
            "percentage": <yuzde_değeri>,
            "transaction_count": <islem_sayisi>,
            "transactions": [
                {{
                    "merchant_name": "<firma_adi>",
                    "amount": <tutar>,
                    "date": "<tarih>",
                    "original_description": "<orijinal_aciklama>"
                }}
            ]
        }}
    ],
    "advice": "<english_advice_text>"
}}
"""
        return prompt

    def analyze_spending(self, transactions: list[dict]) -> dict[str, Any]:
        """
        Harcama verilerini Gemini AI ile analiz eder.

        Ham banka işlem verilerini alır, yapılandırılmış bir prompt ile
        Gemini modeline gönderir ve kategorize edilmiş analiz sonucu döner.

        Args:
            transactions: Plaid'den çekilen işlem listesi.
                Her eleman: {"name", "merchant_name", "amount", "date", "category"}

        Returns:
            dict: Gemini'nin ürettiği analiz sonucu:
                {
                    "total_spending": 4500.00,
                    "categories": [
                        {
                            "name": "Yeme & İçme",
                            "total": 1800.00,
                            "percentage": 40.0,
                            "transaction_count": 12,
                            "transactions": [...]
                        },
                        ...
                    ],
                    "advice": "Harcamalarınızın %40'ı yeme-içmeye gidiyor..."
                }

        Raises:
            ValueError: Gemini'den geçersiz/parse edilemeyen yanıt gelirse.
            Exception: API bağlantı hatası durumunda.
        """
        if not transactions:
            return {
                "total_spending": 0,
                "categories": [],
                "advice": "Analiz edilecek harcama verisi bulunamadı.",
            }

        prompt = self._build_prompt(transactions)

        print(f"🤖 Gemini AI'ya {len(transactions)} işlem gönderiliyor...")

        import time
        max_retries = 3
        base_delay = 2

        for attempt in range(max_retries):
            try:
                # Gemini'ye istek gönder — JSON çıktı formatı zorunlu kıl
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.3,  # Düşük sıcaklık → daha tutarlı çıktı
                    ),
                )
                break  # İstek başarılı olursa döngüden çık
            except Exception as e:
                error_str = str(e)
                # 503 (Service Unavailable) veya 429 (Too Many Requests) kontrolü
                if "503" in error_str or "UNAVAILABLE" in error_str or "429" in error_str or "high demand" in error_str.lower():
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"⚠️  Gemini API yoğun (Deneme {attempt+1}/{max_retries}). {delay} saniye bekleniyor...")
                        time.sleep(delay)
                    else:
                        print(f"❌ Gemini API'ye ulaşılamadı (Max deneme: {max_retries}): {e}")
                        print("    Yedek analiz (fallback) devreye giriyor...")
                        return self._fallback_analysis(transactions)
                else:
                    print(f"❌ Gemini API beklenmeyen hata: {e}")
                    print("    Yedek analiz (fallback) devreye giriyor...")
                    return self._fallback_analysis(transactions)

        # Yanıtı parse et
        try:
            result = json.loads(response.text)
            print("✅ Gemini analizi başarıyla tamamlandı.")
            return result
        except json.JSONDecodeError as e:
            print(f"⚠️  Gemini yanıtı JSON olarak parse edilemedi: {e}")
            print(f"    Ham yanıt: {response.text[:500]}")

            # Fallback: Manuel hesaplama
            return self._fallback_analysis(transactions)

    def _fallback_analysis(self, transactions: list[dict]) -> dict[str, Any]:
        """
        Gemini başarısız olursa basit bir yedek analiz üretir.

        Kategorilendirme yapılmaz, sadece toplam hesaplanır ve
        tüm işlemler "Diğer" kategorisine atılır.
        """
        total = sum(txn.get("amount", 0) for txn in transactions)
        return {
            "total_spending": round(total, 2),
            "categories": [
                {
                    "name": "Diğer",
                    "total": round(total, 2),
                    "percentage": 100.0,
                    "transaction_count": len(transactions),
                    "transactions": [
                        {
                            "merchant_name": txn.get("merchant_name", txn.get("name", "Bilinmeyen")),
                            "amount": txn.get("amount", 0),
                            "date": txn.get("date", ""),
                            "original_description": txn.get("name", ""),
                        }
                        for txn in transactions
                    ],
                }
            ],
            "advice": (
                "Yapay zeka analizi şu anda kullanılamadığı için detaylı "
                "kategorizasyon yapılamamıştır. Toplam harcamanız "
                f"{round(total, 2)} USD olarak hesaplanmıştır."
            ),
        }
