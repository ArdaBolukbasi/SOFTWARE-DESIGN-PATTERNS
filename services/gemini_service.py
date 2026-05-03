"""
gemini_service.py — Google Gemini AI Analiz Servisi
======================================================
Bu modül, Plaid'den çekilen ham banka işlem verilerini Google Gemini
yapay zeka modeline gönderip akıllı finansal analiz yaptırır.

Gemini API'den İstenen Görevler:
    1. Harcamaları firma adına göre Türkçe kategorilere ayırmak
    2. Toplam harcamayı hesaplamak
    3. Her kategorinin toplam harcama içindeki yüzdesini bulmak
    4. Kişiselleştirilmiş Türkçe finansal tavsiye üretmek

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
    """
    Google Gemini AI ile harcama analizi yapan servis sınıfı.

    Ham banka işlem verilerini alır, yapılandırılmış bir prompt ile
    Gemini modeline gönderir ve kategorize edilmiş analiz sonucu döner.

    Attributes:
        _client: Google GenAI istemcisi.
        _model: Kullanılacak Gemini model adı.
    """

    def __init__(self) -> None:
        """
        Gemini API istemcisini yapılandırır.

        API anahtarı config.py'deki GEMINI_API_KEY değişkeninden okunur.
        """
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self._model = settings.GEMINI_MODEL

    def _build_prompt(self, transactions: list[dict]) -> str:
        """
        Gemini'ye gönderilecek analiz promptunu oluşturur.

        Prompt, Gemini'den yapılandırılmış JSON çıktı üretmesini
        ve Türkçe finansal tavsiye yazmasını ister.

        Args:
            transactions: Plaid'den çekilen ham işlem listesi.
                Her işlem: {"name", "merchant_name", "amount", "date", "category"}

        Returns:
            str: Gemini'ye gönderilecek tam prompt metni.
        """
        transactions_json = json.dumps(transactions, ensure_ascii=False, indent=2)

        prompt = f"""
Sen bir kişisel finans uzmanısın. Aşağıda bir kullanıcının banka hesabından çekilen
harcama işlemleri listesi JSON formatında verilmiştir.

Bu verileri analiz ederek aşağıdaki görevleri yerine getir:

## GÖREV 1: Kategorize Etme
Her harcamayı, firma/yer adına bakarak aşağıdaki Türkçe kategorilerden birine ata:
- "Yeme & İçme" (restoranlar, kafeler, market gıda alımları)
- "Ulaşım" (taksi, otobüs, benzin, otopark, uçak bileti)
- "Fatura" (elektrik, su, internet, telefon, doğalgaz)
- "Alışveriş" (giyim, elektronik, ev eşyası, kozmetik)
- "Eğlence" (sinema, konser, oyun, spor, hobi)
- "Sağlık" (eczane, doktor, hastane)
- "Diğer" (yukarıdakilere uymayan)

## GÖREV 2: İstatistik Hesaplama
- Toplam harcama tutarını hesapla.
- Her kategorinin toplam harcama içindeki yüzdesini hesapla (virgülden sonra 1 basamak).
- Her kategorideki işlem sayısını belirt.

## GÖREV 3: Kişiselleştirilmiş Tavsiye
Kullanıcının harcama alışkanlıklarını değerlendirerek yapıcı, kişiselleştirilmiş
bir finansal tavsiye metni yaz. Tavsiye Türkçe olmalı ve şunları içermeli:
- En çok harcama yapılan kategoriye dikkat çekmek
- Tasarruf önerileri sunmak
- Pozitif ve motive edici bir dil kullanmak

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
    "advice": "<turkce_tavsiye_metni>"
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

        # Gemini'ye istek gönder — JSON çıktı formatı zorunlu kıl
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3,  # Düşük sıcaklık → daha tutarlı çıktı
            ),
        )

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

        Args:
            transactions: İşlem listesi.

        Returns:
            dict: Basitleştirilmiş analiz sonucu.
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
