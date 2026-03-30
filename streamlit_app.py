import os
import json
import sqlite3
import hashlib
import threading
import time
import datetime
import requests
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.utils import get_color_from_hex

# =================== إعدادات المنصة ===================
APP_NAME = "Relax Platform"
ESTABLISHED_YEAR = 2025
ESTABLISHED_MONTH = 3
ESTABLISHED_DAY = 31
INVEST_TIMES = ["15:00", "17:00", "19:00"]  # بتوقيت تركيا (UTC+3)
PROFIT_PERCENT = 2  # 2% ربح لكل استثمار
LOCK_DAYS = 45  # تجميد رأس المال
WITHDRAW_COOLDOWN_HOURS = 12  # كل 12 ساعة سحب
REFERRAL_BONUS = {
    500: (30, 20),    # (مكافأة المحيل, مكافأة المحال)
    1000: (60, 40),
    2000: (120, 60),
    3000: (180, 90)
}
SUPPORTED_CURRENCIES = ["USDT", "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "DOT", "MATIC"]

# =================== قاعدة البيانات ===================
def init_db():
    conn = sqlite3.connect('relax_platform.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        email TEXT,
        google_auth_secret TEXT,
        id_verified BOOLEAN DEFAULT 0,
        referrer_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_deposit REAL DEFAULT 0,
        current_balance REAL DEFAULT 0,
        locked_balance REAL DEFAULT 0,
        total_profit REAL DEFAULT 0,
        last_withdraw TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS investments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        profit REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        executed_at TIMESTAMP,
        status TEXT DEFAULT 'pending'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        is_profit BOOLEAN,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_id INTEGER,
        referred_id INTEGER,
        amount REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

# =================== CoinEx API (محاكاة) ===================
class CoinExAPI:
    def __init__(self, api_key=None, api_secret=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.coinex.com/v1"

    def get_balance(self, currency="USDT"):
        # هنا يجب إضافة الكود الحقيقي للاتصال بالـ API
        # للعرض فقط: نرجع رصيد وهمي
        return 10000.0

    def withdraw(self, address, amount, currency="USDT"):
        # سحب حقيقي عبر API
        return {"status": "success", "txid": "fake_txid"}

    def get_market_price(self, symbol="BTCUSDT"):
        # جلب سعر السوق الحقيقي
        return 50000.0

# =================== إدارة المستخدمين ===================
class UserManager:
    @staticmethod
    def create_user(username, password, email, referrer_id=None):
        conn = sqlite3.connect('relax_platform.db')
        c = conn.cursor()
        hashed = hashlib.sha256(password.encode()).hexdigest()
        try:
            c.execute("INSERT INTO users (username, password, email, referrer_id) VALUES (?,?,?,?)",
                      (username, hashed, email, referrer_id))
            user_id = c.lastrowid
            conn.commit()
            # معالجة مكافأة الإحالة إذا كان هناك محيل
            if referrer_id:
                # سيتم استدعاء الدالة المناسبة لاحقاً
                pass
            return user_id
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()

    @staticmethod
    def authenticate(username, password):
        conn = sqlite3.connect('relax_platform.db')
        c = conn.cursor()
        hashed = hashlib.sha256(password.encode()).hexdigest()
        c.execute("SELECT id, username, google_auth_secret, id_verified FROM users WHERE username=? AND password=?", (username, hashed))
        row = c.fetchone()
        conn.close()
        return row

    @staticmethod
    def get_user_balance(user_id):
        conn = sqlite3.connect('relax_platform.db')
        c = conn.cursor()
        c.execute("SELECT current_balance, locked_balance FROM users WHERE id=?", (user_id,))
        row = c.fetchone()
        conn.close()
        return row if row else (0,0)

    @staticmethod
    def update_balance(user_id, amount, lock=False):
        conn = sqlite3.connect('relax_platform.db')
        c = conn.cursor()
        if lock:
            c.execute("UPDATE users SET locked_balance = locked_balance + ? WHERE id=?", (amount, user_id))
        else:
            c.execute("UPDATE users SET current_balance = current_balance + ? WHERE id=?", (amount, user_id))
        conn.commit()
        conn.close()

    @staticmethod
    def add_deposit(user_id, amount):
        # إيداع جديد
        conn = sqlite3.connect('relax_platform.db')
        c = conn.cursor()
        c.execute("UPDATE users SET total_deposit = total_deposit + ?, current_balance = current_balance + ? WHERE id=?", (amount, amount, user_id))
        conn.commit()
        conn.close()
        # هنا يمكن إضافة منطق للإحالة
        # (سنضيفه لاحقاً)

    @staticmethod
    def can_withdraw(user_id):
        conn = sqlite3.connect('relax_platform.db')
        c = conn.cursor()
        c.execute("SELECT last_withdraw, datetime('now', '-12 hours') FROM users WHERE id=?", (user_id,))
        row = c.fetchone()
        conn.close()
        if row and row[0]:
            last = datetime.datetime.fromisoformat(row[0])
            now = datetime.datetime.now()
            return (now - last).total_seconds() >= 12*3600
        return True

    @staticmethod
    def record_withdraw(user_id, amount, is_profit):
        conn = sqlite3.connect('relax_platform.db')
        c = conn.cursor()
        c.execute("INSERT INTO withdrawals (user_id, amount, is_profit) VALUES (?,?,?)", (user_id, amount, is_profit))
        c.execute("UPDATE users SET last_withdraw = CURRENT_TIMESTAMP WHERE id=?", (user_id,))
        if is_profit:
            c.execute("UPDATE users SET current_balance = current_balance - ? WHERE id=?", (amount, user_id))
        else:
            c.execute("UPDATE users SET locked_balance = locked_balance - ? WHERE id=?", (amount, user_id))
        conn.commit()
        conn.close()

# =================== نظام الاستثمار ===================
class InvestmentManager:
    @staticmethod
    def can_invest_now():
        # التحقق من الوقت الحالي بتوقيت تركيا
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))
        current_time = now.strftime("%H:%M")
        return current_time in INVEST_TIMES

    @staticmethod
    def schedule_investment(user_id, amount):
        # تخزين طلب استثمار في قاعدة البيانات
        conn = sqlite3.connect('relax_platform.db')
        c = conn.cursor()
        c.execute("INSERT INTO investments (user_id, amount, status) VALUES (?,?,?)", (user_id, amount, 'scheduled'))
        inv_id = c.lastrowid
        conn.commit()
        conn.close()
        # جدولة التنفيذ بعد 15 دقيقة
        Clock.schedule_once(lambda dt: InvestmentManager.execute_investment(inv_id), 15*60)
        return inv_id

    @staticmethod
    def execute_investment(investment_id):
        conn = sqlite3.connect('relax_platform.db')
        c = conn.cursor()
        c.execute("SELECT user_id, amount FROM investments WHERE id=? AND status='scheduled'", (investment_id,))
        row = c.fetchone()
        if row:
            user_id, amount = row
            profit = amount * PROFIT_PERCENT / 100
            # تحديث رصيد المستخدم (الربح يضاف إلى الرصيد القابل للسحب)
            UserManager.update_balance(user_id, profit, lock=False)
            # تحديث حالة الاستثمار
            c.execute("UPDATE investments SET status='completed', profit=?, executed_at=CURRENT_TIMESTAMP WHERE id=?", (profit, investment_id))
            conn.commit()
            # إشعار المستخدم
            # يمكن إضافة popup
        conn.close()

# =================== نظام الإحالات ===================
class ReferralManager:
    @staticmethod
    def process_referral(referrer_id, referred_id, deposit_amount):
        # البحث عن المكافأة المناسبة
        bonus = None
        for threshold, (ref_bonus, new_bonus) in REFERRAL_BONUS.items():
            if deposit_amount >= threshold:
                bonus = (ref_bonus, new_bonus)
        if bonus:
            ref_bonus, new_bonus = bonus
            # إضافة المكافأة للمحيل
            UserManager.update_balance(referrer_id, ref_bonus, lock=False)
            # إضافة المكافأة للمحال
            UserManager.update_balance(referred_id, new_bonus, lock=False)
            # تسجيل الإحالة
            conn = sqlite3.connect('relax_platform.db')
            c = conn.cursor()
            c.execute("INSERT INTO referrals (referrer_id, referred_id, amount) VALUES (?,?,?)", (referrer_id, referred_id, deposit_amount))
            conn.commit()
            conn.close()

# =================== واجهات Kivy (شاشات متعددة) ===================
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        layout.add_widget(Label(text=APP_NAME, font_size='30sp'))
        self.username = TextInput(hint_text='اسم المستخدم', multiline=False)
        self.password = TextInput(hint_text='كلمة المرور', password=True, multiline=False)
        btn_login = Button(text='دخول')
        btn_login.bind(on_press=self.login)
        btn_register = Button(text='تسجيل جديد')
        btn_register.bind(on_press=self.go_to_register)
        layout.add_widget(self.username)
        layout.add_widget(self.password)
        layout.add_widget(btn_login)
        layout.add_widget(btn_register)
        self.add_widget(layout)

    def login(self, instance):
        user = UserManager.authenticate(self.username.text, self.password.text)
        if user:
            self.manager.current = 'home'
            self.manager.get_screen('home').set_user(user[0], user[1])
        else:
            popup = Popup(title='خطأ', content=Label(text='اسم المستخدم أو كلمة المرور غير صحيحة'), size_hint=(0.8,0.4))
            popup.open()

    def go_to_register(self, instance):
        self.manager.current = 'register'

class RegisterScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        self.username = TextInput(hint_text='اسم المستخدم', multiline=False)
        self.email = TextInput(hint_text='البريد الإلكتروني', multiline=False)
        self.password = TextInput(hint_text='كلمة المرور', password=True, multiline=False)
        self.confirm = TextInput(hint_text='تأكيد كلمة المرور', password=True, multiline=False)
        self.referrer = TextInput(hint_text='رمز الدعوة (اختياري)', multiline=False)
        btn_register = Button(text='تسجيل')
        btn_register.bind(on_press=self.register)
        btn_back = Button(text='رجوع')
        btn_back.bind(on_press=self.go_back)
        layout.add_widget(self.username)
        layout.add_widget(self.email)
        layout.add_widget(self.password)
        layout.add_widget(self.confirm)
        layout.add_widget(self.referrer)
        layout.add_widget(btn_register)
        layout.add_widget(btn_back)
        self.add_widget(layout)

    def register(self, instance):
        if self.password.text != self.confirm.text:
            popup = Popup(title='خطأ', content=Label(text='كلمة المرور غير متطابقة'), size_hint=(0.8,0.4))
            popup.open()
            return
        # البحث عن معرف المحيل إذا تم إدخال رمز
        referrer_id = None
        if self.referrer.text:
            conn = sqlite3.connect('relax_platform.db')
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE username=?", (self.referrer.text,))
            row = c.fetchone()
            if row:
                referrer_id = row[0]
            conn.close()
        user_id = UserManager.create_user(self.username.text, self.password.text, self.email.text, referrer_id)
        if user_id:
            popup = Popup(title='تم', content=Label(text='تم التسجيل بنجاح'), size_hint=(0.8,0.4))
            popup.open()
            self.manager.current = 'login'
        else:
            popup = Popup(title='خطأ', content=Label(text='اسم المستخدم موجود بالفعل'), size_hint=(0.8,0.4))
            popup.open()

    def go_back(self, instance):
        self.manager.current = 'login'

class HomeScreen(Screen):
    def set_user(self, user_id, username):
        self.user_id = user_id
        self.username = username
        self.update_balance_display()
        # تحديث الرصيد كل 30 ثانية
        Clock.schedule_interval(lambda dt: self.update_balance_display(), 30)

    def update_balance_display(self):
        current, locked = UserManager.get_user_balance(self.user_id)
        self.ids.balance_label.text = f"الرصيد المتاح: ${current:,.2f}\nرأس المال المحجوز: ${locked:,.2f}"

    def on_enter(self):
        self.update_balance_display()

class InvestButton(Button):
    def __init__(self, user_id, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.text = 'استثمر الآن'
        self.background_color = get_color_from_hex('#4CAF50')
        self.bind(on_press=self.invest)

    def invest(self, instance):
        if not InvestmentManager.can_invest_now():
            popup = Popup(title='تنبيه', content=Label(text='يمكنك الاستثمار فقط في الأوقات المحددة (3،5،7 مساءً)'), size_hint=(0.8,0.4))
            popup.open()
            return
        current, locked = UserManager.get_user_balance(self.user_id)
        if current <= 0:
            popup = Popup(title='تنبيه', content=Label(text='لا يوجد رصيد متاح للاستثمار'), size_hint=(0.8,0.4))
            popup.open()
            return
        # نأخذ كامل الرصيد المتاح للاستثمار
        amount = current
        InvestmentManager.schedule_investment(self.user_id, amount)
        # نقل المبلغ إلى الرصيد المحجوز
        UserManager.update_balance(self.user_id, -amount, lock=False)
        UserManager.update_balance(self.user_id, amount, lock=True)
        popup = Popup(title='تم', content=Label(text=f'تم استثمار ${amount:,.2f}. سيظهر الربح بعد 15 دقيقة.'), size_hint=(0.8,0.4))
        popup.open()

class WithdrawButton(Button):
    def __init__(self, user_id, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.text = 'سحب الأرباح'
        self.bind(on_press=self.withdraw_profit)

    def withdraw_profit(self, instance):
        if not UserManager.can_withdraw(self.user_id):
            popup = Popup(title='تنبيه', content=Label(text='يمكنك السحب مرة كل 12 ساعة'), size_hint=(0.8,0.4))
            popup.open()
            return
        current, locked = UserManager.get_user_balance(self.user_id)
        if current <= 0:
            popup = Popup(title='تنبيه', content=Label(text='لا توجد أرباح قابلة للسحب'), size_hint=(0.8,0.4))
            popup.open()
            return
        amount = current
        # سحب الأرباح فقط (هنا نفترض أن الرصيد المتاح هو الأرباح)
        # في الواقع يجب تفريق الأرباح عن رأس المال المحجوز
        UserManager.record_withdraw(self.user_id, amount, is_profit=True)
        popup = Popup(title='تم', content=Label(text=f'تم سحب ${amount:,.2f} بنجاح'), size_hint=(0.8,0.4))
        popup.open()

class TeamScreen(Screen):
    def on_enter(self):
        # عرض شجرة الإحالات
        pass

class NewsScreen(Screen):
    def on_enter(self):
        # عرض آخر الأخبار
        pass

class ContestScreen(Screen):
    def on_enter(self):
        # عرض المسابقات
        pass

class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        layout.add_widget(Label(text='الإعدادات'))
        btn_2fa = Button(text='تفعيل المصادقة الثنائية')
        btn_2fa.bind(on_press=self.enable_2fa)
        btn_verify = Button(text='توثيق الهوية')
        btn_verify.bind(on_press=self.verify_id)
        btn_lang = Button(text='تغيير اللغة')
        btn_lang.bind(on_press=self.change_lang)
        btn_back = Button(text='رجوع')
        btn_back.bind(on_press=self.go_back)
        layout.add_widget(btn_2fa)
        layout.add_widget(btn_verify)
        layout.add_widget(btn_lang)
        layout.add_widget(btn_back)
        self.add_widget(layout)

    def enable_2fa(self, instance):
        pass

    def verify_id(self, instance):
        pass

    def change_lang(self, instance):
        pass

    def go_back(self, instance):
        self.manager.current = 'home'

# =================== تطبيق Kivy الرئيسي ===================
class RelaxPlatformApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(RegisterScreen(name='register'))
        home = HomeScreen(name='home')
        home.add_widget(BoxLayout(orientation='vertical'))
        sm.add_widget(home)
        sm.add_widget(TeamScreen(name='team'))
        sm.add_widget(NewsScreen(name='news'))
        sm.add_widget(ContestScreen(name='contest'))
        sm.add_widget(SettingsScreen(name='settings'))
        return sm

if __name__ == '__main__':
    RelaxPlatformApp().run()
