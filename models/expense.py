"""
expense.py — Factory Pattern ile Harcama Nesneleri
=====================================================
🔷 DESIGN PATTERN: FACTORY

Bu modül, Plaid'den çekilen ve Gemini AI tarafından kategorize edilen
harcama verilerini OOP nesnelerine dönüştüren Factory Pattern'i içerir.

Neden Factory Pattern?
-----------------------
- Gemini AI'dan gelen kategori bilgisine göre doğru sınıf otomatik üretilir.
- İstemci kodu (router) hangi sınıfın üretileceğini bilmek zorunda kalmaz.
- Yeni kategori eklemek için sadece yeni bir sınıf ve registry kaydı yeterlidir.
- Her kategori kendi özel davranışlarını (ikon, açıklama) taşıyabilir.

Yapı:
    Expense (Base Class)
    ├── FoodExpense        → Yeme & İçme
    ├── TransportExpense   → Ulaşım
    ├── BillExpense        → Fatura
    ├── ShoppingExpense    → Alışveriş
    ├── EntertainmentExpense → Eğlence
    ├── HealthExpense      → Sağlık
    └── OtherExpense       → Diğer

    ExpenseFactory.create("Yeme & İçme", ...) → FoodExpense(...)

Kullanım:
    from models.expense import ExpenseFactory

    expense = ExpenseFactory.create(
        category="Yeme & İçme",
        merchant_name="Starbucks",
        amount=45.50,
        date="2026-05-01",
        original_description="STARBUCKS COFFEE"
    )

    print(expense.to_dict())    # Firestore'a kaydedilebilir sözlük
    print(expense.icon)         # 🍔
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import ClassVar


# ============================================================
# BASE CLASS — Tüm harcama türlerinin ortak atasıdır
# ============================================================


@dataclass
class Expense(ABC):
    """
    Tüm harcama türlerinin temel (abstract) sınıfı.

    Bu sınıf doğrudan örneklenemez; alt sınıflar (FoodExpense,
    TransportExpense vb.) tarafından genişletilir.

    Attributes:
        merchant_name: Harcamanın yapıldığı firma/yer adı (örn: "Starbucks").
        amount: Harcama tutarı (USD cinsinden).
        date: Harcama tarihi (YYYY-MM-DD formatında string).
        original_description: Banka ekstresindeki orijinal açıklama.
    """

    merchant_name: str
    amount: float
    date: str
    original_description: str = ""

    @property
    @abstractmethod
    def category(self) -> str:
        """Harcama kategorisi (Türkçe). Alt sınıflar tarafından tanımlanır."""
        ...

    @property
    @abstractmethod
    def icon(self) -> str:
        """Kategoriyi temsil eden emoji ikonu."""
        ...

    @property
    def category_key(self) -> str:
        """
        Kategori için URL/key-safe bir tanımlayıcı üretir.

        Returns:
            str: Küçük harfli, boşluksuz kategori anahtarı (örn: "yeme_icme").
        """
        return (
            self.category
            .lower()
            .replace(" & ", "_")
            .replace(" ", "_")
            .replace("ö", "o")
            .replace("ü", "u")
            .replace("ş", "s")
            .replace("ç", "c")
            .replace("ğ", "g")
            .replace("ı", "i")
        )

    def to_dict(self) -> dict:
        """
        Harcama nesnesini Firestore'a kaydedilebilir bir sözlüğe dönüştürür.

        Returns:
            dict: Tüm alanları içeren sözlük.
                  Örnek:
                  {
                      "category": "Yeme & İçme",
                      "category_key": "yeme_icme",
                      "icon": "🍔",
                      "merchant_name": "Starbucks",
                      "amount": 45.50,
                      "date": "2026-05-01",
                      "original_description": "STARBUCKS COFFEE"
                  }
        """
        return {
            "category": self.category,
            "category_key": self.category_key,
            "icon": self.icon,
            "merchant_name": self.merchant_name,
            "amount": self.amount,
            "date": self.date,
            "original_description": self.original_description,
        }


# ============================================================
# CONCRETE CLASSES — Somut Harcama Türleri
# ============================================================


@dataclass
class FoodExpense(Expense):
    """
    Yeme & İçme kategorisindeki harcamaları temsil eder.
    Örnek: Restoran, kafe, market yemek alışverişleri.
    """

    @property
    def category(self) -> str:
        return "Yeme & İçme"

    @property
    def icon(self) -> str:
        return "🍔"


@dataclass
class TransportExpense(Expense):
    """
    Ulaşım kategorisindeki harcamaları temsil eder.
    Örnek: Taksi, otobüs, metro, benzin, otopark.
    """

    @property
    def category(self) -> str:
        return "Ulaşım"

    @property
    def icon(self) -> str:
        return "🚗"


@dataclass
class BillExpense(Expense):
    """
    Fatura kategorisindeki harcamaları temsil eder.
    Örnek: Elektrik, su, internet, telefon, doğalgaz.
    """

    @property
    def category(self) -> str:
        return "Fatura"

    @property
    def icon(self) -> str:
        return "📄"


@dataclass
class ShoppingExpense(Expense):
    """
    Alışveriş kategorisindeki harcamaları temsil eder.
    Örnek: Giyim, elektronik, ev eşyası, kozmetik.
    """

    @property
    def category(self) -> str:
        return "Alışveriş"

    @property
    def icon(self) -> str:
        return "🛒"


@dataclass
class EntertainmentExpense(Expense):
    """
    Eğlence kategorisindeki harcamaları temsil eder.
    Örnek: Sinema, konser, oyun, hobi, spor salonu.
    """

    @property
    def category(self) -> str:
        return "Eğlence"

    @property
    def icon(self) -> str:
        return "🎬"


@dataclass
class HealthExpense(Expense):
    """
    Sağlık kategorisindeki harcamaları temsil eder.
    Örnek: Eczane, doktor, hastane, diş, göz.
    """

    @property
    def category(self) -> str:
        return "Sağlık"

    @property
    def icon(self) -> str:
        return "💊"


@dataclass
class AutoPaymentExpense(Expense):
    """
    Otomatik işlemler ve otomatik ödemeleri temsil eder.
    Örnek: AUTOMATIC PAYMENT - THANK vb.
    """

    @property
    def category(self) -> str:
        return "Otomatik İşlemler"

    @property
    def icon(self) -> str:
        return "🔄"


@dataclass
class CreditCardPaymentExpense(Expense):
    """
    Kredi kartı borç ödemelerini temsil eder.
    Örnek: CREDIT CARD 3333 PAYMENT *// vb.
    """

    @property
    def category(self) -> str:
        return "Kredi Kartı Ödeme"

    @property
    def icon(self) -> str:
        return "💳"


@dataclass
class OtherExpense(Expense):
    """
    Diğer/Sınıflandırılamayan harcamaları temsil eder.
    Yukarıdaki kategorilere uymayan harcamalar bu sınıfa düşer.
    """

    @property
    def category(self) -> str:
        return "Diğer"

    @property
    def icon(self) -> str:
        return "📦"


# ============================================================
# FACTORY CLASS — Kategori bilgisine göre doğru nesneyi üretir
# ============================================================


class ExpenseFactory:
    """
    Factory Pattern implementasyonu — Harcama Nesnesi Fabrikası.

    Gemini AI'dan dönen kategori string'ine göre uygun Expense
    alt sınıfının instance'ını üretir. İstemci kodu hangi sınıfın
    kullanılacağını bilmek zorunda değildir.

    Design Pattern:
        Factory Method — GoF Creational Patterns
        Amaç: Nesne oluşturma mantığını istemci kodundan ayırır,
        böylece yeni türler eklemek mevcut kodu bozmaz (Open/Closed Principle).

    Kullanım:
        expense = ExpenseFactory.create(
            category="Ulaşım",
            merchant_name="Uber",
            amount=75.00,
            date="2026-05-01",
            original_description="UBER TRIP"
        )

    Yeni Kategori Ekleme:
        1. Yeni bir Expense alt sınıfı oluşturun (örn: EducationExpense).
        2. _registry sözlüğüne Türkçe anahtar ile ekleyin.
        Başka hiçbir kodu değiştirmenize gerek yok!
    """

    # Kategori adı → Expense alt sınıfı eşleşme tablosu
    _registry: ClassVar[dict[str, type[Expense]]] = {
        # Yeme & İçme varyasyonları
        "yeme & içme": FoodExpense,
        "yeme ve içme": FoodExpense,
        "yeme-içme": FoodExpense,
        "gıda": FoodExpense,
        "food": FoodExpense,
        "food & drink": FoodExpense,
        "restaurant": FoodExpense,
        "restoran": FoodExpense,
        # Ulaşım varyasyonları
        "ulaşım": TransportExpense,
        "ulasim": TransportExpense,
        "transport": TransportExpense,
        "transportation": TransportExpense,
        "travel": TransportExpense,
        "seyahat": TransportExpense,
        # Fatura varyasyonları
        "fatura": BillExpense,
        "faturalar": BillExpense,
        "bills": BillExpense,
        "utilities": BillExpense,
        # Alışveriş varyasyonları
        "alışveriş": ShoppingExpense,
        "alisveris": ShoppingExpense,
        "shopping": ShoppingExpense,
        "giyim": ShoppingExpense,
        # Eğlence varyasyonları
        "eğlence": EntertainmentExpense,
        "eglence": EntertainmentExpense,
        "entertainment": EntertainmentExpense,
        # Sağlık varyasyonları
        "sağlık": HealthExpense,
        "saglik": HealthExpense,
        "health": HealthExpense,
        # Otomatik İşlemler varyasyonları
        "otomatik işlemler": AutoPaymentExpense,
        "otomatik islemler": AutoPaymentExpense,
        "otomatik ödeme": AutoPaymentExpense,
        "otomatik odeme": AutoPaymentExpense,
        "automatic payment": AutoPaymentExpense,
        # Kredi Kartı Ödeme varyasyonları
        "kredi kartı ödeme": CreditCardPaymentExpense,
        "kredi karti odeme": CreditCardPaymentExpense,
        "kredi kartı": CreditCardPaymentExpense,
        "credit card payment": CreditCardPaymentExpense,
        "credit card": CreditCardPaymentExpense,
        # Diğer
        "diğer": OtherExpense,
        "diger": OtherExpense,
        "other": OtherExpense,
    }

    @classmethod
    def create(
        cls,
        category: str,
        merchant_name: str,
        amount: float,
        date: str,
        original_description: str = "",
    ) -> Expense:
        """
        Verilen kategori adına göre uygun Expense nesnesini üretir.

        Factory Method: Kategori string'ini alır, dahili registry
        tablosundan doğru sınıfı bulur ve bir instance döndürür.
        Bilinmeyen kategoriler OtherExpense olarak üretilir.

        Args:
            category: Gemini AI'dan gelen kategori adı (Türkçe veya İngilizce).
            merchant_name: Harcamanın yapıldığı firma adı.
            amount: Harcama tutarı.
            date: Harcama tarihi (YYYY-MM-DD).
            original_description: Bankadan gelen orijinal açıklama.

        Returns:
            Expense: Kategoriye uygun alt sınıf instance'ı.

        Örnek:
            >>> expense = ExpenseFactory.create("Yeme & İçme", "Starbucks", 45.5, "2026-05-01")
            >>> type(expense).__name__
            'FoodExpense'
            >>> expense.icon
            '🍔'
        """
        # Kategori adını normalize et (küçük harf, boşluk temizliği ve Türkçe İ/I harf hatası)
        normalized = category.strip().replace("İ", "i").replace("I", "ı").lower()

        # Registry'den uygun sınıfı bul, bulamazsa OtherExpense kullan
        expense_class = cls._registry.get(normalized, OtherExpense)

        # Nesneyi üret ve döndür
        return expense_class(
            merchant_name=merchant_name,
            amount=amount,
            date=date,
            original_description=original_description,
        )

    @classmethod
    def get_supported_categories(cls) -> list[str]:
        """
        Desteklenen ana kategori isimlerini döner.

        Returns:
            list[str]: Benzersiz kategori adları listesi.
        """
        seen = set()
        categories = []
        for key, expense_cls in cls._registry.items():
            # Her sınıftan sadece bir tane ekle (varyasyonları atla)
            class_name = expense_cls.__name__
            if class_name not in seen:
                seen.add(class_name)
                # Geçici instance ile kategori adını al
                temp = expense_cls(
                    merchant_name="", amount=0, date=""
                )
                categories.append(
                    {"name": temp.category, "icon": temp.icon, "key": temp.category_key}
                )
        return categories
