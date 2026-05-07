# 🏦 BudgerAI — Backend API

Yapay zeka destekli kişisel finans analiz platformu. Banka harcamalarını otomatik kategorize eder, istatistik hesaplar ve kişiselleştirilmiş Türkçe finansal tavsiye üretir.

> **Not:** Bu proje yalnızca Backend (REST API) katmanını içerir. Frontend ekibi ayrı çalışmaktadır.

---

## 🛠️ Teknoloji Yığını

| Katman | Teknoloji | Açıklama |
|--------|-----------|----------|
| **Framework** | FastAPI (Python) | Yüksek performanslı async REST API |
| **Veritabanı** | Firebase Firestore | NoSQL bulut veritabanı |
| **Banka API** | Plaid Sandbox | Test ortamında sahte banka verisi |
| **Yapay Zeka** | Google Gemini API | Doğal dil işleme ve harcama analizi |
| **Tasarım Kalıpları** | Singleton + Factory | Akademik rapor gereksinimleri |

---

## 🎯 Tasarım Kalıpları (Design Patterns)

### 🔷 Singleton Pattern — `FirebaseDB`
> **Dosya:** [`database/firebase_client.py`](database/firebase_client.py)

Firebase veritabanı bağlantısı Singleton Pattern ile yönetilir. Uygulama boyunca yalnızca **tek bir bağlantı nesnesi** oluşturulur.

```python
db1 = FirebaseDB()
db2 = FirebaseDB()
print(db1 is db2)  # → True (aynı instance)
```

**Neden Singleton?**
- Firebase bağlantısı pahalı bir kaynaktır (ağ, kimlik doğrulama)
- Her istekte yeni bağlantı açmak kaynak israfıdır
- Thread-safe double-checked locking ile güvenli erişim

### 🔷 Factory Pattern — `ExpenseFactory`
> **Dosya:** [`models/expense.py`](models/expense.py)

Gemini AI'dan gelen kategori bilgisine göre doğru `Expense` alt sınıfı otomatik üretilir.

```python
expense = ExpenseFactory.create("Yeme & İçme", "Starbucks", 145.50, "2026-05-01")
# → FoodExpense(merchant_name="Starbucks", amount=145.50, ...)
```

**Desteklenen Kategoriler:**

| Sınıf | Kategori | İkon |
|-------|----------|------|
| `FoodExpense` | Yeme & İçme | 🍔 |
| `TransportExpense` | Ulaşım | 🚗 |
| `BillExpense` | Fatura | 📄 |
| `ShoppingExpense` | Alışveriş | 🛒 |
| `EntertainmentExpense` | Eğlence | 🎬 |
| `HealthExpense` | Sağlık | 💊 |
| `OtherExpense` | Diğer | 📦 |

---

## 📁 Proje Yapısı

```
.
├── main.py                        # FastAPI uygulama giriş noktası
├── config.py                      # Ortam değişkenleri (Settings)
├── requirements.txt               # Python bağımlılıkları
├── .env.example                   # API anahtarları şablonu
├── test_pipeline.py               # Uçtan uca test scripti
│
├── database/
│   ├── __init__.py
│   └── firebase_client.py         # 🔷 Singleton Pattern
│
├── models/
│   ├── __init__.py
│   └── expense.py                 # 🔷 Factory Pattern
│
├── services/
│   ├── __init__.py
│   ├── plaid_service.py           # Plaid Sandbox + Mock Data
│   └── gemini_service.py          # Gemini AI analiz servisi
│
└── routers/
    ├── __init__.py
    ├── spending.py                # /api/analyze-spending
    └── user.py                    # /api/register-user
```

---

## 🔄 Sistem Akışı (Data Pipeline)

```
Frontend GET /api/analyze-spending?user_id=xxx&period=month
          │
          ▼
  ┌──────────────────────────────────┐
  │  ADIM 0: Kullanıcı Doğrulama    │ ← Firebase'de user kaydı + access_token kontrolü
  └──────────┬───────────────────────┘
             │
     access_token var mı?
      ╱              ╲
    EVET             HAYIR
     │                │
  Plaid API      Mock Data
  (gerçek)     (Starbucks, Migros...)
      ╲              ╱
       └─────┬──────┘
             ▼
  ┌──────────────────────────────────┐
  │  ADIM 2: Gemini AI Analizi       │ ← Kategorize + İstatistik + Türkçe Tavsiye
  └──────────┬───────────────────────┘
             ▼
  ┌──────────────────────────────────┐
  │  ADIM 3: Factory Pattern         │ ← ExpenseFactory.create() → FoodExpense, vb.
  └──────────┬───────────────────────┘
             ▼
  ┌──────────────────────────────────┐
  │  ADIM 4: Firebase Kayıt          │ ← Singleton bağlantı → users/{id}/expenses
  └──────────┬───────────────────────┘
             ▼
  ┌──────────────────────────────────┐
  │  ADIM 5: JSON Response           │ ← Toplam, yüzdelik dağılım, AI tavsiye
  └──────────────────────────────────┘
```

