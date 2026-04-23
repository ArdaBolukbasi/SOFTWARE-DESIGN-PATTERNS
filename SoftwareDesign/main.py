from datetime import datetime

class User:
    def __init__(self, username, password, weekly_limit):
        self.username = username
        self.__password = password  
        self.__weekly_limit = weekly_limit 

    def login(self):
        print(f"[{self.username}] sisteme giriş yaptı.")
        return True

    def set_limit(self, new_limit):
        self.__weekly_limit = new_limit
        print(f"Yeni haftalık limit belirlendi: {self.__weekly_limit} TRY")

class Expense:
    def __init__(self, raw_text, amount, category):
        self.raw_text = raw_text
        self.amount = amount
        self.category = category
        self.date = datetime.now()

    def create_record(self):
        return f"Kayıt: {self.amount} TRY - {self.category}"


class FoodExpense(Expense):
    def __init__(self, raw_text, amount):
        super().__init__(raw_text, amount, "Food & Dining")

    def create_record(self):
        return f"🍔 Yemek Kaydı: {self.amount} TRY (Veri: '{self.raw_text}')"


class AICoach:
    def __init__(self, model_name="Gemini 1.5 Pro"):
        self.model_name = model_name

    def parse_text(self, input_text):
        print(f"[{self.model_name}] Doğal dil işleniyor: '{input_text}'")
        return FoodExpense(input_text, 200.0)

    def generate_summary(self):
        return "AI Özeti: Bütçe limitleriniz dahilinde harcama yapıyorsunuz."

class FirebaseDB:
    def __init__(self, db_url):
        self.db_url = db_url

    def save_data(self, expense_data):
        print(f"Veritabanına kaydediliyor ({self.db_url}) -> {expense_data.create_record()}")

    def fetch_history(self, username):
        print(f"{username} için harcama geçmişi getiriliyor...")
        return []



if __name__ == "__main__":
    print("\n--- AI BUDGET TRACKER BAŞLATILIYOR ---\n")

    arda = User("Arda8597", "gizlisifre123", 2500)
    arda.login()
    arda.set_limit(3000)
    print("-" * 40)

    ai = AICoach()
    db = FirebaseDB("https://budget-tracker.firebaseio.com")
    print("-" * 40)


    ornek_metin = "Bugün dışarıda burger yedim 200 TL"
    
   
    harcama_nesnesi = ai.parse_text(ornek_metin)
    

    db.save_data(harcama_nesnesi)
    

    print("-" * 40)
    print(ai.generate_summary())
    print("\n--- SİSTEM KAPATILDI ---")