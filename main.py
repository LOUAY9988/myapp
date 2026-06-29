import os
import json
import requests
import threading
from functools import partial

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout

from kivymd.app import MDApp
from kivymd.uix.toolbar import MDToolbar
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDIconButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog

# Files
HISTORY_FILE = "chat_history.json"
CONFIG_FILE = "config.json"

# Gemini API endpoint (key will be read from config at runtime)
API_ENDPOINT_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={}"
)


def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_history(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


class ChatScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=0, **kwargs)

        # Toolbar
        self.toolbar = MDToolbar(title="MyApp", elevation=10)
        self.toolbar.left_action_items = [["menu", lambda x: None]]
        self.toolbar.right_action_items = [["cog", lambda x: self.open_settings()], ["theme-light-dark", lambda x: self.toggle_theme()]]
        self.add_widget(self.toolbar)

        # Scroll area for chat
        self.scroll = ScrollView(size_hint=(1, 1))
        self.chat_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8), padding=dp(10))
        self.chat_box.bind(minimum_height=self.chat_box.setter("height"))
        self.scroll.add_widget(self.chat_box)
        self.add_widget(self.scroll)

        # Input row
        input_row = BoxLayout(size_hint=(1, None), height=dp(64), padding=[dp(8), dp(8), dp(8), dp(8)])
        self.text_input = MDTextField(hint_text="اكتب رسالتك...", size_hint=(0.8, 1), multiline=False)
        send_btn = MDIconButton(icon="send", size_hint=(0.2, 1))
        send_btn.bind(on_release=self.on_send)
        self.text_input.bind(on_text_validate=self.on_send)
        input_row.add_widget(self.text_input)
        input_row.add_widget(send_btn)
        self.add_widget(input_row)

        # State
        self.history = load_history()
        self.config = load_config()
        self._dialog = None

        # Add existing messages
        for msg in self.history:
            self.add_bubble(msg.get("role", "model"), msg.get("text", ""))

    def add_bubble(self, role, text):
        # role: 'user' or 'model'
        align_right = role == "user"
        card = MDCard(size_hint=(None, None), padding=dp(8), radius=[dp(12)], elevation=2)
        # Width: adapt to Window width (max 80% of width)
        max_w = Window.width * 0.8
        label = MDLabel(text=text, halign="right" if align_right else "left", size_hint=(None, None), theme_text_color="Primary")
        # measure label
        label.text_size = (max_w - dp(24), None)
        label.texture_update()
        label_size = (min(max_w, label.texture_size[0]), label.texture_size[1])
        label.size = (label_size[0], label_size[1])
        card.size = (label.size[0] + dp(24), label.size[1] + dp(16))
        if align_right:
            # align to right by adding a container
            container = BoxLayout(size_hint=(1, None), height=card.height)
            container.add_widget(BoxLayout())
            container.add_widget(card)
            card.add_widget(label)
            self.chat_box.add_widget(container)
        else:
            container = BoxLayout(size_hint=(1, None), height=card.height)
            container.add_widget(card)
            card.add_widget(label)
            container.add_widget(BoxLayout())
            self.chat_box.add_widget(container)

        Clock.schedule_once(lambda dt: self.scroll_to_bottom(), 0.05)

    def scroll_to_bottom(self):
        # scroll to bottom
        try:
            self.scroll.scroll_y = 0
        except Exception:
            pass

    def on_send(self, instance):
        text = self.text_input.text.strip()
        if not text:
            return
        self.text_input.text = ""
        self.add_bubble("user", text)
        self.history.append({"role": "user", "text": text})
        save_history(self.history)
        # call network in thread
        threading.Thread(target=self.call_gemini, args=(text,), daemon=True).start()

    def call_gemini(self, text):
        cfg = load_config()
        api_key = cfg.get("API_KEY")
        if not api_key:
            # show settings dialog on main thread
            Clock.schedule_once(lambda dt: self.show_message("مطلوب API key", "يرجى ضبط مفتاح الـ API في الإعدادات."), 0)
            return

        url = API_ENDPOINT_TEMPLATE.format(api_key)
        payload = {"contents": [{"parts": [{"text": text}] }]}
        try:
            r = requests.post(url, json=payload, timeout=30)
            r.raise_for_status()
            data = r.json()
            reply = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        except Exception as e:
            reply = f"خطأ: {e}"

        # schedule UI update
        Clock.schedule_once(partial(self._add_model_reply, reply), 0)

    def _add_model_reply(self, reply, dt):
        self.add_bubble("model", reply)
        self.history.append({"role": "model", "text": reply})
        save_history(self.history)

    def open_settings(self):
        cfg = load_config()
        api_val = cfg.get("API_KEY", "")
        self.api_field = MDTextField(hint_text="API Key", text=api_val, size_hint=(1, None), height=dp(48))
        save_btn = MDFlatButton(text="حفظ", on_release=self.save_settings)
        cancel_btn = MDFlatButton(text="إلغاء", on_release=lambda x: self._dialog.dismiss())
        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))
        content.add_widget(self.api_field)
        self._dialog = MDDialog(title="إعدادات", type="custom", content_cls=content, buttons=[save_btn, cancel_btn])
        self._dialog.open()

    def save_settings(self, instance):
        cfg = load_config()
        cfg["API_KEY"] = self.api_field.text.strip()
        save_config(cfg)
        if self._dialog:
            self._dialog.dismiss()
        self.show_message("تم الحفظ", "تم حفظ إعدادات الـ API.")

    def show_message(self, title, text):
        dlg = MDDialog(title=title, text=text, buttons=[MDFlatButton(text="حسناً", on_release=lambda x: dlg.dismiss())])
        dlg.open()

    def toggle_theme(self):
        app = MDApp.get_running_app()
        app.theme_cls.theme_style = "Dark" if app.theme_cls.theme_style == "Light" else "Light"


class MyApp(MDApp):
    def build(self):
        # Use adaptive font size based on screen
        base_font = max(14, int(Window.width / 40))
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        return ChatScreen()


if __name__ == "__main__":
    MyApp().run()
