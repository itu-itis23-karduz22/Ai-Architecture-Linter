import os
import sys
import sqlite3

class ErrorLogger:
    def log(self, message):
        print(f"ERROR: {message}")

class UserManager:
    """
    Kasten Kötü Mimari Örneği (AI Linter'ı test etmek için)
    """
    def __init__(self):
        # 1. HATA (DIP İhlali): Bağımlılıkları dışarıdan enjekte etmek yerine, doğrudan somut sınıflara/kütüphanelere bağımlı.
        self.db_connection = sqlite3.connect("users.db")
        self.logger = ErrorLogger()

    def create_user_and_send_email(self, username, password):
        # 2. HATA (SRP İhlali): Bu sınıf hem kullanıcı yaratıyor, hem veritabanına bağlanıyor, 
        # hem hata konsoluna log basıyor, hem de e-posta gönderiyor (Single Responsibility Principle).
        
        if len(password) < 6:
            self.logger.log("Şifre çok kısa!")
            return False
            
        try:
            # 3. HATA: Veri erişim (Data Access) katmanı ile İş (Business) katmanı birbirine karışmış.
            cursor = self.db_connection.cursor()
            # Ayrıca SQL Injection'a açık bir kullanım (Clean Coding ihlali)
            cursor.execute(f"INSERT INTO users (user, pass) VALUES ('{username}', '{password}')")
            self.db_connection.commit()
            
            # 4. HATA: Gereksiz kütüphane kullanımı (import os) ve sistem çağrısı.
            os.system(f"echo 'Hoş geldin {username}' > welcome.txt")
            
            # 5. HATA (SRP / SoC İhlali): Bildirim gönderme işi ayrı bir serviste olmalıydı.
            print(f"E-posta gönderiliyor: {username}@sistem.com")
            
            return True
        except Exception as e:
            self.logger.log(str(e))
            return False
