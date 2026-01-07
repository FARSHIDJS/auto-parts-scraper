import time
import os
import json
from django.core.management.base import BaseCommand
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from scraper.models import Product


def fix_watch_terminology(specs_dict):
    corrections = {
        "طناب": "بند", "سیم": "بند", "طول سیم": "طول بند", "رنگ طناب": "رنگ بند",
        "مورد": "بدنه", "شکل موردی": "فرم قاب", "رنگ مورد": "رنگ بدنه", "مواد مورد": "جنس بدنه",
        "قطر کیس": "قطر قاب", "شماره گیری": "صفحه", "شماره گیری رنگ": "رنگ صفحه",
        "سنگ طاق": "نگین دور قاب", "ضد آب": "مقاومت در برابر آب", "نام تجاری": "برند",
        "دستگاه خودپرداز": "ATM", "فولاد": "استیل", "مواد معدنی": "مینرال",
        "هیچ کدام": "ندارد", "بله": "دارد", "خیر": "ندارد", "کوارتز": "کوارتز (باتری)"
    }
    cleaned_specs = {}
    for key, value in specs_dict.items():
        new_key = key
        for bad, good in corrections.items():
            if bad in new_key: new_key = new_key.replace(bad, good)
        new_value = str(value)
        if "دستگاه خودپرداز" in new_value:
            new_value = new_value.replace("دستگاه خودپرداز", "ATM")
        for bad, good in corrections.items():
            if bad == new_value:
                new_value = good
            elif len(bad) > 3 and bad in new_value:
                new_value = new_value.replace(bad, good)
        cleaned_specs[new_key] = new_value
    return cleaned_specs


class Command(BaseCommand):
    help = 'Generate SEO Description (Using Corrected Persian Title) with Gemini 2.5 Flash'

    def handle(self, *args, **kwargs):

        GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

        if not GOOGLE_API_KEY:
            self.stdout.write(self.style.ERROR('FATAL ERROR: GOOGLE_API_KEY is missing in environment variables!'))
            return
        # =========================================================

        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('models/gemini-2.5-flash')

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        # فقط محصولاتی که نیاز به ترجمه دارند
        products = Product.objects.filter(needtotranslate=True,is_long_desc_generated=False)

        total = products.count()
        if total == 0:
            self.stdout.write(self.style.WARNING('No products found.'))
            return

        self.stdout.write(self.style.SUCCESS(f'Found {total} products. Starting Engine...'))

        for i, product in enumerate(products):
            try:
                # === تغییر مهم: انتخاب عنوان درست ===
                # اگر عنوان فارسی (اصلاح شده) وجود دارد، آن را انتخاب کن
                # در غیر این صورت از عنوان اصلی استفاده کن
                final_title = product.title_translate if product.title_translate else product.title

                self.stdout.write(f"\n[{i + 1}/{total}] Processing: {final_title}")

                # دریافت و تمیزکاری مشخصات
                raw_specs = product.specifications_translate if product.specifications_translate else product.specifications

                if raw_specs and isinstance(raw_specs, dict):
                    specs_data = fix_watch_terminology(raw_specs)
                else:
                    specs_data = {}

                specs_text = ", ".join([f"{k}: {v}" for k, v in specs_data.items()])

                # تعیین جنسیت (بهبود یافته: بررسی عنوان فارسی هم اضافه شد)
                gender = "مردانه"
                full_text_search = str(product.description) + str(product.title) + str(final_title)

                if "زن" in full_text_search or "Kadın" in full_text_search or "Lady" in full_text_search:
                    gender = "زنانه"

                gender_kw = f"ساعت مچی {gender}"

                # --- پرامپت اصلاح شده با final_title ---
                prompt = f"""
                نقش: نویسنده ارشد مجله مد و فشن دیجی‌کالا.
                محصول: {final_title}
                برند: {product.brand if product.brand else 'GC'}
                مشخصات فنی: {specs_text}
                نوع: {gender_kw}

                وظیفه: نوشتن توضیحات محصول جذاب برای صفحه فروشگاه.

                قوانین اکید:
                1. **ممنوعیت متا تگ:** به هیچ وجه "Meta Description" یا تگ‌های `<meta>` تولید نکن. فقط محتوای متنی HTML را بنویس.
                2. **واژگان:** "طناب" -> "بند"، "دستگاه خودپرداز" -> "ATM"، "شماره‌گیری" -> "صفحه".
                3. **فرمت:** از تگ‌های `<h2>` برای تیترها و `<p>` برای پاراگراف‌ها استفاده کن. لیست (`<ul>`) ممنوع است.
                4. **بومی‌سازی:** برای استایل، از لباس‌های رایج در ایران (مانتو، شومیز، کت اسپرت) مثال بزن.
                5. **عنوان:** در متن توضیحات حتماً از نام فارسی محصول ("{final_title}") استفاده کن.

                ساختار خروجی HTML:

                <h2>نقد و بررسی تخصصی {final_title}</h2>
                (پاراگراف اول: توصیف جذاب ظاهر ساعت، رنگ {specs_data.get('رنگ بدنه', '')}، جنس {specs_data.get('جنس بدنه', '')} و حس لوکس بودن آن. نام کامل محصول "{final_title}" را حتماً در جمله اول بیاور.)

                <h2>مشخصات ظاهری و کیفیت ساخت</h2>
                (پاراگراف دوم: توضیح درباره مقاومت رنگ، نوع شیشه و کیفیت ساخت برند {product.brand}.)

                <h2>پیشنهاد ست کردن و استایل</h2>
                (پاراگراف سوم: این ساعت با چه لباس‌هایی ست می‌شود؟ رسمی یا اسپرت؟)

                <h2>سوالات متداول</h2>
                <p><strong>آیا این ساعت ضد آب است؟</strong><br>
                بله، این مدل دارای مقاومت {specs_data.get('مقاومت در برابر آب', 'استاندارد')} در برابر آب است.</p>
                <p><strong>موتور این ساعت ساخت کجاست؟</strong><br>
                این ساعت از موتور {specs_data.get('مکانیسم', 'کوارتز')} بهره می‌برد که دقت بالایی دارد.</p>
                """

                # ارسال به گوگل
                response = model.generate_content(prompt, safety_settings=safety_settings)
                generated_text = response.text

                if generated_text:
                    clean_text = generated_text.replace("```html", "").replace("```", "").strip()

                    # اطمینان از اینکه خروجی با تگ P یا H2 شروع شود
                    if not clean_text.startswith("<"):
                        clean_text = f"<p>{clean_text}</p>"

                    product.description_translate = clean_text
                    product.is_long_desc_generated=True
                    product.save()
                    self.stdout.write(self.style.SUCCESS(f"   > ✅ Saved (Description + FAQ)."))
                else:
                    self.stdout.write(self.style.ERROR(f"   > ❌ Empty response."))

                time.sleep(3)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
                time.sleep(5)
                continue