---

## 🚀 Kurulum ve Çalıştırma

### 1. Bağımlılıkları Yükle
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Ortam Değişkenlerini Ayarla
```bash
cp .env.example .env
# .env dosyasını düzenle ve API anahtarlarını gir
```

**Gerekli Anahtarlar:**
- **Plaid:** [dashboard.plaid.com](https://dashboard.plaid.com) → Sandbox Keys
- **Gemini:** [aistudio.google.com](https://aistudio.google.com) → Get API Key
- **Firebase:** Firebase Console → Project Settings → Service Accounts → JSON Key

### 3. Sunucuyu Başlat
```bash
source venv/bin/activate
uvicorn main:app --reload
```

### 4. Test Et
```bash
# Başka bir terminalde:
source venv/bin/activate
python3 test_pipeline.py
```

---

## 📡 API Endpoint'leri

### `POST /api/register-user` — Kullanıcı Kaydı
Yeni kullanıcı oluşturur veya mevcut kullanıcıyı doğrular.

```bash
curl -X POST http://localhost:8000/api/register-user \
  -H "Content-Type: application/json" \
  -d '{"user_id": "arda_123", "display_name": "Arda", "email": "arda@example.com"}'
```

**Yanıtlar:**
- `201` → Kullanıcı oluşturuldu
- `200` → Kullanıcı zaten kayıtlı

---

### `GET /api/analyze-spending` — Harcama Analizi
Ana pipeline endpoint'i. Akıllı senkronizasyon mantığı ile çalışır:

- ✅ Kullanıcının `plaid_access_token`'ı varsa → **gerçek banka verisi** çekilir
- 🎭 Token yoksa → **otomatik sandbox modu** ile mock data üretilir

```bash
curl "http://localhost:8000/api/analyze-spending?user_id=arda_123&period=month"
```

**Yanıt Örneği:**
```json
{
  "status": "success",
  "data": {
    "user_id": "arda_123",
    "period": "month",
    "total_spending": 1801.34,
    "currency": "USD",
    "categories": [
      {"name": "Yeme & İçme", "icon": "🍔", "total": 1037.80, "percentage": 57.6, "transaction_count": 2},
      {"name": "Ulaşım", "icon": "🚗", "total": 67.80, "percentage": 3.8, "transaction_count": 1}
    ],
    "ai_advice": "Harcamalarınızın %57.6'sı yeme-içmeye gidiyor...",
    "data_source": "sandbox"
  }
}
```

---

### `GET /api/categories` — Kategori Listesi
```bash
curl http://localhost:8000/api/categories
```

### `GET /health` — Sağlık Kontrolü
```bash
curl http://localhost:8000/health
```

---

## 🗄️ Firebase Veritabanı Yapısı

```
Firestore
├── users/
│   └── {user_id}/                    # Kullanıcı dökümanı
│       ├── user_id: "arda_123"
│       ├── display_name: "Arda"
│       ├── email: "arda@example.com"
│       ├── registered_at: "2026-05-03T..."
│       ├── plaid_access_token: null   # Banka bağlandığında dolar
│       │
│       ├── expenses/                  # Harcama koleksiyonu
│       │   ├── {auto_id}/
│       │   │   ├── category: "Yeme & İçme"
│       │   │   ├── merchant_name: "Starbucks"
│       │   │   ├── amount: 145.50
│       │   │   ├── date: "2026-05-02"
│       │   │   └── icon: "🍔"
│       │   └── ...
│       │
│       └── analysis_history/          # Analiz geçmişi
│           └── {auto_id}/
│               ├── total_spending: 1801.34
│               ├── category_count: 5
│               ├── ai_advice: "..."
│               └── data_source: "sandbox"
```

---

## 📚 Swagger Dokümantasyonu

Sunucu çalışırken:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 👨‍💻 Geliştirici

**Arda Bölükbaşı**

Software Design Patterns — Akademik Proje

---

## 📊 UML Diagramları (UML Diagrams)

Projenin mimarisini ve akışını gösteren UML diyagramları aşağıdadır. Bu diyagramlar akademik proje raporunda kullanılması amacıyla tasarlanmıştır. GitHub Markdown yapısı gereği bu diyagramlar projeye girildiğinde otomatik olarak görsellere dönüşecektir.

### 1. Class Diagram (Sınıf Diyagramı)
```mermaid
classDiagram
    class FirebaseDB {
        <<Singleton>>
        - _instance : FirebaseDB
        - _db : firestore.Client
        + __new__()
        + save_document()
        + get_document()
    }
    class PlaidService {
        - _client
        - _access_token
        + get_transactions(period)
        - _get_fallback_transactions()
    }
    class GeminiService {
        - client : genai.Client
        + analyze_spending(transactions)
        - _fallback_analysis()
    }
    class ExpenseFactory {
        <<Factory>>
        + create_expense(category, data) Expense
    }
    class Expense {
        <<Abstract>>
        + amount: float
        + date: str
        + calculate_impact()
    }
    class FoodExpense
    class TransportExpense

    Expense <|-- FoodExpense
    Expense <|-- TransportExpense
    ExpenseFactory ..> Expense : creates
    FirebaseDB <-- PlaidService : uses (token storage)
```

### 2. Use Case Diagram (Kullanım Senaryosu)
```mermaid
flowchart LR
    User([User])
    
    SignIn(Sign In / Register)
    ViewDash(View Dashboard)
    RefreshData(Refresh Bank Data)
    GetAdvice(Get AI Advice)
    
    User --> SignIn
    User --> ViewDash
    User --> RefreshData
    User --> GetAdvice
    
    SignIn -.-> |includes| VerifyUser(Verify with Firebase)
    RefreshData -.-> |includes| FetchPlaid(Fetch from Plaid API)
    GetAdvice -.-> |includes| AskGemini(Analyze via Gemini API)
```

### 3. Sequence Diagram (Sıralama Diyagramı)
```mermaid
sequenceDiagram
    actor User
    participant Frontend as Streamlit UI
    participant Backend as FastAPI Router
    participant Plaid as Plaid API
    participant AI as Gemini API
    participant DB as Firebase DB

    User->>Frontend: Clicks "Refresh Analysis"
    Frontend->>Backend: GET /api/analyze-spending
    Backend->>DB: Check User existence
    DB-->>Backend: User found
    Backend->>Plaid: get_transactions()
    Plaid-->>Backend: Returns Raw Transactions
    Backend->>AI: analyze_spending(raw_transactions)
    AI-->>Backend: Returns JSON Analysis (Categories & Advice)
    Backend->>Backend: ExpenseFactory maps data to Objects
    Backend->>DB: save_document(users/{uid}/expenses)
    DB-->>Backend: Success ACK
    Backend-->>Frontend: HTTP 200 OK (JSON Data)
    Frontend-->>User: Renders Dashboard & Charts
```

### 4. Component Diagram (Bileşen Diyagramı)
```mermaid
flowchart TB
    subgraph Client Tier
        UI[Streamlit Frontend App]
    end

    subgraph Application Tier
        API[FastAPI REST API]
        Router[Controllers / Routers]
        Services[Business Logic Services]
        Factory[Model Factory]
        
        API --> Router
        Router --> Services
        Router --> Factory
    end

    subgraph Data Tier
        DB[(Firebase Firestore NoSQL)]
    end

    subgraph External APIs
        Plaid[Plaid Banking API]
        Gemini[Google Gemini LLM]
    end

    UI -- HTTP REST --> API
    Services -- HTTPS --> Plaid
    Services -- HTTPS --> Gemini
    Services -- Firebase SDK --> DB
```

### 5. Communication Diagram (İletişim Diyagramı)
```mermaid
flowchart TD
    UI["1: UI Dashboard"] -->|"1.1: GET /analyze-spending"| Router["2: SpendingRouter"]
    Router -->|"1.2: get_transactions()"| PlaidSvc["3: PlaidService"]
    PlaidSvc -.->|"1.3: Returns Data"| Router
    Router -->|"1.4: analyze_spending()"| GeminiSvc["4: GeminiService"]
    GeminiSvc -.->|"1.5: Returns JSON"| Router
    Router -->|"1.6: create_expense()"| Factory["5: ExpenseFactory"]
    Router -->|"1.7: save_document()"| DB["6: FirebaseDB"]
    DB -.->|"1.8: ACK"| Router
    Router -.->|"1.9: HTTP 200"| UI
```

### 6. Object Diagram (Nesne Diyagramı)
```mermaid
classDiagram
    class UserDocument {
        user_id = "arda123"
        display_name = "Arda Bölükbaşı"
        plaid_access_token = "access-sandbox-xxx"
    }
    class DBInstance {
        _initialized = True
        _db = FirestoreClient
    }
    class FoodExpense {
        name = "Starbucks"
        amount = 145.50
        category = "Food and Drink"
    }
    class TransportExpense {
        name = "Uber"
        amount = 67.80
        category = "Transportation"
    }

    UserDocument --> FoodExpense : owns
    UserDocument --> TransportExpense : owns
    DBInstance ..> UserDocument : manages
```

### 7. State Machine Diagram (Durum Makinesi)
```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> VerifyingUser : User Requests Analysis
    VerifyingUser --> FetchingBankData : User Verified
    VerifyingUser --> Idle : User Not Found (HTTP 404)
    
    FetchingBankData --> AnalyzingData : Transactions Retrieved
    FetchingBankData --> FallbackMockData : Plaid API Failed
    FallbackMockData --> AnalyzingData : Mock Transactions Ready
    
    AnalyzingData --> SavingToDatabase : Gemini Returns JSON
    AnalyzingData --> FallbackAnalysis : Gemini 503 Error / Timeout
    FallbackAnalysis --> SavingToDatabase : Basic Stats Computed
    
    SavingToDatabase --> Completed : Firestore Save Success
    Completed --> [*] : Response Sent to UI
```
