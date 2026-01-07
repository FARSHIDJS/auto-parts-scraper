import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
# from datetime import timedelta # دیگر نیازی به ماژول زمان نیست

# --- NEW: ایمپورت‌های جدید برای مدیریت کوکی ---
from scraper.models import Product, ProductImage, ScrapingLog, Supplier
from scraper.scraper_logic import init_driver
from scraper.product_scraper_logic import scrape_product_page  # <-- منطق اسکرپ (بدون کوکی)

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ---------------------------------------------

# NEW: سلکتور کوکی به این فایل منتقل شد
COOKIE_BUTTON_SELECTOR = "button#ucookie-allow-all-button"


class Command(BaseCommand):
    help = '[اسکرپر] اطلاعات محصولات جدید یا بدون قیمت را استخراج می‌کند'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- [ربات اسکرپر] شروع عملیات ---'))

        driver = init_driver()
        if not driver:
            self.stdout.write(self.style.ERROR('!! مرورگر سلنیوم راه‌اندازی نشد. عملیات لغو شد.'))
            return

        # --- CHANGED: این خط اصلاح شد ---
        # تامین‌کنندگانی را پیدا کن که حداقل یک صفحه دسته‌بندی فعال دارند
        active_suppliers = Supplier.objects.filter(monitored_pages__is_active=True).distinct()
        # -----------------------------

        for supplier in active_suppliers:
            self.stdout.write(f'\n--- در حال بررسی تامین‌کننده: {supplier.name} ---')

            # --- منطق فیلتر (بدون تاریخ) ---
            products_to_scrape = Product.objects.filter(
                Q(supplier=supplier) &
                (
                        Q(title__isnull=True) |
                        Q(title='--- در انتظار اسکرپ ---') |
                        Q(supplier_price__isnull=True)
                )
            ).distinct()

            product_count = products_to_scrape.count()
            if product_count == 0:
                self.stdout.write(self.style.WARNING(f'  ! محصولی برای اسکرپ (جدید یا بدون قیمت) یافت نشد.'))
                continue  # برو سراغ تامین‌کننده بعدی

            self.stdout.write(self.style.SUCCESS(f'  {product_count} محصول برای اسکرپ/آپدیت پیدا شد.'))

            # --- مدیریت کوکی (فقط یک بار برای هر تامین‌کننده) ---
            first_product_url = products_to_scrape.first().source_url
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
            for product in products_to_scrape:
                if product.source_url == first_product_url:
                    self.stdout.write(f'\n>> درحال پردازش (صفحه از قبل باز است): {product.source_url}')
                else:
                    self.stdout.write(f'\n>> درحال پردازش: {product.source_url}')

                # فراخوانی تابع اسکرپ (که دیگر منطق کوکی ندارد)
                data, status = scrape_product_page(driver, product.source_url, product.supplier,
                                                   is_first_page=(product.source_url == first_product_url))

                if not data:
                    self.stdout.write(self.style.ERROR(f'  - ناموفق: {status}'))
                    ScrapingLog.objects.create(status='FAILED',
                                               message=f'خطا در اسکرپ محصول {product.source_url}: {status}',
                                               product=product)
                    continue

                # --- ذخیره در دیتابیس ---
                try:
                    with transaction.atomic():
                        product.title = data.get('title')
                        product.supplier_sku = data.get('sku')
                        product.brand = data.get('brand')
                        product.description = data.get('description')
                        product.supplier_price = data.get('price')
                        product.sale_price = data.get('sale_price')
                        product.is_in_stock = data.get('is_in_stock')
                        product.specifications = data.get('specs')
                        product.last_scraped_at = timezone.now()
                        product.save()

                        if data.get('images'):
                            product.images.all().delete()
                            for img_url in data.get('images'):
                                ProductImage.objects.get_or_create(product=product, image_url=img_url)

                        self.stdout.write(self.style.SUCCESS(f'  + محصول "{product.title}" با موفقیت آپدیت شد.'))
                        ScrapingLog.objects.create(status='SUCCESS',
                                                   message=f'محصول آپدیت شد: {product.title}',
                                                   product=product)

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  - خطا در ذخیره دیتابیس: {e}'))
                    ScrapingLog.objects.create(status='FAILED',
                                               message=f'خطا در ذخیره {product.source_url}: {e}',
                                               product=product)

                time.sleep(3)

        driver.quit()
        self.stdout.write(self.style.SUCCESS('--- [ربات اسکرپر] عملیات تمام شد. ---'))