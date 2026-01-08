import os
import re
import time
import undetected_chromedriver as uc

def init_driver():
    """
    مرورگر را با حالت گرافیکی (Headful) اما در محیط مجازی اجرا می‌کند.
    """
    print("--- Initializing Chrome Driver (Headful Mode with Virtual Display) ---")
    try:
        options = uc.ChromeOptions()
        
        # --- تنظیمات حیاتی ---
        options.add_argument('--no-sandbox')  # برای اجرا در محیط کانتینر لینوکس الزامی است
        options.add_argument('--disable-dev-shm-usage') # جلوگیری از کرش مموری
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        options.add_argument('--lang=en-US')
        
        # نکته کلیدی: اینجا دیگر Headless را فعال نمی‌کنیم!
        # ما در فایل YML با استفاده از xvfb یک مانیتور الکی می‌سازیم.
        
        driver = uc.Chrome(
            options=options,
            headless=False, # <--- مهم: باید False باشد تا Cloudflare گول بخورد
            use_subprocess=True,
        )

        print("Browser driver initiated successfully.")
        return driver
    except Exception as e:
        print(f"ERROR starting driver: {e}")
        return None

# --- توابع تمیزکننده (بدون تغییر) ---
def clean_price(price_text):
    if not price_text: return None
    try:
        price_text = price_text.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789'))
        price_text = price_text.replace('.', '').replace(',', '.')
        cleaned_price = re.sub(r'[^\d.]', '', price_text)
        return float(cleaned_price) if cleaned_price else None
    except Exception:
        return None

def clean_sku(sku_text):
    if not sku_text: return None
    try:
        match = re.search(r'\b(\d{7,})\b', sku_text)
        if match: return match.group(1)
        numbers = re.findall(r'\d+', sku_text)
        return numbers[0] if numbers else None
    except Exception:
        return None
