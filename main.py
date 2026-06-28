import os
import json
import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import Clock

API_KEY = "AIzaSyAqj3BM_V2Y6xoPuZtapSwhhrvXwrXDzgg"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
HISTORY_FILE = "chat_history.json"


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


class ChatApp(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.history = load_history()

        self.scroll = ScrollView(size_hint=(1, 0.85))
        self.chat_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=10, padding=10)
        self.chat_box.bind(minimum_height=self.chat_box.setter("height"))
        self.scroll.add_widget(self.chat_box)
        self.add_widget(self.scroll)

        for msg in self.history:
            self.add_bubble(msg["role"], msg["text"])

        input_row = BoxLayout(size_hint=(1, 0.15))
        self.text_input = TextInput(multiline=False, hint_text="اكتب رسالتك...")
        send_btn = Button(text="إرسال", size_hint=(0.3, 1))

        send_btn.bind(on_press=self.send_message)
        self.text_input.bind(on_text_validate=self.send_message)

        input_row.add_widget(self.text_input)
        input_row.add_widget(send_btn)
        self.add_widget(input_row)

    def add_bubble(self, role, text):
        prefix = "أنت: " if role == "user" else "Gemini: "
        lbl = Label(
            text=prefix + text,
            size_hint_y=None,
            text_size=(self.scroll.width - 20, None),
            halign="right" if role == "user" else "left",
            valign="top",
        )
        lbl.bind(texture_size=lambda inst, val: setattr(lbl, "height", val[1] + 10))
        self.chat_box.add_widget(lbl)
        Clock.schedule_once(lambda dt: self.scroll_to_bottom(), 0.1)

    def scroll_to_bottom(self):
        self.scroll.scroll_y = 0

    def send_message(self, instance):
        text = self.text_input.text.strip()
        if not text:
            return
        self.text_input.text = ""
        self.add_bubble("user", text)
        self.history.append({"role": "user", "text": text})
        save_history(self.history)
        Clock.schedule_once(lambda dt: self.call_gemini(text), 0.1)

    def call_gemini(self, text):
        try:
            payload = {
                "contents": [{"parts": [{"text": text}]}]
            }
            r = requests.post(API_URL, json=payload, timeout=30)
            data = r.json()
            reply = data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            reply = f"خطأ: {e}"

        self.add_bubble("model", reply)
        self.history.append({"role": "model", "text": reply})
        save_history(self.history)


class MyApp(App):
    def build(self):
        return ChatApp()


if __name__ == "__main__":
    MyApp().run()
