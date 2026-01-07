import time
import os
from django.core.management.base import BaseCommand
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from scraper.models import Product


class Command(BaseCommand):
    help = 'Generate PERFECT HTML Tech Specs (14+ items) with Fixed Grammar'

    def handle(self, *args, **kwargs):
        # =========================================================
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

        products = Product.objects.filter(needtotranslate=True,is_short_desc_generated=False)

        total = products.count()
        if total == 0:
            self.stdout.write(self.style.WARNING('No products found.'))
            return

        self.stdout.write(self.style.SUCCESS(f'Found {total} products. Generating Final Specs...'))

        for i, product in enumerate(products):
            try:
                final_title = product.title_translate if hasattr(product,
                                                                 'title_translate') and product.title_translate else product.title

                self.stdout.write(f"\n[{i + 1}/{total}] Processing: {final_title}")

                raw_specs = product.specifications_translate if product.specifications_translate else product.specifications
                specs_text = str(raw_specs)

                # --- پرامپت نهایی با اصلاح گرامر جنسیت ---
                prompt = f"""
                نقش: مدیر محصول وسواسی فروشگاه ساعت.
                محصول: {final_title}
                دیتا: {specs_text}

                وظیفه: ساخت لیست HTML کامل (حدود 14 مورد) از مشخصات فنی.

                قوانین اکید:
                1. **تعداد:** سعی کن حدود 12 تا 16 مورد مفید استخراج کنی.
                2. **اصلاح گرامر:** - جنسیت "زن" -> بنویس **"زنانه"**.
                   - جنسیت "مرد" -> بنویس **"مردانه"**.
                3. **اصلاح عناوین:** "ویژگی بند" -> "جنس بند"، "مواد بدنه" -> "جنس قاب"، "صفحه رنگ" -> "رنگ صفحه".
                4. **حذف:** موارد "ندارد" یا "خیر" را حذف کن.
                5. **نگارش:** اعداد فارسی (۲۸ میلی‌متر).

                فرمت خروجی (HTML):
                <ul class="tech-specs">
                  <li><strong>عنوان:</strong> مقدار</li>
                </ul>
                """

                response = model.generate_content(prompt, safety_settings=safety_settings)
                generated_text = response.text

                if generated_text:
                    clean_html = generated_text.replace("```html", "").replace("```", "").strip()

                    if hasattr(product, 'short_description'):
                        product.short_description = clean_html
                        product.is_short_desc_generated=True
                        product.save()
                        self.stdout.write(self.style.SUCCESS(f"   > ✅ Saved (Perfect Grammar)."))
                    else:
                        print(clean_html)
                else:
                    self.stdout.write(self.style.ERROR(f"   > ❌ Empty response."))

                time.sleep(1.5)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
                time.sleep(3)
                continue