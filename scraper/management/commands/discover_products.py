import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from scraper.models import Product, ScrapingLog, MonitoredPage, Supplier
from urllib.parse import urljoin, urlparse, urlunparse

# --- کتابخانه قدرتمند DrissionPage ---
from DrissionPage import ChromiumPage, ChromiumOptions

class Command(BaseCommand):
    help = '[کاشف] نسخه DrissionPage برای عبور از Cloudflare'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- [ربات کاشف - DrissionPage] شروع عملیات ---'))

        # 1. تنظیمات مرورگر
        co = ChromiumOptions()
        # تنظیمات برای اجرا در داکر/لینوکس
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-gpu')
        co.set_argument('--lang=en-US')
        
        # --- نکته طلایی ---
        # ما Headless را خاموش می‌کنیم چون در فایل YML مانیتور مجازی (xvfb) داریم.
        # این کار باعث می‌شود Cloudflare نتواند تشخیص دهد ما ربات هستیم.
        co.headless(False)

        page = None
        try:
            # اتصال به مرورگر
            page = ChromiumPage(co)
            self.stdout.write("مرورگر DrissionPage با موفقیت راه اندازی شد.")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"خطا در اجرای مرورگر: {e}"))
            return

        categories = MonitoredPage.objects.filter(is_active=True)
        self.stdout.write(f'{categories.count()} دسته بندی فعال پیدا شد.')

        for cat in categories:
            supplier = cat.supplier
            self.stdout.write(f'\n>> درحال بررسی: {cat.name} ({supplier.name})')
            
            # اگر سلکتور در دیتابیس نیست، پیش‌فرض را استفاده کن
            link_selector = supplier.product_link_selector if supplier.product_link_selector else 'a.product-item-link'
            
            current_url = cat.page_url
            page_count = 1
            new_products_in_cat = 0

            while current_url:
                self.stdout.write(f'  ... ورود به صفحه {page_count}: {current_url}')
                try:
                    page.get(current_url)
                    
                    # === دور زدن Cloudflare ===
                    # اگر تایتل صفحه مشکوک بود
                    if "Just a moment" in page.title or "Access Denied" in page.title:
                        self.stdout.write(self.style.WARNING("  ! گیر افتادیم (Cloudflare). 15 ثانیه صبر برای عبور خودکار..."))
                        time.sleep(15)
                        
                        # تلاش برای کلیک روی دکمه چالش (اگر وجود داشته باشد)
                        try:
                            # DrissionPage می‌تواند داخل ShadowRoot را هم ببیند
                            cf_btn = page.ele('css:#challenge-stage', timeout=2)
                            if cf_btn:
                                cf_btn.click()
                                self.stdout.write("  ! روی دکمه چالش کلیک شد.")
                        except:
                            pass
                        
                        time.sleep(5)
                    # ==========================

                    # چاپ تایتل برای اطمینان (دیباگ)
                    self.stdout.write(f"  [DEBUG] Page Title: {page.title}")

                    # بستن کوکی (اختیاری)
                    try:
                        cookie_btn = page.ele('css:button#ucookie-allow-all-button', timeout=2)
                        if cookie_btn:
                            cookie_btn.click()
                    except:
                        pass

                    # اسکرول به پایین
                    self.stdout.write('  ... اسکرول ...')
                    page.scroll.to_bottom()
                    time.sleep(3) 

                    # پیدا کردن لینک‌ها
                    # سینتکس: page.eles (جمع) همه را برمی‌گرداند
                    link_tags = page.eles(f'css:{link_selector}')
                    
                    if not link_tags:
                        self.stdout.write(self.style.WARNING(f'  ! لینکی با سلکتور {link_selector} پیدا نشد.'))
                        # اگر لینک پیدا نشد احتمالا صفحه لود نشده، میریم بعدی
                        break

                    page_new_links = 0
                    with transaction.atomic():
                        for link in link_tags:
                            href = link.attr('href') # گرفتن ویژگی href
                            if href:
                                full_url = urljoin(supplier.website_url, href)
                                # تمیزکاری URL
                                parsed = urlparse(full_url)
                                clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

                                obj, created = Product.objects.get_or_create(
                                    supplier=supplier,
                                    source_url=clean_url,
                                    defaults={'title': '--- در انتظار اسکرپ ---'}
                                )
                                if created:
                                    page_new_links += 1

                    new_products_in_cat += page_new_links
                    self.stdout.write(self.style.SUCCESS(f'  + {page_new_links} محصول جدید در این صفحه.'))

                    # رفتن به صفحه بعد
                    if supplier.next_page_selector:
                        # تلاش برای پیدا کردن دکمه صفحه بعد
                        next_btn = page.ele(f'css:{supplier.next_page_selector}', timeout=2)
                        if next_btn:
                            # گرفتن لینک صفحه بعد
                            current_url = next_btn.attr('href')
                            page_count += 1
                        else:
                            current_url = None
                    else:
                        current_url = None

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ! خطا در پردازش صفحه: {e}'))
                    current_url = None
            
            cat.last_checked = timezone.now()
            cat.save()

        # بستن مرورگر
        if page:
            page.quit()
        self.stdout.write(self.style.SUCCESS(f'--- پایان عملیات. ---'))
