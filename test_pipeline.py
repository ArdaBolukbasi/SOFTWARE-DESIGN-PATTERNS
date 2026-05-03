"""
test_pipeline.py — AI Budget Tracker Uçtan Uca Test Scripti
================================================================
Bu script, tüm veri akışını tek tuşla test eder:

    Plaid Mock → Gemini AI Analizi → Factory Pattern → Firebase Kaydı

Kullanım:
    1. Önce sunucuyu başlatın:
       uvicorn main:app --reload

    2. Ardından bu scripti çalıştırın:
       python test_pipeline.py

Çıktı:
    - Renkli terminal çıktısı ile toplam harcama, kategori dağılımı
      ve Gemini'nin Türkçe finansal tavsiyesi gösterilir.
"""

import sys
import json
import urllib.request
import urllib.error

# ============================================================
# ANSI Renk Kodları — Terminal çıktısını renklendirir
# ============================================================

class Colors:
    """Terminal renk kodları (ANSI escape sequences)."""
    HEADER    = "\033[95m"     # Mor/Pembe
    BLUE      = "\033[94m"     # Mavi
    CYAN      = "\033[96m"     # Cyan
    GREEN     = "\033[92m"     # Yeşil
    YELLOW    = "\033[93m"     # Sarı
    RED       = "\033[91m"     # Kırmızı
    BOLD      = "\033[1m"      # Kalın
    UNDERLINE = "\033[4m"      # Altı çizili
    DIM       = "\033[2m"      # Soluk
    RESET     = "\033[0m"      # Sıfırla


def print_banner():
    """Başlangıç banner'ını yazdırır."""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🧪  AI BUDGET TRACKER — Pipeline Test Scripti  🧪         ║
║                                                              ║
║   Plaid Mock → Gemini AI → Factory → Firebase → Response     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
{Colors.RESET}"""
    print(banner)


def print_section(title: str, emoji: str = "📌"):
    """Bölüm başlığı yazdırır."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'─'*60}")
    print(f"  {emoji}  {title}")
    print(f"{'─'*60}{Colors.RESET}\n")


def test_health():
    """Health check endpoint'ini test eder."""
    print_section("ADIM 1: Health Check", "💓")

    try:
        req = urllib.request.Request("http://localhost:8000/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        status = data.get("status", "unknown")
        if status == "healthy":
            print(f"   {Colors.GREEN}✅ Sunucu durumu: {status}{Colors.RESET}")
            print(f"   {Colors.DIM}App: {data.get('app')} v{data.get('version')}{Colors.RESET}")
            return True
        else:
            print(f"   {Colors.RED}❌ Beklenmeyen durum: {status}{Colors.RESET}")
            return False

    except urllib.error.URLError:
        print(f"   {Colors.RED}❌ Sunucuya bağlanılamıyor!{Colors.RESET}")
        print(f"   {Colors.YELLOW}   Önce sunucuyu başlatın:{Colors.RESET}")
        print(f"   {Colors.DIM}   uvicorn main:app --reload{Colors.RESET}")
        return False


def test_analyze_spending():
    """
    Ana pipeline'ı test eder:
    GET /api/analyze-spending?user_id=test_kullanicisi_1&period=month
    """
    print_section("ADIM 2: Harcama Analizi Pipeline Testi", "🚀")

    url = "http://localhost:8000/api/analyze-spending?user_id=test_kullanicisi_1&period=month"
    print(f"   {Colors.DIM}URL: {url}{Colors.RESET}")
    print(f"   {Colors.YELLOW}⏳ İstek gönderiliyor (Gemini analizi biraz sürebilir)...{Colors.RESET}\n")

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode()
            data = json.loads(raw)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"   {Colors.RED}❌ HTTP Hatası: {e.code}{Colors.RESET}")
        print(f"   {Colors.DIM}{error_body[:500]}{Colors.RESET}")
        return False
    except urllib.error.URLError as e:
        print(f"   {Colors.RED}❌ Bağlantı Hatası: {e}{Colors.RESET}")
        return False
    except json.JSONDecodeError:
        print(f"   {Colors.RED}❌ JSON parse hatası{Colors.RESET}")
        print(f"   {Colors.DIM}Ham yanıt: {raw[:500]}{Colors.RESET}")
        return False

    # ── Yanıtı güzel yazdır ──────────────────────────────────

    if data.get("status") != "success":
        print(f"   {Colors.RED}❌ API başarısız yanıt döndü: {data}{Colors.RESET}")
        return False

    result = data["data"]

    # Toplam Harcama
    print_section("💰 TOPLAM HARCAMA", "💰")
    total = result.get("total_spending", 0)
    currency = result.get("currency", "USD")
    print(f"   {Colors.BOLD}{Colors.GREEN}")
    print(f"   ╔═══════════════════════════════╗")
    print(f"   ║   💵  ${total:,.2f} {currency}          ║")
    print(f"   ╚═══════════════════════════════╝")
    print(f"   {Colors.RESET}")

    # Kategori Dağılımı
    print_section("📊 KATEGORİ DAĞILIMI", "📊")
    categories = result.get("categories", [])

    if categories:
        # Tablo başlığı
        print(f"   {Colors.BOLD}{'Kategori':<20} {'Toplam':>10} {'Yüzde':>8} {'İşlem':>6}{Colors.RESET}")
        print(f"   {'─'*48}")

        for cat in categories:
            name = cat.get("name", "?")
            icon = cat.get("icon", "📦")
            cat_total = cat.get("total", 0)
            pct = cat.get("percentage", 0)
            count = cat.get("transaction_count", 0)

            # Yüzdeye göre çubuk oluştur
            bar_len = int(pct / 5)  # Her 5% = 1 blok
            bar = "█" * bar_len + "░" * (20 - bar_len)

            # Yüzdeye göre renk belirle
            if pct >= 30:
                color = Colors.RED
            elif pct >= 15:
                color = Colors.YELLOW
            else:
                color = Colors.GREEN

            print(
                f"   {icon} {name:<17} "
                f"{Colors.BOLD}${cat_total:>8,.2f}{Colors.RESET} "
                f"{color}%{pct:>5.1f}{Colors.RESET} "
                f"{Colors.DIM}{count:>4} txn{Colors.RESET}"
            )
            print(f"      {color}{bar}{Colors.RESET}")

    # AI Tavsiyesi
    print_section("🤖 GEMİNİ AI TAVSİYESİ (TÜRKÇE)", "🤖")
    advice = result.get("ai_advice", "Tavsiye bulunamadı.")
    print(f"   {Colors.CYAN}{Colors.BOLD}╔{'═'*56}╗{Colors.RESET}")

    # Tavsiye metnini satırlara böl (max 54 karakter)
    words = advice.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= 54:
            current_line += (" " if current_line else "") + word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    for line in lines:
        print(f"   {Colors.CYAN}║ {line:<55}║{Colors.RESET}")

    print(f"   {Colors.CYAN}{Colors.BOLD}╚{'═'*56}╝{Colors.RESET}")

    # Meta bilgiler
    print(f"\n   {Colors.DIM}User ID   : {result.get('user_id')}{Colors.RESET}")
    print(f"   {Colors.DIM}Period    : {result.get('period')}{Colors.RESET}")
    print(f"   {Colors.DIM}Analyzed  : {result.get('analyzed_at')}{Colors.RESET}")

    return True


