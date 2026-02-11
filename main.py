import flet as ft
import uuid
import hashlib
import requests
import threading
from datetime import datetime

# --- CONFIG ---
TELEGRAM_BOT_TOKEN = "8283768042:AAFZ_5OXTS-1SCDuV9m9ixhmZYDMXbny9b0" # Ganti Token Lo
TELEGRAM_CHAT_ID = "5642195388" # Ganti ID Lo
SECRET_SALT = "CROWN_WIN_TRICKS_SECRET"

class CasinoApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "3 Patti Crown Win Tricks"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.scroll = "adaptive"
        self.page.bgcolor = "#1e272e"
        self.page.window_width = 400
        self.page.window_height = 800
        
        # VARIABLES
        self.history = []
        self.start_capital = 0
        self.base_bet = 0
        self.current_bet = 0
        self.current_balance = 0
        self.profit = 0
        self.target_profit = 0
        self.martingale_step = 1
        self.last_pred = None
        
        self.device_id = self.get_or_create_device_id()
        self.init_login_ui()

    def get_or_create_device_id(self):
        stored_id = self.page.client_storage.get("device_id")
        if not stored_id:
            stored_id = str(uuid.uuid4())[:8].upper()
            self.page.client_storage.set("device_id", stored_id)
        return stored_id

    def verify_key(self, input_key):
        data = self.device_id + SECRET_SALT
        generated = hashlib.md5(data.encode()).hexdigest().upper()
        valid_key = f"{generated[:4]}-{generated[4:8]}"
        return input_key == valid_key

    def send_report(self, ref_id):
        def _send():
            try:
                msg = f"📱 **LOGIN SUCCESS!**\nApp: 3 Patti Crown\nUser: {ref_id}\nID: {self.device_id}\nTime: {datetime.now()}"
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
            except: pass
        threading.Thread(target=_send).start()

    # ================= UI SECTIONS =================

    def init_login_ui(self):
        self.page.clean()
        
        self.txt_ref = ft.TextField(label="Game ID / Referral", text_align="center", width=300, border_color="#f1c40f")
        self.txt_key = ft.TextField(label="License Key", text_align="center", width=300, border_color="#f1c40f")
        self.lbl_id = ft.Text(f"DEVICE ID: {self.device_id}", color="grey", size=12)
        
        btn_login = ft.ElevatedButton(
            "CONNECT SERVER 🔓", 
            on_click=self.login_click, 
            bgcolor="#27ae60", color="white", width=300, height=50
        )

        self.page.add(
            ft.Column(
                [
                    ft.Icon(ft.icons.DIAMOND_OUTLINED, size=60, color="#f1c40f"),
                    ft.Text("3 Patti Crown", size=30, weight="bold", color="#f1c40f"),
                    ft.Text("Win Tricks V1.0", size=16, color="white"),
                    ft.Divider(height=20, color="transparent"),
                    self.lbl_id,
                    self.txt_ref,
                    self.txt_key,
                    ft.Divider(height=20, color="transparent"),
                    btn_login,
                    ft.Text("Contact Admin to buy key", size=10, color="grey")
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10
            )
        )

    def init_main_ui(self):
        self.page.clean()
        
        # INPUT MODAL
        self.txt_modal = ft.TextField(label="Capital (Rs)", value="100000", width=140, text_size=12)
        self.txt_base = ft.TextField(label="Base Bet", value="2000", width=100, text_size=12)
        self.btn_lock = ft.ElevatedButton("LOCK", on_click=self.lock_click, bgcolor="#0984e3", color="white", width=80)

        row_setup = ft.Row([self.txt_modal, self.txt_base, self.btn_lock], alignment=ft.MainAxisAlignment.CENTER)

        # DASHBOARD
        self.lbl_balance = ft.Text("BAL: Rs 0", size=18, weight="bold", color="#00b894")
        self.lbl_profit = ft.Text("Profit: 0 (Target 60%)", size=14, color="#f1c40f")
        
        card_dash = ft.Container(
            content=ft.Column([self.lbl_balance, self.lbl_profit], alignment="center", horizontal_alignment="center"),
            padding=15, bgcolor="black", border_radius=10, width=350
        )

        # PREDIKSI (Updated Label)
        self.lbl_pred = ft.Text("SETUP FIRST", size=35, weight="bold", color="grey")
        self.lbl_amount = ft.Text("Rs 0", size=20, color="#00cec9")
        self.lbl_status = ft.Text("Waiting...", color="grey")

        card_main = ft.Container(
            content=ft.Column([
                ft.Text("PREDICTION:", size=14, color="#bdc3c7", weight="bold"), # <-- LABEL BARU
                self.lbl_pred,
                self.lbl_amount,
                self.lbl_status
            ], alignment="center", horizontal_alignment="center"),
            padding=20, bgcolor="#2d3436", border_radius=10, width=350, height=220
        )

        # TOMBOL WIN/LOSS
        self.btn_win = ft.ElevatedButton("✅ WIN", on_click=self.win_click, bgcolor="#27ae60", color="white", width=150, height=50, disabled=True)
        self.btn_loss = ft.ElevatedButton("❌ LOSS", on_click=self.loss_click, bgcolor="#c0392b", color="white", width=150, height=50, disabled=True)
        
        row_action = ft.Row([self.btn_win, self.btn_loss], alignment=ft.MainAxisAlignment.CENTER)

        # HISTORY & MANUAL
        self.lbl_history = ft.Text("---", font_family="monospace", size=16, color="white")
        
        btn_d = ft.ElevatedButton("D", on_click=lambda e: self.manual_input("D"), bgcolor="#ff7675", width=60)
        btn_t = ft.ElevatedButton("T", on_click=lambda e: self.manual_input("T"), bgcolor="#74b9ff", width=60)
        btn_x = ft.ElevatedButton("Tie", on_click=lambda e: self.manual_input("X"), bgcolor="#55efc4", width=60)
        
        row_manual = ft.Row([btn_d, btn_x, btn_t], alignment=ft.MainAxisAlignment.CENTER)
        btn_reset = ft.ElevatedButton("RESET GAME", on_click=self.reset_click, bgcolor="#e67e22", color="white", width=300)

        self.page.add(
            ft.Column([
                ft.Text("3 PATTI CROWN WIN", size=18, weight="bold", color="#f39c12"),
                row_setup,
                card_dash,
                card_main,
                row_action,
                ft.Divider(),
                ft.Text("Manual Input (First 3):", size=10),
                self.lbl_history,
                row_manual,
                ft.Divider(),
                btn_reset
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
        )

    # ================= LOGIC FUNCTIONS =================
    def login_click(self, e):
        ref = self.txt_ref.value
        key = self.txt_key.value
        if not ref:
            self.page.snack_bar = ft.SnackBar(ft.Text("Input Referral ID!"))
            self.page.snack_bar.open = True
            self.page.update()
            return
        if self.verify_key(key):
            self.send_report(ref)
            self.init_main_ui()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Invalid Key!"))
            self.page.snack_bar.open = True
            self.page.update()

    def lock_click(self, e):
        try:
            self.start_capital = int(self.txt_modal.value)
            self.base_bet = int(self.txt_base.value)
            self.current_balance = self.start_capital
            self.current_bet = self.base_bet
            self.target_profit = int(self.start_capital * 0.60) # 60% Target
            
            self.txt_modal.disabled = True
            self.txt_base.disabled = True
            self.btn_lock.disabled = True
            self.btn_win.disabled = False
            self.btn_loss.disabled = False
            self.update_ui()
            self.run_logic()
        except: pass

    def update_ui(self):
        self.lbl_balance.value = f"BAL: Rs {self.current_balance:,}"
        if self.profit >= self.target_profit:
            self.lbl_profit.value = "TARGET REACHED! WITHDRAW!"
            self.lbl_profit.color = "#00ff00"
            self.lbl_pred.value = "STOP"
            self.lbl_pred.color = "red"
            self.btn_win.disabled = True
            self.btn_loss.disabled = True
        else:
            self.lbl_profit.value = f"Profit: {self.profit:,} (Target: {self.target_profit:,})"
            self.lbl_profit.color = "#f1c40f"
        
        hist_str = " ".join(self.history[-10:])
        self.lbl_history.value = hist_str
        self.page.update()

    def manual_input(self, val):
        self.history.append(val)
        self.update_ui()
        self.run_logic()

    def win_click(self, e):
        if not self.last_pred or self.last_pred == "WAIT": return
        self.profit += self.current_bet
        self.current_balance += self.current_bet
        self.martingale_step = 1
        self.current_bet = self.base_bet
        self.history.append("D" if self.last_pred == "DRAGON" else "T")
        self.update_ui()
        self.run_logic()

    def loss_click(self, e):
        if not self.last_pred or self.last_pred == "WAIT": return
        self.profit -= self.current_bet
        self.current_balance -= self.current_bet
        self.martingale_step += 1
        self.current_bet *= 2
        actual = "T" if self.last_pred == "DRAGON" else "D"
        self.history.append(actual)
        self.update_ui()
        self.run_logic()

    def reset_click(self, e):
        self.init_main_ui()

    def run_logic(self):
        data = [x for x in self.history if x != 'X']
        pred = "WAIT"
        color = "grey"
        if len(data) >= 3:
            last_1 = data[-1]
            if data[-3:] == [last_1] * 3:
                pred = "DRAGON" if last_1 == 'D' else "TIGER"
                color = "#ff7675" if pred == "DRAGON" else "#74b9ff"
            elif data[-1] != data[-2] and data[-2] != data[-3]:
                pred = "TIGER" if last_1 == 'D' else "DRAGON"
                color = "#74b9ff" if pred == "TIGER" else "#ff7675"
        self.last_pred = pred
        self.lbl_pred.value = pred
        self.lbl_pred.color = color
        if pred == "WAIT":
            self.lbl_amount.value = "DO NOT BET"
            self.lbl_status.value = "Waiting for pattern..."
            self.btn_win.disabled = True
            self.btn_loss.disabled = True
        else:
            self.lbl_amount.value = f"Bet: Rs {self.current_bet:,}"
            self.lbl_status.value = "Pattern Detected!"
            self.btn_win.disabled = False
            self.btn_loss.disabled = False
        self.page.update()

def main(page: ft.Page):
    CasinoApp(page)

ft.app(target=main)