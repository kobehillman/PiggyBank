import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk
from subprocess import call
import sqlite3
from CTkToolTip import CTkToolTip
from db import create_database
from decimal import Decimal
import os
from cryptography.fernet import Fernet
from datetime import datetime
from customtkinter import CTkInputDialog
import CTkMessagebox
from argon2 import PasswordHasher
import csv
import re

ph = PasswordHasher()

FERNET_KEY = b"J4xv9Y1G0hR0f3nX7M5mFqQm4E5k8PZr1WmTQ2D8x0A="
cipher = Fernet(FERNET_KEY)


def encrypt_balance(balance: str) -> bytes:
    return cipher.encrypt(balance.encode())


def decrypt_balance(encrypted_balance: bytes) -> str:
    return cipher.decrypt(encrypted_balance).decode()


def fetch_user_accounts(db_path, user_id, decrypt_balance):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""
        SELECT account_type, balance
        FROM accounts
        WHERE user_id = ?
    """, (user_id,))

    rows = c.fetchall()
    conn.close()

    accounts = {}
    for account_type, encrypted_balance in rows:
        balance = Decimal(decrypt_balance(encrypted_balance))
        accounts[account_type] = balance

    return accounts

def sign_out():
    users = sqlite3.connect('bankapp.db')
    mycursor = users.cursor()

    command = "UPDATE users set logged_in = 0 where logged_in = ?"
    mycursor.execute(command, (1,))
    users.commit()
    users.close()

    messagebox.showinfo("Sign Out", "Signing out...", parent=app)

    app.after(100, lambda: (app.destroy(), call(['python', 'login.py'])))


def cursor_on_hover(button):
    button.configure(cursor='hand2')


def reset_cursor_on_leave(button):
    button.configure(cursor='none')


# FETCH CURRENT USER_ID FROM USERS TABLE FROM BANKAPP.DB
def fetch_current_user(database):
    try:
        users = sqlite3.connect(database)
        mycursor = users.cursor()

        command = "SELECT * FROM users WHERE logged_in = 1"
        mycursor.execute(command)

        result = mycursor.fetchone()
        # result[0] = current user id

        logged_in_user = result[0]

        return logged_in_user

    except:
        logged_in_user = 'current_user'

        return logged_in_user


def fetch_current_username(database):
    try:
        conn = sqlite3.connect(database)
        mycursor = conn.cursor()
        command = "SELECT username FROM users WHERE logged_in = 1"
        mycursor.execute(command)
        result = mycursor.fetchone()
        conn.close()

        if result is not None:
            return result[0]
        else:
            return 'User'

    except Exception as e:
        print('Error fetching current username:', e)
        return 'User'


def exit_button(window):
    conn = sqlite3.connect('bankapp.db')
    mycursor = conn.cursor()

    command = "UPDATE users set logged_in = 0 where logged_in = 1"
    mycursor.execute(command)
    conn.commit()
    conn.close()

    window.destroy()


def clear_frame(frame):
    for widget in frame.winfo_children():
        widget.destroy()


class Main(ctk.CTk):

    def show_frames(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

    def __init__(self, *args, **kwargs):
        ctk.CTk.__init__(self, *args, **kwargs)
        self.wm_title('Piggy Bank')
        self.geometry('1000x600')
        self._set_appearance_mode('dark')
        self.resizable(False, False)
        self.wm_iconbitmap('resources/appicon.ico')
        self.eval("tk::PlaceWindow . center")
        self.protocol("WM_DELETE_WINDOW", lambda: exit_button(self))
        self.configure(fg_color='#2e2e2e')

        # Status label at the bottom (or wherever you want)
        self.status_label = ctk.CTkLabel(self, text="", font=("Arial", 14))
        self.status_label.pack(side="bottom", fill="x", pady=5)

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        self.db_path = os.path.join(BASE_DIR, 'bankapp.db')

        self.current_user_id = None

        self.decrypt_balance = decrypt_balance

        #  SET THE CURRENT_USER_ID ON THIS CONTROLLER
        self.current_user_id = fetch_current_user('bankapp.db')

        # GET CURRENT USERNAME
        self.current_username = fetch_current_username('bankapp.db')

        # CREATES AND PLACES FRAME FOR PAGES ON THE RIGHT SIDE
        container = ctk.CTkFrame(self, height=500, width=900, fg_color='#2e2e2e')
        container.place(x=100, y=100)

        self.frames = {}

        for F in (HomePage, TransactionPage, ProfilePage, OpenAccountPage, InfoPage, SettingsPage):
            frame = F(container, self)
            frame.configure(height=500, width=900)
            frame.place(x=0, y=0)
            frame.update_idletasks()

            self.frames[F] = frame

        # Initial startup page
        self.show_frames(HomePage)

        # ----------------- TOOLBAR BASE ----------------------- #
        toolbar_top = ctk.CTkFrame(self, height=60, width=60, fg_color='#ffb4bb')
        toolbar_top.place(x=15, y=60)

        toolbar_middle = ctk.CTkFrame(self, height=180, width=60, fg_color='#ffb4bb')
        toolbar_middle.place(x=15, y=200)

        toolbar_bottom = ctk.CTkFrame(self, height=60, width=60, fg_color='#FD9854')
        toolbar_bottom.place(x=15, y=460)

        separator_line = ctk.CTkFrame(self, height=600, width=2, fg_color="#FD9854")
        separator_line.place(x=90, y=0)

        tool_button_divider_info = ctk.CTkFrame(self, height=2, width=60, fg_color='#333a55')
        tool_button_divider_info.place(x=15, y=320)

        tool_button_divider_favorites = ctk.CTkFrame(self, height=2, width=60, fg_color='#333a55')
        tool_button_divider_favorites.place(x=15, y=260)

        # tool_button_divider_stored_passwords = ctk.CTkFrame(self, height=2, width=60, fg_color='#333a55')
        # tool_button_divider_stored_passwords.place(x=15, y=320)

        # tool_button_divider_generate_passwords = ctk.CTkFrame(self, height=2, width=60, fg_color='#333a55')
        # tool_button_divider_generate_passwords.place(x=15, y=380)

        # ----------------- TOOLBAR ICONS ----------------------- #
        info_icon = ctk.CTkImage(Image.open('resources/info_icon.png'))
        info_icon._size = 40, 40

        user_icon = ctk.CTkImage(Image.open('resources/user_icon.png'))
        user_icon._size = 40, 40

        add_icon = ctk.CTkImage(Image.open('resources/add_icon.png'))
        add_icon._size = 40, 40

        toolbar_logo = ctk.CTkImage(Image.open('resources/main_menu_logo.png'))
        toolbar_logo._size = 50, 50

        home_icon = ctk.CTkImage(Image.open('resources/home.png'))
        home_icon._size = 40, 40

        # ----------------- TOOLBAR IMAGE HOLDERS & BUTTONS ----------------------- #
        home_icon_button = ctk.CTkButton(toolbar_middle, height=40, width=40, image=home_icon,
                                         fg_color='transparent', text='', hover=False,
                                         command=lambda: self.show_frames(HomePage))
        home_icon_button.place(x=0, y=3)

        info_icon_button = ctk.CTkButton(toolbar_middle, height=60, width=60, image=info_icon, fg_color='transparent',
                                         text='', hover=False, command=lambda: self.show_frames(InfoPage))
        info_icon_button.place(x=0, y=63)

        user_icon_button = ctk.CTkButton(toolbar_middle, height=40, width=40, image=user_icon, fg_color='transparent',
                                         text='', hover=False, command=lambda: self.show_frames(ProfilePage))
        user_icon_button.place(x=2, y=126)

        add_icon_button = ctk.CTkButton(toolbar_bottom, height=40, width=40, image=add_icon, fg_color='transparent',
                                        text='', hover=False, command=lambda: self.show_frames(OpenAccountPage))
        add_icon_button.place(x=2, y=6)

        toolbar_logo_label = ctk.CTkLabel(toolbar_top, text='', image=toolbar_logo)
        toolbar_logo_label.place(x=5, y=5)

        # ----------------- TOOLBAR MISC FUNCTIONALITY ----------------------- #
        home_icon_button.bind('<Enter>', lambda event: cursor_on_hover(home_icon_button))
        home_icon_button.bind('<Leave>', lambda event: reset_cursor_on_leave(home_icon_button))

        info_icon_button.bind('<Enter>', lambda event: cursor_on_hover(info_icon_button))
        info_icon_button.bind('<Leave>', lambda event: reset_cursor_on_leave(info_icon_button))

        add_icon_button.bind('<Enter>', lambda event: cursor_on_hover(add_icon_button))
        add_icon_button.bind('<Leave>', lambda event: reset_cursor_on_leave(add_icon_button))

        user_icon_button.bind('<Enter>', lambda event: cursor_on_hover(user_icon_button))
        user_icon_button.bind('<Leave>', lambda event: reset_cursor_on_leave(user_icon_button))

        # ----------------- TOP BAR --------------------- #

        top_bar = ctk.CTkFrame(self, height=90, width=900, fg_color='#2e2e2e')
        top_bar.place(x=99, y=5)

        settings_icon = ctk.CTkImage(Image.open('resources/settings_icon.png'))
        settings_icon._size = 35, 35

        settings_icon_button = ctk.CTkButton(top_bar, image=settings_icon, fg_color='transparent', text='', hover=False,
                                             command=lambda: self.show_frames(SettingsPage))
        settings_icon_button.place(x=740, y=25)

        settings_icon_button.bind('<Enter>', lambda event: cursor_on_hover(settings_icon_button))
        settings_icon_button.bind('<Leave>', lambda event: reset_cursor_on_leave(settings_icon_button))

        settings_text = ctk.CTkLabel(top_bar, text='Settings', font=('Helvetica', 10))
        settings_text.place(x=790, y=65)

        sign_out_icon = ctk.CTkImage(Image.open('resources/sign_out_icon.png'))
        sign_out_icon._size = 33, 33

        sign_out_icon_button = ctk.CTkButton(top_bar, image=sign_out_icon, command=sign_out, fg_color='transparent',
                                             text='', hover=False, height=30, width=30)
        sign_out_icon_button.place(x=840, y=25)

        sign_out_text = ctk.CTkLabel(top_bar, text='Sign Out', font=('Helvetica', 10))
        sign_out_text.place(x=840, y=65)

        sign_out_icon_button.bind('<Enter>', lambda event: cursor_on_hover(sign_out_icon_button))
        sign_out_icon_button.bind('<Leave>', lambda event: reset_cursor_on_leave(sign_out_icon_button))

        greeting_label = ctk.CTkLabel(top_bar, text='Hello,', font=("Great Vibes", 26, "bold"), width=200)
        greeting_label.place(x=40, y=10)

        current_user = fetch_current_username('bankapp.db')

        current_user_label = ctk.CTkLabel(top_bar, text=current_user, font=("Lucida Sans", 20), width=200)
        current_user_label.place_configure(x=100, y=50)

        # -------------------- TOOLTIPS ------------------- #
        home_tooltip = CTkToolTip(home_icon_button, 'Home', delay=0.1)

        info_tooltip = CTkToolTip(info_icon_button, message='Info', delay=0.1)

        add_tooltip = CTkToolTip(add_icon_button, message='Open New Account', delay=0.1)

        user_tooltip = CTkToolTip(user_icon_button, message='My Account', delay=0.1)


# Set appearance globally
ctk.set_appearance_mode("dark")


class CenteredInputDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="Enter Amount", prompt="Amount:"):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)

        # Set icon to match parent
        if hasattr(parent, "iconbitmap"):
            self.wm_iconbitmap('resources/appicon.ico')

        self.transient(parent)
        self.grab_set()  # modal

        # Frame for input
        frame = ctk.CTkFrame(self, fg_color="#2e2e2e")
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        self.input_var = ctk.StringVar()

        label = ctk.CTkLabel(frame, text=prompt, font=("Arial", 14))
        label.pack(pady=(0, 10))

        entry = ctk.CTkEntry(frame, textvariable=self.input_var, width=200)
        entry.pack(pady=(0, 10))
        entry.focus()

        btn_frame = ctk.CTkFrame(frame, fg_color="#2e2e2e")
        btn_frame.pack(pady=(10, 0))

        ok_btn = ctk.CTkButton(btn_frame, text="OK", command=self.on_ok,
                               fg_color="#ffb4bb", hover_color="#fd5465", text_color='black', )
        ok_btn.pack(side="left", padx=(0, 10))
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", command=self.on_cancel,
                                   fg_color="red", hover_color="red", text_color='black',)
        cancel_btn.pack(side="left")

        self.value = None

        # Center dialog over parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

        self.wait_window()  # wait until closed

    def on_ok(self):
        self.value = self.input_var.get()
        self.destroy()

    def on_cancel(self):
        self.value = None
        self.destroy()

    def get_input(self):
        return self.value


class HomePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#2e2e2e")
        self.controller = controller

        self.configure(width=900, height=500)
        self.pack_propagate(False)

        # Title
        title = ctk.CTkLabel(self, text="Account Overview", font=("Arial", 22, "bold"))
        title.pack(pady=20, fill="x")

        # Accounts container
        self.accounts_frame = ctk.CTkFrame(self, fg_color="#3a3a3a")
        self.accounts_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Transactions container (optional)
        self.transactions_frame = ctk.CTkFrame(self, fg_color="#3a3a3a")
        self.transactions_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.load_accounts()
        self.load_transactions()

    def show_temporary_status(self, message, color="green", duration=5000):
        """Show a status message that disappears automatically after `duration` ms."""
        if not hasattr(self, "status_label"):
            # Create the status_label if it doesn't exist yet
            self.status_label = ctk.CTkLabel(self, text="", font=("Arial", 14))
            self.status_label.pack(pady=(0, 10), fill="x")

        self.status_label.configure(text=message, text_color=color)
        # Clear the message after `duration` milliseconds
        self.status_label.after(duration, lambda: self.status_label.configure(text=""))

    def load_accounts(self):
        for widget in self.accounts_frame.winfo_children():
            widget.destroy()

        username = getattr(self.controller, "current_username", None)
        if not username:
            return

        accounts = fetch_user_accounts(self.controller.db_path, username, self.controller.decrypt_balance)
        if not accounts:
            no_account_label = ctk.CTkLabel(
                self.accounts_frame,
                text="No accounts found. Open an account to get started.",
                font=("Arial", 14)
            )
            no_account_label.pack(pady=20)
            return

        for account_type, balance in accounts.items():
            self.create_account_card(account_type, balance)

    def deposit(self, account_type):
        # Ask user for amount
        dialog = CenteredInputDialog(self.controller, title="Deposit Funds",
                                     prompt=f"Enter deposit amount for {account_type}:")
        amount_str = dialog.get_input()
        if not amount_str:
            return

        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            CTkMessagebox.CTkMessagebox(title="Invalid Input", message="Please enter a valid positive number.", icon="warning")
            return

        conn = sqlite3.connect(self.controller.db_path)
        cursor = conn.cursor()

        # Get current balance
        cursor.execute("SELECT balance FROM accounts WHERE user_id=? AND account_type=?",
                       (self.controller.current_username, account_type.upper()))
        current_balance_enc = cursor.fetchone()[0]
        current_balance = float(decrypt_balance(current_balance_enc))

        # Update balance
        new_balance = current_balance + amount
        cursor.execute("UPDATE accounts SET balance=? WHERE user_id=? AND account_type=?",
                       (encrypt_balance(f"{new_balance:.2f}"),
                        self.controller.current_username,
                        account_type.upper()))

        # Insert transaction
        cursor.execute("""
            INSERT INTO transactions (user_id, account_type, type, amount, timestamp)
            VALUES (?, ?, 'Deposit', ?, CURRENT_TIMESTAMP)
        """, (self.controller.current_username, account_type.upper(), amount))

        conn.commit()
        conn.close()

        self.load_accounts()
        self.load_transactions()  # refresh recent transactions display

    def withdraw(self, account_type):
        dialog = CenteredInputDialog(self.controller, title="Withdraw Funds",
                                     prompt=f"Enter withdrawal amount for {account_type}:")
        amount_str = dialog.get_input()
        if not amount_str:
            return

        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            CTkMessagebox.CTkMessagebox(title="Invalid Input", message="Please enter a valid positive number.", icon="warning")
            return

        conn = sqlite3.connect(self.controller.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT balance FROM accounts WHERE user_id=? AND account_type=?",
                       (self.controller.current_username, account_type.upper()))
        current_balance_enc = cursor.fetchone()[0]
        current_balance = float(decrypt_balance(current_balance_enc))

        if amount > current_balance:
            CTkMessagebox.CTkMessagebox(title="Insufficient Funds", message="You do not have enough funds.", icon="warning")
            conn.close()
            return

        new_balance = current_balance - amount
        cursor.execute("UPDATE accounts SET balance=? WHERE user_id=? AND account_type=?",
                       (encrypt_balance(f"{new_balance:.2f}"),
                        self.controller.current_username,
                        account_type.upper()))

        # Insert transaction
        cursor.execute("""
            INSERT INTO transactions (user_id, account_type, type, amount, timestamp)
            VALUES (?, ?, 'Withdrawal', ?, CURRENT_TIMESTAMP)
        """, (self.controller.current_username, account_type.upper(), amount))

        conn.commit()
        conn.close()

        self.load_accounts()
        self.load_transactions()

    def create_account_card(self, account_type, balance):
        card = ctk.CTkFrame(self.accounts_frame, fg_color="#4a4a4a", corner_radius=10)
        card.pack(fill="x", pady=10, padx=10)

        account_label = ctk.CTkLabel(card, text=f"{account_type.capitalize()} Account", font=("Arial", 16, "bold"))
        account_label.pack(anchor="w", padx=15, pady=(10, 0))

        balance_label = ctk.CTkLabel(card, text=f"Balance: ${balance:,.2f}", font=("Arial", 15))
        balance_label.pack(anchor="w", padx=15, pady=(5, 10))

        btn_frame = ctk.CTkFrame(card, fg_color="#4a4a4a")
        btn_frame.pack(anchor="w", padx=15, pady=(0, 10))

        deposit_btn = ctk.CTkButton(btn_frame, text="Deposit", text_color='black', width=80, fg_color='#ffb4bb',
                                    hover_color='#fd5465',
                                    command=lambda: self.deposit(account_type))
        deposit_btn.pack(side="left", padx=(0, 10))

        withdraw_btn = ctk.CTkButton(btn_frame, text="Withdraw", text_color='black', width=80, fg_color='#ffb4bb',
                                     hover_color='#fd5465',
                                     command=lambda: self.withdraw(account_type))
        withdraw_btn.pack(side="left")

    def load_transactions(self):
        import sqlite3

        # Clear previous transaction widgets
        for widget in self.transactions_frame.winfo_children():
            widget.destroy()

        username = getattr(self.controller, "current_username", None)
        if not username:
            return

        conn = sqlite3.connect(self.controller.db_path)
        cursor = conn.cursor()

        # Fetch last 10 transactions, newest first
        cursor.execute("""
            SELECT account_type, type, amount, timestamp
            FROM transactions
            WHERE user_id=?
            ORDER BY timestamp DESC
            LIMIT 10
        """, (username,))
        transactions = cursor.fetchall()
        conn.close()

        if not transactions:
            no_trans_label = ctk.CTkLabel(
                self.transactions_frame,
                text="No recent transactions.",
                font=("Arial", 14)
            )
            no_trans_label.pack(pady=10)
            return

        # Scrollable frame for transactions
        scrollable_frame = ctk.CTkScrollableFrame(self.transactions_frame, fg_color="#3a3a3a")
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        for trans in transactions:
            acc_type, trans_type, amount, timestamp = trans
            card = ctk.CTkFrame(scrollable_frame, fg_color="#4a4a4a", corner_radius=8)
            card.pack(fill="x", pady=5, padx=5)

            label = ctk.CTkLabel(
                card,
                text=f"{timestamp} | {acc_type.capitalize()} | {trans_type}: ${float(amount):,.2f}",
                font=("Arial", 13),
                anchor="w"
            )
            label.pack(fill="x", padx=10, pady=5)


class TransactionPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        ctk.CTkFrame.__init__(self, parent, fg_color='#2e2e2e')
        button = ctk.CTkButton(self, text='TransactionPage')
        button.place(x=50, y=100)


class OpenAccountPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#2e2e2e")
        self.controller = controller

        # Force frame size
        self.configure(width=900, height=500)
        self.pack_propagate(False)  # prevent shrinking

        # Container to center widgets
        container = ctk.CTkFrame(self, fg_color="#2e2e2e")
        container.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        title = ctk.CTkLabel(
            container,
            text="Open Account",
            font=("Arial", 22, "bold")
        )
        title.pack(pady=(0, 30), fill="x")

        # Grouped frame for checkboxes
        accounts_container = ctk.CTkFrame(container, fg_color="#3a3a3a", corner_radius=10)
        accounts_container.pack(pady=(0, 20), padx=50, fill="x")

        # Checkboxes
        self.checking_var = ctk.BooleanVar(value=False)
        self.savings_var = ctk.BooleanVar(value=False)

        self.checking_cb = ctk.CTkCheckBox(
            accounts_container,
            text="Checking Account",
            variable=self.checking_var,
            fg_color="#ffb4bb",
            hover_color='#fd5465',
            font=("Arial", 14),
            command=self.update_open_button_state  # enable/disable button on toggle
        )
        self.checking_cb.pack(pady=10, anchor="w", padx=15)

        self.savings_cb = ctk.CTkCheckBox(
            accounts_container,
            text="Savings Account",
            variable=self.savings_var,
            fg_color="#ffb4bb",
            hover_color='#fd5465',
            font=("Arial", 14),
            command=self.update_open_button_state
        )
        self.savings_cb.pack(pady=10, anchor="w", padx=15)

        # Open account button
        self.open_btn = ctk.CTkButton(
            container,
            text="Open Account(s)",
            text_color='black',
            command=self.open_account,
            height=50,
            fg_color='#ffb4bb',
            hover_color='#fd5465',
            font=("Arial", 16, "bold"),
            state="disabled"  # starts disabled
        )
        self.open_btn.pack(pady=(0, 20), fill="x", padx=100)

        # Status label
        self.status_label = ctk.CTkLabel(container, text="", font=("Arial", 14))
        self.status_label.pack(pady=(0, 10), fill="x")

    def update_open_button_state(self):
        """Enable the open button only if at least one checkbox is selected"""
        if self.checking_var.get() or self.savings_var.get():
            self.open_btn.configure(state="normal")
        else:
            self.open_btn.configure(state="disabled")

    def open_account(self):
        import sqlite3

        # Fetch the actual username instead of using current_user_id placeholder
        user_name = self.controller.current_username

        account_types = []
        if self.checking_var.get():
            account_types.append("checking")
        if self.savings_var.get():
            account_types.append("savings")

        # Extra validation just in case
        if not account_types:
            self.status_label.configure(
                text="Select at least one account type.",
                text_color="red"
            )
            return

        try:
            conn = sqlite3.connect('bankapp.db')
            cursor = conn.cursor()

            opened = []
            for acc_type in account_types:
                acc_type_upper = acc_type.upper()  # match CHECK constraint ('CHECKING'/'SAVINGS')

                # Prevent duplicate accounts
                cursor.execute("""
                    SELECT 1 FROM accounts
                    WHERE user_id = ? AND account_type = ?
                """, (user_name, acc_type_upper))

                if cursor.fetchone():
                    continue  # skip already existing accounts

                encrypted_balance = encrypt_balance("0.00")
                cursor.execute("""
                    INSERT INTO accounts (user_id, account_type, balance)
                    VALUES (?, ?, ?)
                """, (user_name, acc_type_upper, encrypted_balance))
                opened.append(acc_type_upper)

            conn.commit()
            conn.close()

            if opened:
                self.status_label.configure(
                    text=f"Opened account(s): {', '.join(opened)}",
                    text_color="green"
                )
                # Refresh home page to show new accounts
                self.controller.frames[HomePage].load_accounts()
            else:
                self.status_label.configure(
                    text="Selected account(s) already exist.",
                    text_color="orange"
                )

        except Exception as e:
            print("Open account error:", e)
            self.status_label.configure(
                text="Failed to open account(s).",
                text_color="red"
            )

            if opened:
                self.status_label.configure(
                    text=f"Opened account(s): {', '.join(opened)}",
                    text_color="green"
                )
                # Refresh HomePage to show new accounts
                self.controller.frames[HomePage].load_accounts()
                # Reset checkboxes and disable button
                self.checking_var.set(False)
                self.savings_var.set(False)
                self.update_open_button_state()
            else:
                self.status_label.configure(
                    text="Selected account(s) already exist.",
                    text_color="orange"
                )

        except Exception as e:
            print("Open account error:", e)
            self.status_label.configure(
                text="Failed to open account(s).",
                text_color="red"
            )


class ProfilePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#2e2e2e")
        self.controller = controller

        self.configure(width=900, height=500)
        self.pack_propagate(False)

        title = ctk.CTkLabel(self, text="Profile", font=("Arial", 22, "bold"))
        title.pack(pady=20)

        self.card = ctk.CTkFrame(self, fg_color="#3a3a3a", corner_radius=10)
        self.card.pack(padx=40, pady=10, fill="both", expand=True)

        self.email_label = ctk.CTkLabel(self.card, font=("Arial", 15))
        self.email_label.pack(anchor="w", padx=25, pady=(25, 5))

        self.member_label = ctk.CTkLabel(self.card, font=("Arial", 15))
        self.member_label.pack(anchor="w", padx=25, pady=5)

        self.account_count_label = ctk.CTkLabel(self.card, font=("Arial", 15))
        self.account_count_label.pack(anchor="w", padx=25, pady=5)

        self.transaction_count_label = ctk.CTkLabel(self.card, font=("Arial", 15))
        self.transaction_count_label.pack(anchor="w", padx=25, pady=5)

        divider = ctk.CTkFrame(self.card, height=2, fg_color="#555555")
        divider.pack(fill="x", padx=20, pady=20)

        btn_frame = ctk.CTkFrame(self.card, fg_color="#3a3a3a")
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="Change Email", fg_color="#ffb4bb", hover_color="#fd5465", text_color='black',
                      width=180, command=self.change_email).pack(side="left", padx=10)

        ctk.CTkButton(btn_frame, text="Change Password", fg_color="#ffb4bb", hover_color="#fd5465", text_color='black',
                      width=180, command=self.change_password).pack(side="left", padx=10)

        ctk.CTkButton(btn_frame, text="Export Transactions", fg_color="#ffb4bb",
                      hover_color="#fd5465", text_color='black',
                      width=180, command=self.export_transactions).pack(side="left", padx=10)

        ctk.CTkButton(btn_frame, text="Delete Account", text_color='black',
                      width=180, fg_color="#8b0000",
                      hover_color="#a30000",
                      command=self.delete_account).pack(side="left", padx=10)

        self.load_profile()

    # ---------------- PROFILE DATA ---------------- #

    def load_profile(self):
        conn = sqlite3.connect(self.controller.db_path)
        cur = conn.cursor()

        username = self.controller.current_username

        # Fetch user info
        cur.execute("""
            SELECT email, created_at
            FROM users
            WHERE username = ?
        """, (username,))
        row = cur.fetchone()

        if row:
            email, created_at = row
            # Parse the created_at timestamp safely
            try:
                created_date = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S").strftime("%m/%d/%Y")
            except Exception:
                created_date = created_at  # fallback if parsing fails
        else:
            email = "N/A"
            created_date = "Unknown"

        # Fetch account count
        cur.execute("SELECT COUNT(*) FROM accounts WHERE user_id = ?", (username,))
        account_count_row = cur.fetchone()
        account_count = account_count_row[0] if account_count_row else 0

        # Fetch transaction count
        cur.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ?", (username,))
        transaction_count_row = cur.fetchone()
        transaction_count = transaction_count_row[0] if transaction_count_row else 0

        conn.close()

        # Update UI labels
        self.email_label.configure(text=f"Email: {email}")
        self.member_label.configure(text=f"Member since {created_date}")
        self.account_count_label.configure(text=f"Accounts: {account_count}")
        self.transaction_count_label.configure(text=f"Total transactions: {transaction_count}")

    # ---------------- ACTIONS ---------------- #

    def change_email(self):
        # Open the centered dialog
        dialog = CenteredInputDialog(
            self.controller,
            title="Change Email",
            prompt="Enter new email:"
        )
        new_email = dialog.get_input()
        if not new_email:
            return  # user cancelled

        # Validate email format
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_regex, new_email):
            CTkMessagebox.CTkMessagebox(title="Invalid Email", message="Please enter a valid email address.", icon="warning")
            return

        # Update in the database
        conn = sqlite3.connect(self.controller.db_path)
        cur = conn.cursor()
        cur.execute("UPDATE users SET email = ? WHERE username = ?", (new_email, self.controller.current_username))
        conn.commit()
        conn.close()

        # Refresh profile display
        self.load_profile()
        CTkMessagebox.CTkMessagebox(title='Change Email', message="Email changed successfully.", icon="success")

    def change_password(self):
        dialog = CenteredInputDialog(self.controller, title="Change Password", prompt="Enter new password:")
        new_password = dialog.get_input()

        if not new_password:
            return

        hashed = ph.hash(new_password)

        conn = sqlite3.connect(self.controller.db_path)
        cur = conn.cursor()
        cur.execute("UPDATE users SET password_hash=? WHERE username=?",
                    (hashed, self.controller.current_username))
        conn.commit()
        conn.close()

        CTkMessagebox.CTkMessagebox(title="Success", message="Password updated.", icon="success")

    def export_transactions(self):
        conn = sqlite3.connect(self.controller.db_path)
        cur = conn.cursor()

        cur.execute("""
            SELECT account_type, amount, type, timestamp
            FROM transactions
            WHERE user_id = ?
            ORDER BY timestamp DESC
        """, (self.controller.current_username,))

        rows = cur.fetchall()
        conn.close()

        if not rows:
            CTkMessagebox.CTkMessagebox(title="No Data", message="No transactions to export.", icon="info")
            return

        with open("transactions_export.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Account", "Amount", "Type", "Timestamp"])
            writer.writerows(rows)

        CTkMessagebox.CTkMessagebox(title="Export Complete",
                      message="Transactions exported to transactions_export.csv",
                      icon="check")

    def delete_account(self):
        confirm = CTkMessagebox.CTkMessagebox(
            title="Confirm Delete",
            message="This will permanently delete your account.\nAre you sure?",
            icon="warning",
            option_1="Cancel",
            option_2="Delete"
        )

        if confirm.get() != "Delete":
            return

        pw_dialog = CenteredInputDialog(self.controller, title="Confirm Password", prompt="Enter your password:")
        password = pw_dialog.get_input()
        if not password:
            return

        conn = sqlite3.connect(self.controller.db_path)
        cur = conn.cursor()

        cur.execute("SELECT password_hash FROM users WHERE username=?",
                    (self.controller.current_username,))
        stored_hash = cur.fetchone()[0]

        try:
            ph.verify(stored_hash, password)
        except:
            CTkMessagebox.CTkMessagebox(title="Error", message="Incorrect password.", icon="cancel")
            conn.close()
            return

        cur.execute("DELETE FROM transactions WHERE user_id=?", (self.controller.current_username,))
        cur.execute("DELETE FROM accounts WHERE user_id=?", (self.controller.current_username,))
        cur.execute("DELETE FROM users WHERE username=?", (self.controller.current_username,))

        conn.commit()
        conn.close()

        CTkMessagebox.CTkMessagebox(title="Account Deleted",
                      message="Your account has been removed.",
                      icon="check")

        self.controller.destroy()

class InfoPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#2e2e2e")
        self.controller = controller

        # Force frame size
        self.configure(width=900, height=500)
        self.pack_propagate(False)  # prevent shrinking to fit widgets

        # Container to center content
        container = ctk.CTkFrame(self, fg_color="#2e2e2e")
        container.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        title = ctk.CTkLabel(
            container,
            text="Welcome to Piggy Bank",
            font=("Arial", 24, "bold")
        )
        title.pack(pady=(0, 20), fill="x")

        # Brief description
        description_text = (
            "Piggy Bank is your personal banking companion, designed to make managing "
            "your money simple, secure, and efficient. Keep track of your balances, "
            "open new accounts, and perform transactions with ease."
        )
        description_label = ctk.CTkLabel(
            container,
            text=description_text,
            font=("Arial", 14),
            wraplength=800,
            justify="center"
        )
        description_label.pack(pady=(0, 20), fill="x")

        # Key features
        features_title = ctk.CTkLabel(
            container,
            text="Key Features",
            font=("Arial", 18, "bold")
        )
        features_title.pack(pady=(0, 10), fill="x")

        features = [
            "• Secure storage of checking and savings accounts",
            "• Real-time balance overview with automatic updates",
            "• Ability to open multiple account types",
            "• User-friendly interface with a sleek toolbar",
            "• Encrypted balances to protect your financial data"
        ]

        for feature in features:
            feature_label = ctk.CTkLabel(
                container,
                text=feature,
                font=("Arial", 14),
                wraplength=800,
                justify="left"
            )
            feature_label.pack(anchor="w", padx=20, pady=2)

class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#2e2e2e")
        self.controller = controller

        # Force frame size
        self.configure(width=900, height=500)
        self.pack_propagate(False)

        # Title
        title = ctk.CTkLabel(
            self,
            text="Settings",
            font=("Arial", 22, "bold")
        )
        title.pack(pady=20, fill="x")

        # Container for settings options
        container = ctk.CTkFrame(self, fg_color="#3a3a3a", corner_radius=10)
        container.pack(pady=20, padx=50, fill="both", expand=True)

        # Appearance Mode
        appearance_label = ctk.CTkLabel(container, text="Appearance Mode:", font=("Arial", 14, "bold"))
        appearance_label.pack(pady=(20, 5), anchor="w", padx=15)

        self.appearance_option = ctk.StringVar(value=ctk.get_appearance_mode())
        appearance_menu = ctk.CTkOptionMenu(
            container,
            values=["Dark", "Light", "System"],
            variable=self.appearance_option,
            fg_color="#ffb4bb",
            dropdown_fg_color='#ffb4bb',
            dropdown_hover_color='#fd5465',
            dropdown_text_color='black',
            button_color='#ffb4bb',
            button_hover_color='#fd5465',
            text_color='black',
            command=self.change_appearance
        )
        appearance_menu.pack(pady=(0, 20), padx=15, anchor="w")

        # Notification Settings (example)
        notifications_label = ctk.CTkLabel(container, text="Notifications:", font=("Arial", 14, "bold"))
        notifications_label.pack(pady=(0, 5), anchor="w", padx=15)

        self.notifications_var = ctk.BooleanVar(value=True)
        notifications_cb = ctk.CTkCheckBox(
            container,
            text="Enable notifications",
            fg_color="#ffb4bb",
            hover_color='#fd5465',
            variable=self.notifications_var
        )
        notifications_cb.pack(pady=(0, 20), padx=15, anchor="w")

        # Save button
        save_btn = ctk.CTkButton(
            container,
            text="Save Settings",
            command=self.save_settings,
            height=40,
            fg_color="#ffb4bb",
            hover_color="#fd5465",
            text_color='black',
            font=("Arial", 14, "bold")
        )
        save_btn.pack(pady=(10, 20), padx=15, anchor="center")

        # Status label
        self.status_label = ctk.CTkLabel(container, text="", font=("Arial", 12))
        self.status_label.pack(pady=(0, 10))

    def change_appearance(self, choice):
        """Change the global appearance mode."""
        ctk.set_appearance_mode(choice)

    def save_settings(self):
        # For now, just show status label feedback
        self.status_label.configure(text="Settings saved!", text_color="green")
        self.after(5000, lambda: self.status_label.configure(text=""))  # disappear after 5 seconds



if __name__ == '__main__':
    create_database()
    app = Main()
    app.mainloop()









