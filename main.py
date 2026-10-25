import threading
import time
import requests
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from jnius import autoclass

# آدرس سرور ویندوز شما (IP کامپیوتر در شبکه محلی و پورت ربات)
PC_SERVER_URL = "http://192.168.1.100:3000/api/receive-sms"
SENDER_KEYWORD = "KavirTire"

PythonActivity = autoclass("org.kivy.android.PythonActivity")
Telephony = autoclass("android.provider.Telephony")


class SMSForwarderApp(App):

  def build(self):
    self.layout = BoxLayout(
        orientation="vertical", padding=30, spacing=20
    )
    self.status_label = Label(
        text="[ اهراز هویت کویرتایر ]\nدر حال پایش پیامک‌ها...",
        halign="center",
        font_size=18,
    )
    self.layout.add_widget(self.status_label)

    # شروع نخ (Thread) پس‌زمینه برای چک کردن پیامک‌ها
    threading.Thread(target=self.background_sms_loop, daemon=True).start()
    return self.layout

  def get_latest_sms(self):
    try:
      activity = PythonActivity.mActivity
      cursor = activity.getContentResolver().query(
          Telephony.Sms.CONTENT_URI, None, None, None, "date DESC"
      )
      if cursor and cursor.moveToFirst():
        sender = cursor.getString(cursor.getColumnIndex("address"))
        body = cursor.getString(cursor.getColumnIndex("body"))
        cursor.close()
        if SENDER_KEYWORD in sender or SENDER_KEYWORD in body:
          import re

          codes = re.findall(r"\b\d{4,6}\b", body)
          if codes:
            return codes[0], body
    except Exception as e:
      print("SMS Read Error:", e)
    return None, None

  def background_sms_loop(self):
    last_body = ""
    while True:
      code, full_body = self.get_latest_sms()
      if code and full_body != last_body:
        last_body = full_body
        Clock.schedule_once(
            lambda dt: self.update_ui(f"کد جدید یافت شد: {code}")
        )
        try:
          res = requests.post(
              PC_SERVER_URL, json={"code": code, "text": full_body}, timeout=5
          )
          if res.status_code == 200:
            Clock.schedule_once(
                lambda dt: self.update_ui(
                    f"✅ کد {code}\nبا موفقیت به ربات ارسال شد!"
                )
            )
        except Exception as e:
          Clock.schedule_once(
              lambda dt: self.update_ui(f"❌ خطا در ارسال به کامپیوتر:\n{e}")
          )
      time.sleep(3)

  def update_ui(self, text):
    self.status_label.text = text


if __name__ == "__main__":
  SMSForwarderApp().run()