def test_categories():
    """Desteklenen kategorileri listeler."""
    print_section("ADIM 3: Kategori Listesi", "📂")

    try:
        req = urllib.request.Request("http://localhost:8000/api/categories")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        categories = data.get("categories", [])
        print(f"   {Colors.GREEN}✅ {len(categories)} kategori destekleniyor:{Colors.RESET}\n")

        for cat in categories:
            print(f"      {cat.get('icon', '📦')}  {cat.get('name', '?'):<15} (key: {cat.get('key', '?')})")

        return True

    except Exception as e:
        print(f"   {Colors.RED}❌ Hata: {e}{Colors.RESET}")
        return False


def main():
    """Ana test fonksiyonu — tüm testleri sırayla çalıştırır."""
    print_banner()

    results = {}

    # Test 1: Health Check
    results["Health Check"] = test_health()
    if not results["Health Check"]:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Sunucu çalışmıyor, testler durduruluyor.{Colors.RESET}")
        sys.exit(1)

    # Test 2: Harcama Analizi (Ana Pipeline)
    results["Pipeline"] = test_analyze_spending()

    # Test 3: Kategori Listesi
    results["Categories"] = test_categories()

    # ── Sonuç Özeti ──────────────────────────────────────────
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print(f"{'═'*60}")
    print(f"  📋  TEST SONUÇLARI")
    print(f"{'═'*60}{Colors.RESET}\n")

    all_passed = True
    for test_name, passed in results.items():
        icon = f"{Colors.GREEN}✅ BAŞARILI" if passed else f"{Colors.RED}❌ BAŞARISIZ"
        print(f"   {icon}{Colors.RESET}  {test_name}")
        if not passed:
            all_passed = False

    if all_passed:
        print(f"\n   {Colors.GREEN}{Colors.BOLD}🎉 Tüm testler başarıyla geçti!{Colors.RESET}")
        print(f"   {Colors.DIM}   Pipeline: Plaid Mock ✓ → Gemini AI ✓ → Factory ✓ → Firebase ✓{Colors.RESET}")
    else:
        print(f"\n   {Colors.YELLOW}⚠️  Bazı testler başarısız oldu.{Colors.RESET}")

    print(f"\n{'═'*60}\n")
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
