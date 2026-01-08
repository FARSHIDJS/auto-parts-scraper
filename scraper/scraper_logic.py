import os
import re  # <--- این خط قبلا نبود و باعث ارور میشد
import time
import undetected_chromedriver as uc

def init_driver():
    """
    مرورگر را راه اندازی می کند.
    تنظیمات خاص برای عبور از Cloudflare و اجرا روی سرور گیت‌هاب.
    """
    print("--- Initializing Undetected Chrome Driver ---")
    try:
        options = uc.ChromeOptions()
        
        # --- تنظیمات عمومی ---
        options.add_argument('--log-level=3') # فقط ارورهای مهم را نشان بده
        options.add_argument('--window-size=1920,1080') # سایز استاندارد برای جلوگیری از تشخیص ربات
        options.add_argument('--start-maximized')
        
        # --- تنظیمات مخصوص سرور (لینوکس/گیت‌هاب) ---
        # این خطوط برای اجرا روی سرور حیاتی هستند تا رم کم نیاورد و کرش نکند
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        
        # زبان مرورگر را انگلیسی میکنیم تا مشکوک نباشد
        options.add_argument('--lang=en-US')

        # بررسی اینکه آیا روی سرور گیت‌هاب هستیم یا کامپیوتر شخصی
        is_headless = False
        if os.getenv('GITHUB_ACTIONS') == 'true':
            print("Running on GitHub Actions (Headless mode)")
            is_headless = True
            # نکته: در undetected-chromedriver بهتره هدلس رو توی خود کلاس تعریف کنیم نه در آپشن‌ها

        driver = uc.Chrome(
            options=options,
            headless=is_headless, # حالت مخفی فقط روی سرور فعال میشه
            use_subprocess=True,  # این گزینه پایداری رو بیشتر میکنه
        )

        print("Browser driver initiated successfully.")
        return driver
    except Exception as e:
        print(f"ERROR starting driver: {e}")
        return None


def clean_price(price_text):
    """
    متن قیمت را به عدد تمیز (float) تبدیل می‌کند.
    """
    if not price_text: return None
    try:
        # ۱. ترجمه اعداد فارسی (اگر وجود داشته باشد)
        price_text = price_text.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789'))

        # ۲. حذف جداکننده‌های هزارگان (نقطه)
        price_text = price_text.replace('.', '')

        # ۳. تبدیل جداکننده اعشار (ویرگول) به نقطه
        price_text = price_text.replace(',', '.')

        # ۴. حذف تمام کاراکترهای غیر عددی (مثل "TL" یا "₺")
        # نیاز به import re دارد که بالا اضافه شد
        cleaned_price = re.sub(r'[^\d.]', '', price_text)

        return float(cleaned_price) if cleaned_price else None
    except Exception:
        return None


def clean_sku(sku_text):
    """متکد کالا را تمیز می‌کند و فقط دنباله عددی را برمی‌گرداند"""
    if not sku_text: return None
    try:
        # دنبال عددی با ۷ رقم یا بیشتر می‌گردد
        match = re.search(r'\b(\d{7,})\b', sku_text)
        if match:
            return match.group(1)
        else:
            numbers = re.findall(r'\d+', sku_text)
            if numbers:
                return numbers[0]
            return None
    except Exception:
        return None
