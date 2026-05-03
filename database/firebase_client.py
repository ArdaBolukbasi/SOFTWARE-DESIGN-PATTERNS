"""
firebase_client.py — Singleton Pattern ile Firebase Bağlantısı
================================================================
🔷 DESIGN PATTERN: SINGLETON

Bu modül, Firebase Firestore veritabanı bağlantısını Singleton tasarım
kalıbı kullanarak yönetir. Singleton Pattern sayesinde uygulama boyunca
sadece TEK BİR Firebase bağlantı nesnesi (instance) oluşturulur.

Neden Singleton?
-----------------
- Firebase bağlantısı pahalı bir kaynaktır (ağ bağlantısı, kimlik doğrulama).
- Her API isteğinde yeni bir bağlantı açmak kaynak israfına neden olur.
- Singleton ile tüm istekler aynı bağlantıyı paylaşır → performans artar.

Kullanım:
    from database.firebase_client import FirebaseDB

    db = FirebaseDB()           # İlk çağrıda bağlantı kurulur
    db2 = FirebaseDB()          # Aynı instance döner (db is db2 → True)

    db.save_document("users/user_123/expenses", data)
    doc = db.get_document("users/user_123/expenses", "doc_id")
"""

import threading
from datetime import datetime, timezone
from typing import Any

import firebase_admin
from firebase_admin import credentials, firestore

from config import settings


