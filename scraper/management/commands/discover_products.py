import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from scraper.models import Product, ScrapingLog, MonitoredPage, Supplier
from scraper.scraper_logic import init_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import urljoin, urlparse, urlunparse

COOKIE_BUTTON_SELECTOR = "button#ucookie-allow-all-button"


class Command(BaseCommand):
    help = '[کاشف] صفحات دسته‌بندی را می‌خزد، تا انتها اسکرول می‌کند و محصولات جدید را اضافه می‌کند'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- [ربات کاشف] شروع عملیات کشف محصول ---'))

        driver = init_driver()
        if not driver:
            self.stdout.write(self.style.ERROR('!! مرورگر سلنیوم راه‌اندازی نشد. عملیات لغو شد.'))
            ScrapingLog.objects.create(status='FAILED', message='مرورگر سلنیوم راه‌اندازی نشد.')  # لاگ خطا
            return

        categories = MonitoredPage.objects.filter(is_active=True)
        self.stdout.write(f'{categories.count()} صفحه دسته‌بندی فعال پیدا شد.')

        # --- متغیرهای گزارش نهایی ---
        total_products_created_all_runs = 0
        total_errors_all_runs = 0
        # -----------------------------

        for cat in categories:
            supplier = cat.supplier
            self.stdout.write(f'\n>> درحال بررسی: {cat.name} ({supplier.name})')

            if not supplier.product_link_selector:
                self.stdout.write(self.style.WARNING(
                    f'!! سلکتور لینک محصول (product_link_selector) برای {supplier.name} تعریف نشده. رد می‌شویم...'))
                continue

            current_url = cat.page_url
            page_count = 1
            new_products_found_in_this_cat = 0  # <-- تغییر نام متغیر

            while current_url:
                self.stdout.write(f'  ... درحال اسکن صفحه {page_count}: {current_url}')
                try:
                    driver.get(current_url)

                    # --- بستن پاپ‌آپ کوکی (مثل قبل) ---
                    try:
                        cookie_button = WebDriverWait(driver, 20).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, COOKIE_BUTTON_SELECTOR))
                        )
                        cookie_button.click();
                        time.sleep(2)
                        self.stdout.write(self.style.SUCCESS('  + بنر کوکی با موفقیت بسته شد.'))
                    except TimeoutException:
                        self.stdout.write(self.style.WARNING('  ! بنر کوکی پیدا نشد (احتمالا قبلا بسته شده).'))
                    except Exception as e_cookie:
                        pass

                    # --- اسکرول هوشمند (مثل قبل) ---
                    self.stdout.write(self.style.WARNING('  ... در حال اسکرول کردن صفحه ...'))
                    last_height = driver.execute_script("return document.body.scrollHeight")
                    patience_counter = 0;
                    MAX_PATIENCE = 2
                    while True:
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        self.stdout.write(self.style.WARNING('      ... 5 ثانیه صبر ...'))
                        time.sleep(5)
                        new_height = driver.execute_script("return document.body.scrollHeight")
                        if new_height == last_height:
                            patience_counter += 1
                            if patience_counter >= MAX_PATIENCE:
                                self.stdout.write(self.style.SUCCESS('  + به انتهای صفحه رسیدیم.'))
                                break
                        else:
                            patience_counter = 0
                            last_height = new_height

                    # --- صبر دستی ۳۰ ثانیه‌ای (مثل قبل) ---
                    self.stdout.write(self.style.WARNING('  ... 30 ثانیه صبر نهایی (دستی) ...'))
                    time.sleep(30)
                    # ---------------------------------------------

                    product_link_tags = driver.find_elements(By.CSS_SELECTOR, supplier.product_link_selector)

                    if not product_link_tags:
                        self.stdout.write(self.style.WARNING('  ! لینکی پیدا نشد.'))
                        current_url = None
                        continue

                    # --- ذخیره‌سازی با تمیز کردن URL و لاگ کردن ---
                    page_new_links = 0
                    with transaction.atomic():
                        for link_tag in product_link_tags:
                            href = link_tag.get_attribute('href')
                            if href:
                                parsed_url = urlparse(urljoin(supplier.website_url, href))
                                product_url = urlunparse(
                                    (parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))

                                product, created = Product.objects.update_or_create(
                                    supplier=supplier,
                                    source_url=product_url,
                                    defaults={'title': '--- در انتظار اسکرپ ---'}
                                )

                                if created:
                                    page_new_links += 1
                                    # --- لاگ کردن محصول جدید در دیتابیس ---
                                    ScrapingLog.objects.create(
                                        status='INFO',
                                        message=f'محصول جدید یافت شد: {product_url}',
                                        monitored_page=cat
                                    )
                                    # -------------------------------------

                    new_products_found_in_this_cat += page_new_links  # به مجموع این دسته‌بندی اضافه کن
                    self.stdout.write(
                        f'  + {page_new_links} محصول جدید در این صفحه اضافه شد. (مجموع این دسته‌بندی: {new_products_found_in_this_cat})')

                    # --- پیدا کردن صفحه بعد (مثل قبل) ---
                    if supplier.next_page_selector:
                        try:
                            next_page_element = driver.find_element(By.CSS_SELECTOR, supplier.next_page_selector)
                            current_url = next_page_element.get_attribute('href')
                            page_count += 1
                        except NoSuchElementException:
                            current_url = None
                    else:
                        current_url = None

                    time.sleep(3)

                except TimeoutException:
                    self.stdout.write(self.style.WARNING(f'  ! خطای Timeout در پردازش صفحه {page_count}.'))
                    ScrapingLog.objects.create(status='FAILED', message=f'Timeout در صفحه {page_count}: {current_url}',
                                               monitored_page=cat)
                    total_errors_all_runs += 1
                    current_url = None
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'!! خطا در دسترسی به {current_url}: {e}'))
                    ScrapingLog.objects.create(status='FAILED', message=f'خطا در اسکن دسته‌بندی {cat.name}: {e}',
                                               monitored_page=cat)
                    total_errors_all_runs += 1
                    current_url = None

            cat.last_checked = timezone.now()
            cat.save()
            total_products_created_all_runs += new_products_found_in_this_cat  # اضافه کردن به مجموع کل

        # --- گزارش نهایی ---
        final_message = f'عملیات تمام شد. {total_products_created_all_runs} محصول جدید پیدا شد. {total_errors_all_runs} خطا رخ داد.'
        self.stdout.write(self.style.SUCCESS(f'\n--- [ربات کاشف] {final_message} ---'))
        # ثبت گزارش نهایی در دیتابیس
        ScrapingLog.objects.create(
            status='INFO' if total_errors_all_runs == 0 else 'FAILED',
            message=final_message
        )
        # --------------------

        driver.quit()
        self.stdout.write(self.style.SUCCESS('--- مرورگر بسته شد. ---'))
