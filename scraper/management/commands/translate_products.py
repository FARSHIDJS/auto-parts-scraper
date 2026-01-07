import time
from django.core.management.base import BaseCommand
from deep_translator import GoogleTranslator
# نام اپلیکیشن خودت را جایگزین 'shop' کن
from scraper.models import Product


def fix_watch_terminology(specs_dict):
    """
    این تابع دیکشنری ترجمه شده توسط گوگل را می گیرد و کلمات نامناسب
    (مثل دستگاه خودپرداز، طناب و...) را با کلمات تخصصی ساعت جایگزین می کند.
    """
    corrections = {
        # --- اصلاحات کلیدی (Keys) ---
        "طناب": "بند",
        "سیم": "بند",
        "طول سیم": "طول بند",
        "رنگ طناب": "رنگ بند",
        "ویژگی طناب": "جنس بند",
        "مورد": "بدنه",
        "شکل موردی": "فرم بدنه",
        "رنگ مورد": "رنگ بدنه",
        "مواد مورد": "جنس بدنه",
        "قطر کیس": "قطر بدنه",
        "شماره گیری": "صفحه",
        "شماره گیری رنگ": "رنگ صفحه",
        "شماره گیری نور": "نور پس‌زمینه",
        "نوع شماره گیری": "نوع نمایش",
        "سنگ شماره گیری": "نگین داخل صفحه",
        "سنگ طاق": "نگین دور قاب",
        "ویژگی شیشه ای": "جنس شیشه",
        "ضد آب": "مقاومت در برابر آب",
        "نام تجاری": "برند",

        # --- اصلاحات مقادیر (Values) ---
        "دستگاه خودپرداز": "ATM",
        "فولاد": "استیل ضدزنگ",
        "مواد معدنی": "مینرال",
        "هیچ کدام": "ندارد",
        "بله": "دارد",
        "خیر": "ندارد",
        "کوارتز": "کوارتز (باتری)",
    }

    cleaned_specs = {}

    for key, value in specs_dict.items():
        # 1. اصلاح کلید (Key)
        new_key = key
        for bad_word, good_word in corrections.items():
            if bad_word in new_key:
                new_key = new_key.replace(bad_word, good_word)

        # 2. اصلاح مقدار (Value)
        new_value = str(value)

        # فیکس کردن اختصاصی ATM
        if "دستگاه خودپرداز" in new_value:
            new_value = new_value.replace("دستگاه خودپرداز", "ATM")

        for bad_word, good_word in corrections.items():
            # تطبیق دقیق برای کلمات کوتاه، تطبیق بخشی برای کلمات بلند
            if bad_word == new_value:
                new_value = good_word
            elif len(bad_word) > 3 and bad_word in new_value:
                new_value = new_value.replace(bad_word, good_word)

        cleaned_specs[new_key] = new_value

    return cleaned_specs


class Command(BaseCommand):
    help = 'Translate products marked with needtotranslate=True and Fix SEO terms'

    def handle(self, *args, **kwargs):
        # --- فیلتر کردن هوشمند ---
        products = Product.objects.filter(
            needtotranslate=True,
            specifications__isnull=False
        ).exclude(
            specifications__exact={}
        ).filter(
            specifications_translate__isnull=False
        )

        total = products.count()

        if total == 0:
            self.stdout.write(self.style.WARNING(
                'No products found needing translation (Checked needtotranslate=True & un-translated).'))
            return

        self.stdout.write(self.style.SUCCESS(f'Found {total} marked products to translate...'))

        # تنظیم مترجم (ترکی به فارسی)
        translator = GoogleTranslator(source='tr', target='fa')

        for i, product in enumerate(products):
            try:
                original_specs = product.specifications

                # بررسی اعتبارسنجی ساده
                if not isinstance(original_specs, dict) or not original_specs:
                    self.stdout.write(self.style.WARNING(f"Skipping Product ID {product.id}: Invalid JSON format."))
                    continue

                # --- شروع فرآیند ترجمه ---
                keys = list(original_specs.keys())
                values = list(original_specs.values())
                split_index = len(keys)

                # ترکیب لیست برای یک درخواست واحد (صرفه جویی در زمان)
                combined_list = keys + values
                combined_list_str = [str(item) if item is not None else "" for item in combined_list]

                # ارسال به گوگل
                translated_combined = translator.translate_batch(combined_list_str)

                # جدا کردن کلیدها و مقادیر
                translated_keys = translated_combined[:split_index]
                translated_values = translated_combined[split_index:]

                # ساخت دیکشنری فارسی اولیه (حاوی غلط های گوگل)
                raw_translated_specs = dict(zip(translated_keys, translated_values))

                # --- اصلاح واژگان (SEO Cleaning) ---
                # اینجا تابع ما وارد عمل می‌شود و کلمات را درست می‌کند
                final_specs = fix_watch_terminology(raw_translated_specs)

                # --- ذخیره در دیتابیس ---
                product.specifications_translate = final_specs
                product.save()

                self.stdout.write(f"[{i + 1}/{total}] ✅ Translated & Fixed: {product.title}")

                # وقفه امنیتی
                time.sleep(1.5)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error converting ID {product.id}: {e}"))
                time.sleep(5)
                continue

        self.stdout.write(self.style.SUCCESS('All marked translations finished!'))