import time
import os
from django.core.management.base import BaseCommand
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from scraper.models import Product


class Command(BaseCommand):
    help = 'Generate Standard Persian Titles using AI (Smart & Flexible)'

    def handle(self, *args, **kwargs):
        # =========================================================
        # تنظیمات اتصال (پروکسی و کلید)
        GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

        if not GOOGLE_API_KEY:
            self.stdout.write(self.style.ERROR('FATAL ERROR: GOOGLE_API_KEY is missing in environment variables!'))
            return
        # =========================================================

        genai.configure(api_key=GOOGLE_API_KEY)
        # مدل Flash برای کارهای کوتاه مثل "تایتل" عالی و سریع است
        model = genai.GenerativeModel('models/gemini-2.5-flash')

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        # محصولاتی که نیاز به ترجمه دارند
        # (می‌توانید شرط title_translate__isnull=True را اضافه کنید که فقط جدیدها را بزند)
        products = Product.objects.filter(needtotranslate=True,is_title_fixed=False)

        total = products.count()
        self.stdout.write(self.style.SUCCESS(f'Found {total} products. Fixing Titles with AI...'))

        for i, product in enumerate(products):
            try:
                original_title = product.title
                brand = product.brand if product.brand else ""

                # پرامپت هوشمند برای استانداردسازی عنوان
                prompt = f"""
                تو یک متخصص سئو فروشگاه اینترنتی هستی.

                وظیفه: تبدیل عنوان محصول از ترکی/انگلیسی به یک "عنوان استاندارد فارسی".

                عنوان اصلی: "{original_title}"
                برند: "{brand}"

                قوانین تبدیل:
                1. ساختار استاندارد باید اینگونه باشد: "نوع محصول + جنسیت + برند + مدل + کد مدل".
                2. مثال: اگر ورودی "Gc GCZ02007L9MF Kadın Kol Saati" است، خروجی باید "ساعت مچی زنانه Gc مدل GCZ02007L9MF" باشد.
                3. کلمات ترکی را ترجمه کن (Kadın -> زنانه، Erkek -> مردانه، Unisex -> اسپرت).
                4. کد مدل (که انگلیسی است) را تغییر نده.
                5. هیچ علامت اضافی مثل گیومه "" یا نقطه نگذار. فقط متن خالص.

                خروجی نهایی (فقط عنوان فارسی):
                """

                response = model.generate_content(prompt, safety_settings=safety_settings)
                generated_text = response.text

                if generated_text:
                    new_title = generated_text.strip().replace('"', '').replace('\n', '')

                    # ذخیره در فیلد ترجمه (پیشنهادی)
                    if hasattr(product, 'title_translate'):
                        product.title_translate = new_title
                    else:
                        # اگر فیلد ترجمه ندارید و میخواهید روی اصلی ذخیره کنید (با احتیاط)
                        # product.title = new_title
                        print("Warning: title_translate field not found. Printing only.")
                    product.is_title_fixed=True
                    product.save()

                    self.stdout.write(f"[{i + 1}/{total}]")
                    self.stdout.write(f"   Old: {original_title}")
                    self.stdout.write(self.style.SUCCESS(f"   New: {new_title}"))
                    self.stdout.write("-" * 30)

                # وقفه کوتاه چون مدل فلش خیلی سریع است
                time.sleep(1.5)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
                time.sleep(3)
                continue