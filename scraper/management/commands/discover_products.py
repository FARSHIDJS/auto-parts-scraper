import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from scraper.models import Product, ScrapingLog, MonitoredPage, Supplier
from urllib.parse import urljoin, urlparse, urlunparse

# --- ایمپورت سلاح جدید: DrissionPage ---
from DrissionPage import ChromiumPage, ChromiumOptions

class Command(BaseCommand):
    help = '[کاشف] نسخه DrissionPage برای عبور از Cloudflare'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- [ربات کاشف - DrissionPage] شروع عملیات ---'))

        # 1. تنظیمات مرورگر (بسیار قدرتمندتر از سلنیوم)
        co = ChromiumOptions()
        co.set_argument('--no-sandbox') 
        co.set_argument('--lang=en-US')
        # نکته: ما هدلس را خاموش می‌گذاریم چون xvfb در فایل YML داریم
        co.headless(False) 
        
        # اتصال به مرورگر
        try:
            page = ChromiumPage(co)
            self.stdout.write("مرورگر DrissionPage با موفقیت راه اندازی شد.")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"خطا در اجرای مرورگر: {e}"))
            return

        categories = MonitoredPage.objects.filter(is_active=True)
        
        for cat in categories:
            supplier = cat.supplier
            self.stdout.write(f'\n>> درحال بررسی: {cat.name}')
            
            # استفاده از سلکتور جدیدی که گفتم (اگر در دیتابیس ندارید، اینجا پیش‌فرض می‌گذاریم)
            # پیشنهاد: حتما در دیتابیس a.product-item-link را ذخیره کنید
            link_selector = supplier.product_link_selector if supplier.product_link_selector else 'a.product-item-link'
            
            current_url = cat.page_url
            page_count = 1
            new_products = 0

            while current_url:
                self.stdout.write(f'  ... ورود به صفحه: {current_url}')
                try:
                    page.get(current_url)
                    
                    # === بخش عبور از Cloudflare ===
                    if "Just a moment" in page.title or "Access Denied" in page.title:
                        self.stdout.write(self.style.WARNING("  ! مواجهه با Cloudflare. صبر برای عبور خودکار..."))
                        time.sleep(15) # DrissionPage معمولا خودش عبور می‌کند
                        
                        # تلاش برای کلیک روی چک‌باکس اگر وجود داشته باشد
                        try:
                            cf_btn = page.ele('css:#challenge-stage', timeout=2)
                            if cf_btn: cf_btn.click()
                        except:
                            pass
                        
                        time.sleep(5)
                    # ==============================

                    self.stdout.write(f"  [DEBUG] Title: {page.title}")

                    # مدیریت کوکی (ساده‌تر)
                    try:
                        cookie_btn = page.ele('css:button#ucookie-allow-all-button', timeout=3)
                        if cookie_btn:
                            cookie_btn.click()
                            self.stdout.write("  + کوکی بسته شد.")
                    except:
                        pass

                    # اسکرول هوشمند
                    self.stdout.write('  ... اسکرول ...')
                    page.scroll.to_bottom()
                    time.sleep(5) # صبر کوتاه بعد از اسکرول
                    
                    # پیدا کردن لینک‌ها
                    # سینتکس DrissionPage: استفاده از eles برای پیدا کردن همه
                    link_tags = page.eles(f'css:{link_selector}')
                    
                    if not link_tags:
                        self.stdout.write(self.style.WARNING(f'  ! لینکی با سلکتور {link_selector} پیدا نشد.'))
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

                    new_products += page_new_links
                    self.stdout.write(self.style.SUCCESS(f'  + {page_new_links} محصول جدید یافت شد.'))

                    # صفحه بعد
                    if supplier.next_page_selector:
                        next_btn = page.ele(f'css:{supplier.next_page_selector}', timeout=2)
                        if next_btn:
                            current_url = next_btn.attr('href')
                            page_count += 1
                        else:
                            current_url = None
                    else:
                        current_url = None

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ! خطا: {e}'))
                    current_url = None
            
            cat.last_checked = timezone.now()
            cat.save()

        page.quit()
        self.stdout.write(self.style.SUCCESS(f'--- پایان. مجموع جدید: {new_products} ---'))
