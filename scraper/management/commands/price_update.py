import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.db.models import Q

# ایمپورت‌های مورد نیاز
from scraper.models import Product, ProductImage, ScrapingLog, Supplier
from scraper.scraper_logic import init_driver
from scraper.product_scraper_logic import scrape_product_page  # <-- از همان منطق اسکرپ استفاده می‌کنیم

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from decimal import Decimal, InvalidOperation  # برای مقایسه دقیق قیمت

COOKIE_BUTTON_SELECTOR = "button#ucookie-allow-all-button"


class Command(BaseCommand):
    help = '[آپدیت قیمت] قیمت و موجودی تمام محصولات موجود را بررسی و آپدیت می‌کند'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- [ربات آپدیت قیمت] شروع عملیات ---'))

        driver = init_driver()
        if not driver:
            self.stdout.write(self.style.ERROR('!! مرورگر سلنیوم راه‌اندازی نشد. عملیات لغو شد.'))
            return

        active_suppliers = Supplier.objects.filter(monitored_pages__is_active=True).distinct()
        total_updates = 0
        total_checked = 0

        for supplier in active_suppliers:
            self.stdout.write(f'\n--- در حال بررسی تامین‌کننده: {supplier.name} ---')

            # --- CHANGED: این کوئری تمام محصولات را برمی‌گرداند ---
            # (محصولاتی که عنوان دارند و در انتظار اسکرپ نیستند)
            products_to_check = Product.objects.filter(
                supplier=supplier,
                title__isnull=False
            ).exclude(title='--- در انتظار اسکرپ ---')
            # ----------------------------------------------------

            product_count = products_to_check.count()
            if product_count == 0:
                self.stdout.write(self.style.WARNING(f'  ! هیچ محصولی برای بررسی قیمت یافت نشد.'))
                continue

            self.stdout.write(self.style.SUCCESS(f'  {product_count} محصول برای بررسی قیمت پیدا شد.'))

            # --- مدیریت کوکی (فقط یک بار برای هر تامین‌کننده) ---
            first_product_url = products_to_check.first().source_url
            self.stdout.write(f'  ... در حال بارگذاری صفحه اول ({first_product_url}) برای بستن کوکی...')
            try:
                driver.get(first_product_url)
                time.sleep(2)
                cookie_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, COOKIE_BUTTON_SELECTOR))
                )
                cookie_button.click()
                self.stdout.write(self.style.SUCCESS('  + بنر کوکی با موفقیت بسته شد (یک بار برای این دامنه).'))
                time.sleep(2)
            except TimeoutException:
                self.stdout.write(self.style.WARNING('  ! بنر کوکی پیدا نشد (احتمالا قبلا بسته شده).'))
            except Exception as e_cookie:
                self.stdout.write(self.style.WARNING(f'  ! خطایی در بستن بنر کوکی رخ داد: {e_cookie}'))
            # --- پایان مدیریت کوکی ---

            # --- حلقه محصولات ---
            for i, product in enumerate(products_to_check):
                is_first = (i == 0)  # چک می‌کنیم آیا این محصول اولی است که لود کردیم

                if is_first:
                    self.stdout.write(
                        f'\n>> درحال پردازش ({i + 1}/{product_count}) (صفحه از قبل باز است): {product.source_url}')
                else:
                    self.stdout.write(f'\n>> درحال پردازش ({i + 1}/{product_count}): {product.source_url}')

                total_checked += 1

                # فراخوانی تابع اسکرپ
                data, status = scrape_product_page(driver, product.source_url, product.supplier, is_first_page=is_first)

                if not data:
                    self.stdout.write(self.style.ERROR(f'  - ناموفق: {status}'))
                    ScrapingLog.objects.create(status='FAILED',
                                               message=f'[Price Update] خطا در اسکرپ: {status}',
                                               product=product)
                    continue

                # --- NEW: منطق مقایسه و آپدیت ---
                try:
                    new_price_float = data.get('price')
                    new_sale_price_float = data.get('sale_price')
                    new_stock = data.get('is_in_stock', True)  # اگر استخراج نشد، موجود فرض کن

                    # تبدیل قیمت‌های float به Decimal برای مقایسه دقیق
                    # (قیمت در دیتابیس Decimal است)
                    new_price = Decimal(str(new_price_float)) if new_price_float is not None else None
                    new_sale_price = Decimal(str(new_sale_price_float)) if new_sale_price_float is not None else None

                    # مقایسه با دیتابیس
                    price_changed = (new_price is not None) and (new_price != product.supplier_price)
                    sale_price_changed = (new_sale_price != product.sale_price)  # None != 100.0 هم True است
                    stock_changed = (new_stock != product.is_in_stock)

                    # فقط اگر تغییری وجود داشت، ذخیره کن
                    if price_changed or sale_price_changed or stock_changed:
                        log_message_parts = []
                        if price_changed:
                            log_message_parts.append(f"قیمت: {product.supplier_price} -> {new_price}")
                            product.supplier_price = new_price

                        if sale_price_changed:
                            log_message_parts.append(f"تخفیف: {product.sale_price} -> {new_sale_price}")
                            product.sale_price = new_sale_price

                        if stock_changed:
                            log_message_parts.append(f"موجودی: {product.is_in_stock} -> {new_stock}")
                            product.is_in_stock = new_stock

                        product.last_scraped_at = timezone.now()
                        product.save()

                        log_message = f"[Price Update] آپدیت شد: {', '.join(log_message_parts)}"
                        self.stdout.write(self.style.SUCCESS(f"  + {log_message}"))
                        ScrapingLog.objects.create(status='SUCCESS', message=log_message, product=product)
                        total_updates += 1

                    else:
                        # اگر تغییری نبود، فقط لاگ بزن و last_scraped_at را آپدیت کن
                        product.last_scraped_at = timezone.now()
                        product.save()
                        self.stdout.write(
                            self.style.NOTICE(f"  - قیمت/موجودی برای '{product.title}' تغییری نکرده است."))

                except InvalidOperation:
                    self.stdout.write(
                        self.style.ERROR(f'  - خطا: قیمت استخراج شده ({new_price_float}) قابل تبدیل به Decimal نیست.'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  - خطا در مقایسه یا ذخیره دیتابیس: {e}'))
                    ScrapingLog.objects.create(status='FAILED',
                                               message=f'[Price Update] خطا در ذخیره: {e}',
                                               product=product)

                time.sleep(3)  # صبر بین هر صفحه محصول

        driver.quit()
        self.stdout.write(self.style.SUCCESS(f'\n--- [ربات آپدیت قیمت] عملیات تمام شد. ---'))
        self.stdout.write(
            self.style.SUCCESS(f'--- مجموعا {total_checked} محصول چک شد و {total_updates} محصول آپدیت گردید. ---'))