import google.generativeai as genai
import os

# 1. تنظیم پروکسی (بسیار مهم)
PROXY_URL = "http://127.0.0.1:10809"  # <--- پورت خود را چک کنید
os.environ['HTTP_PROXY'] = PROXY_URL
os.environ['HTTPS_PROXY'] = PROXY_URL

# 2. تنظیم کلید
raw_key = "AIzaSyClJyogwZCIS9ooRQgGH7gNrBWo4XY5GQI"  # <--- کلید خود را اینجا بگذارید
GOOGLE_API_KEY = raw_key.strip()

genai.configure(api_key=GOOGLE_API_KEY)

print("⏳ Connecting to Google to fetch model list...")

try:
    # دریافت لیست مدل‌ها
    models = genai.list_models()

    print("\n✅ Available Models for you:")
    print("-----------------------------")
    found_any = False
    for m in models:
        # فقط مدل‌هایی که قابلیت تولید متن دارند را چاپ کن
        if 'generateContent' in m.supported_generation_methods:
            print(f"Name: {m.name}")
            print(f" - Display Name: {m.display_name}")
            print(f" - Version: {m.version}")
            print("-----------------------------")
            found_any = True

    if not found_any:
        print("❌ No models found that support 'generateContent'.")

except Exception as e:
    print(f"\n❌ Error fetching models: {e}")