class FirebaseDB:
    """
    Firebase Firestore veritabanı bağlantısını yöneten Singleton sınıfı.

    Bu sınıf, Python'un __new__ metodu override edilerek klasik
    thread-safe Singleton Pattern ile implemente edilmiştir.

    Attributes:
        _instance: Sınıfın tek örneğini (instance) tutan class-level değişken.
        _initialized: Bağlantının zaten kurulup kurulmadığını izleyen bayrak.
        _lock: Thread-safety için kullanılan kilit mekanizması.
        _db: Firestore istemci (client) referansı.

    Design Pattern:
        Singleton — GoF Creational Patterns
        Amaç: Bir sınıftan yalnızca bir örnek oluşturulmasını garanti eder
        ve bu örneğe global bir erişim noktası sağlar.
    """

    _instance = None          # Tek instance referansı
    _initialized = False      # İlk başlatma kontrolü
    _lock = threading.Lock()  # Thread-safe erişim kilidi

    def __new__(cls) -> "FirebaseDB":
        """
        Singleton instance oluşturma mekanizması.

        Double-checked locking pattern kullanılarak thread-safe
        bir şekilde tek instance garanti edilir.

        Returns:
            FirebaseDB: Sınıfın tek örneği.
        """
        if cls._instance is None:
            with cls._lock:
                # Double-checked locking: kilit alındıktan sonra tekrar kontrol
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """
        Firebase bağlantısını başlatır (sadece ilk çağrıda).

        İkinci ve sonraki çağrılarda _initialized bayrağı True olduğu
        için bağlantı tekrar kurulmaz — mevcut bağlantı kullanılır.
        """
        if not FirebaseDB._initialized:
            with FirebaseDB._lock:
                if not FirebaseDB._initialized:
                    self._connect()
                    FirebaseDB._initialized = True

    def _connect(self) -> None:
        """
        Firebase Admin SDK'yı başlatır ve Firestore istemcisini oluşturur.

        Service Account JSON dosyası config.py'deki FIREBASE_CREDENTIALS_PATH
        değişkeninden okunur.

        Raises:
            FileNotFoundError: Service account dosyası bulunamazsa.
            ValueError: Geçersiz kimlik bilgileri sağlanırsa.
        """
        try:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            self._db = firestore.client()
            print(f"✅ Firebase Firestore bağlantısı başarıyla kuruldu.")
        except FileNotFoundError:
            print(
                f"⚠️  Firebase credentials dosyası bulunamadı: "
                f"{settings.FIREBASE_CREDENTIALS_PATH}"
            )
            print("   Firestore işlemleri devre dışı kalacak.")
            self._db = None
        except Exception as e:
            print(f"⚠️  Firebase bağlantı hatası: {e}")
            print("   Firestore işlemleri devre dışı kalacak.")
            self._db = None

    @property
    def client(self) -> Any:
        """
        Firestore istemci referansını döner.

        Returns:
            google.cloud.firestore.Client veya None: Firestore istemcisi.
        """
        return self._db

    @property
    def is_connected(self) -> bool:
        """
        Firestore bağlantısının aktif olup olmadığını kontrol eder.

        Returns:
            bool: Bağlantı aktifse True, değilse False.
        """
        return self._db is not None

    def save_document(
        self, collection_path: str, data: dict, document_id: str | None = None
    ) -> str | None:
        """
        Firestore'a bir döküman kaydeder.

        Args:
            collection_path: Koleksiyon yolu (örn: "users/user_123/expenses").
            data: Kaydedilecek veri sözlüğü.
            document_id: Opsiyonel döküman ID'si. Verilmezse otomatik üretilir.

        Returns:
            str | None: Kaydedilen dökümanın ID'si veya hata durumunda None.
        """
        if not self.is_connected:
            print("⚠️  Firestore bağlantısı yok, kayıt atlanıyor.")
            return None

        try:
            # Zaman damgası ekle
            data["created_at"] = datetime.now(timezone.utc).isoformat()

            collection_ref = self._db.collection(collection_path)

            if document_id:
                collection_ref.document(document_id).set(data)
                return document_id
            else:
                _, doc_ref = collection_ref.add(data)
                return doc_ref.id

        except Exception as e:
            print(f"❌ Firestore kayıt hatası: {e}")
            return None

    def save_batch(self, collection_path: str, documents: list[dict]) -> list[str]:
        """
        Birden fazla dökümanı toplu (batch) olarak Firestore'a kaydeder.

        Firestore batch write kullanarak tek bir ağ isteğinde
        birden fazla döküman yazılır — performans açısından daha verimli.

        Args:
            collection_path: Koleksiyon yolu (örn: "users/user_123/expenses").
            documents: Kaydedilecek veri sözlüklerinin listesi.

        Returns:
            list[str]: Kaydedilen dökümanların ID listesi.
        """
        if not self.is_connected:
            print("⚠️  Firestore bağlantısı yok, toplu kayıt atlanıyor.")
            return []

        try:
            batch = self._db.batch()
            doc_ids = []
            collection_ref = self._db.collection(collection_path)

            for doc_data in documents:
                doc_data["created_at"] = datetime.now(timezone.utc).isoformat()
                doc_ref = collection_ref.document()
                batch.set(doc_ref, doc_data)
                doc_ids.append(doc_ref.id)

            batch.commit()
            print(
                f"✅ {len(doc_ids)} döküman başarıyla kaydedildi: {collection_path}"
            )
            return doc_ids

        except Exception as e:
            print(f"❌ Firestore toplu kayıt hatası: {e}")
            return []

    def get_document(self, collection_path: str, document_id: str) -> dict | None:
        """
        Firestore'dan belirli bir dökümanı okur.

        Args:
            collection_path: Koleksiyon yolu.
            document_id: Okunacak dökümanın ID'si.

        Returns:
            dict | None: Döküman verisi veya bulunamazsa None.
        """
        if not self.is_connected:
            return None

        try:
            doc = self._db.collection(collection_path).document(document_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"❌ Firestore okuma hatası: {e}")
            return None

    def get_collection(self, collection_path: str) -> list[dict]:
        """
        Bir koleksiyondaki tüm dökümanları okur.

        Args:
            collection_path: Koleksiyon yolu.

        Returns:
            list[dict]: Döküman verilerinin listesi.
        """
        if not self.is_connected:
            return []

        try:
            docs = self._db.collection(collection_path).stream()
            return [{"id": doc.id, **doc.to_dict()} for doc in docs]
        except Exception as e:
            print(f"❌ Firestore koleksiyon okuma hatası: {e}")
            return []
