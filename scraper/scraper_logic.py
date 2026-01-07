# # # import re
# # # import time
# # # from selenium import webdriver
# # # from selenium.webdriver.common.by import By
# # # from selenium.webdriver.chrome.service import Service
# # # from selenium.common.exceptions import NoSuchElementException, TimeoutException
# # # from selenium.webdriver.support.ui import WebDriverWait
# # # from selenium.webdriver.support import expected_conditions as EC
# # # import undetected_chromedriver as uc
# # #
# # # # مطمئن شوید chromedriver.exe کنار manage.py است
# # # DRIVER_PATH = 'chromedriver.exe'
# # #
# # #
# # # def init_driver():
# # #     """
# # #     مرورگر را با استفاده از undetected_chromedriver راه‌اندازی می‌کند
# # #     تا شناسایی نشود.
# # #     """
# # #     try:
# # #         options = uc.ChromeOptions()
# # #         options.add_argument('--log-level=3')
# # #         # options.add_argument('--headless') # برای مخفی کردن مرورگر (فعلا برای تست لازم نیست)
# # #
# # #         driver = uc.Chrome(options=options, driver_executable_path=DRIVER_PATH)
# # #
# # #         print("Browser driver initiated (undetected mode).")
# # #         return driver
# # #     except Exception as e:
# # #         print(f"ERROR starting undetected driver: {e}")
# # #         print("Ensure chromedriver.exe is in the project root and matches your Chrome version.")
# # #         return None
# # #
# # #
# # # def clean_price(price_text):
# # #     """متن قیمت را به عدد تمیز (float) تبدیل می‌کند"""
# # #     if not price_text: return None
# # #     try:
# # #         price_text = price_text.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789'))
# # #         cleaned_price = re.sub(r'[^\d.]', '', price_text)
# # #         return float(cleaned_price) if cleaned_price else None
# # #     except Exception:
# # #         return None
# # #
# # #
# # # def clean_sku(sku_text):
# # #     """متن کد کالا را تمیز می‌کند و فقط دنباله عددی را برمی‌گرداند"""
# # #     if not sku_text: return None
# # #     try:
# # #         match = re.search(r'\b(\d{7,})\b', sku_text)  # دنبال عددی با ۷ رقم یا بیشتر بگرد
# # #         if match:
# # #             return match.group(1)
# # #         else:
# # #             numbers = re.findall(r'\d+', sku_text)
# # #             if numbers: return numbers[0]
# # #             return None
# # #     except Exception:
# # #         return None
# # #
# # # # (توابع دیگر مثل scrape_page_data را بعداً به اینجا اضافه خواهیم کرد)
# #
# #
# # import re
# # import time
# # from selenium import webdriver  # <-- از سلنیوم استاندارد استفاده می‌کنیم
# # from selenium.webdriver.common.by import By
# # from selenium.webdriver.chrome.service import Service
# # from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
# # from selenium.webdriver.support.ui import WebDriverWait
# # from selenium.webdriver.support import expected_conditions as EC
# #
# # # --- ایمپورت کتابخانه جدید ---
# # from selenium_stealth import stealth
# #
# # # -----------------------------
# #
# # DRIVER_PATH = 'chromedriver.exe'
# #
# #
# # def clean_price(price_text):
# #     # ... (کد این تابع تغییری نکرده) ...
# #     if not price_text: return None
# #     try:
# #         price_text = price_text.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789'))
# #         cleaned_price = re.sub(r'[^\d.]', '', price_text)
# #         return float(cleaned_price) if cleaned_price else None
# #     except Exception:
# #         return None
# #
# #
# # def clean_sku(sku_text):
# #     # ... (کد این تابع تغییری نکرده) ...
# #     if not sku_text: return None
# #     try:
# #         match = re.search(r'\b(\d{10})\b', sku_text)
# #         if match:
# #             return match.group(1)
# #         else:
# #             numbers = re.findall(r'\d+', sku_text)
# #             if numbers: return numbers[0]
# #             return None
# #     except Exception:
# #         return None
# #
# #
# # # --- تابع init_driver کاملاً بازنویسی شده است ---
# # def init_driver():
# #     """
# #     مرورگر را با استفاده از selenium-stealth راه‌اندازی می‌کند
# #     تا شناسایی نشود.
# #     """
# #     try:
# #         options = webdriver.ChromeOptions()
# #         options.add_argument('--log-level=3')
# #         options.add_experimental_option('excludeSwitches', ['enable-logging'])
# #
# #         # آپشن‌های استاندارد مخفی‌سازی
# #         options.add_argument("start-maximized")
# #         options.add_experimental_option("excludeSwitches", ["enable-automation"])
# #         options.add_experimental_option('useAutomationExtension', False)
# #
# #         # راه‌اندازی درایور کروم استاندارد
# #         service = Service(executable_path=DRIVER_PATH)
# #         driver = webdriver.Chrome(service=service, options=options)
# #
# #         # --- اعمال وصله‌های selenium-stealth ---
# #         stealth(driver,
# #                 languages=["en-US", "en"],
# #                 vendor="Google Inc.",
# #                 platform="Win32",
# #                 webgl_vendor="Intel Inc.",
# #                 renderer="Intel Iris OpenGL Engine",
# #                 fix_hairline=True,
# #                 )
# #         # --------------------------------------
# #
# #         print("Browser driver initiated (selenium-stealth mode).")
# #         return driver
# #     except Exception as e:
# #         print(f"ERROR starting stealth driver: {e}")
# #         return None
# #
# # # --- تابع scrape_page_data (کاشف) ---
# # # این تابع (و هر تابع دیگری که از driver استفاده می‌کند)
# # # نیازی به تغییر ندارد و سر جای خودش باقی می‌ماند.
# # # (کد تابع discover_products.py شما از این init_driver جدید استفاده خواهد کرد)
# # # ... (توابع init_driver, clean_price, clean_sku در بالای فایل هستند) ...
# #
# # def scrape_product_page(driver, product_url, supplier):
# #     """
# #     یک صفحه محصول را با سلنیوم باز می‌کند و تمام جزئیات آن را
# #     بر اساس سلکتورهای تامین‌کننده، استخراج می‌کند.
# #     """
# #     if not driver:
# #         return None, "Driver not initialized"
# #
# #     data = {
# #         'title': None, 'sku': None, 'brand': None, 'description': None,
# #         'price': None, 'sale_price': None, 'is_in_stock': True,
# #         'images': [], 'specs': {}
# #     }
# #
# #     try:
# #         driver.get(product_url)
# #         # صبر اولیه برای لود شدن کلی صفحه (می‌توانید زمانش را تنظیم کنید)
# #         WebDriverWait(driver, 20).until(
# #             EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
# #         )
# #         time.sleep(2)  # صبر اضافی برای اجرای JS
# #
# #         # --- استخراج داده‌های متنی (عنوان، SKU، مارک، توضیحات) ---
# #         if supplier.title_selector:
# #             try:
# #                 data['title'] = driver.find_element(By.CSS_SELECTOR, supplier.title_selector).text.strip()
# #             except NoSuchElementException:
# #                 print(f"  ! سلکتور عنوان پیدا نشد")
# #
# #         if supplier.sku_selector:
# #             try:
# #                 data['sku'] = clean_sku(driver.find_element(By.CSS_SELECTOR, supplier.sku_selector).text)
# #             except NoSuchElementException:
# #                 print(f"  ! سلکتور SKU پیدا نشد")
# #
# #         if supplier.brand_selector:
# #             try:
# #                 data['brand'] = driver.find_element(By.CSS_SELECTOR, supplier.brand_selector).text.strip()
# #             except NoSuchElementException:
# #                 print(f"  ! سلکتور مارک پیدا نشد")
# #
# #         if supplier.description_selector:
# #             try:
# #                 data['description'] = driver.find_element(By.CSS_SELECTOR, supplier.description_selector).get_attribute(
# #                     'innerHTML')
# #             except NoSuchElementException:
# #                 print(f"  ! سلکتور توضیحات پیدا نشد")
# #
# #         # --- استخراج قیمت‌ها (منطق هوشمند) ---
# #         original_price = None
# #         current_price = None
# #
# #         if supplier.price_selector:  # قیمت اصلی (خط خورده)
# #             try:
# #                 original_price = clean_price(driver.find_element(By.CSS_SELECTOR, supplier.price_selector).text)
# #             except NoSuchElementException:
# #                 pass  # اشکالی ندارد اگر قیمت خط خورده وجود نداشته باشد
# #
# #         if supplier.sale_price_selector:  # قیمت فعلی (چه تخفیف خورده چه عادی)
# #             try:
# #                 current_price = clean_price(driver.find_element(By.CSS_SELECTOR, supplier.sale_price_selector).text)
# #             except NoSuchElementException:
# #                 print(f"  ! سلکتور قیمت فعلی پیدا نشد")
# #
# #         if original_price and current_price:
# #             # اگر هر دو قیمت وجود دارند (یعنی تخفیف خورده)
# #             data['price'] = original_price
# #             data['sale_price'] = current_price
# #         else:
# #             # اگر فقط یک قیمت وجود دارد (تخفیف نخورده)
# #             data['price'] = current_price  # قیمت فعلی را به عنوان قیمت اصلی در نظر بگیر
# #             data['sale_price'] = None
# #
# #         # --- استخراج وضعیت موجودی ---
# #         if supplier.in_stock_selector:
# #             try:
# #                 driver.find_element(By.CSS_SELECTOR, supplier.in_stock_selector)
# #                 data['is_in_stock'] = False  # اگر سلکتور (دکمه "تمام شد") پیدا شد
# #             except NoSuchElementException:
# #                 data['is_in_stock'] = True  # اگر پیدا نشد، یعنی موجود است
# #
# #         # --- استخراج گالری عکس‌ها ---
# #         if supplier.image_selector:
# #             try:
# #                 image_elements = driver.find_elements(By.CSS_SELECTOR, supplier.image_selector)
# #                 for img_tag in image_elements:
# #                     src = img_tag.get_attribute('src')
# #                     if src:
# #                         # تمیز کردن URL عکس از پارامترهای اضافه (مثل ?ts=...&w=...)
# #                         parsed_url = urlparse(urljoin(supplier.website_url, src))
# #                         img_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))
# #                         if img_url not in data['images']:  # جلوگیری از عکس تکراری
# #                             data['images'].append(img_url)
# #             except Exception as e:
# #                 print(f"  ! خطایی در استخراج عکس‌ها رخ داد: {e}")
# #
# #         # --- استخراج مشخصات فنی (JSON) ---
# #         if supplier.specs_selector:
# #             try:
# #                 # پیدا کردن کانتینر اصلی مشخصات
# #                 specs_container = driver.find_element(By.CSS_SELECTOR, supplier.specs_selector)
# #                 # پیدا کردن تمام ردیف‌های مشخصات در کانتینر
# #                 spec_items = specs_container.find_elements(By.CSS_SELECTOR, "div.product-detail__properties-item")
# #
# #                 for item in spec_items:
# #                     try:
# #                         key = item.find_element(By.CSS_SELECTOR, "span.name").text.strip().replace(":", "")
# #                         value = item.find_element(By.CSS_SELECTOR, "span.value").text.strip()
# #                         if key and value:
# #                             data['specs'][key] = value
# #                     except Exception:
# #                         pass  # اگر ردیفی ساختار متفاوتی داشت، رد شو
# #             except Exception as e:
# #                 print(f"  ! خطایی در استخراج مشخصات فنی رخ داد: {e}")
# #
# #         return data, "Success"
# #
# #     except Exception as e:
# #         return None, f"خطای ناشناخته در اسکرپ صفحه محصول: {e}"
#
#
# import re
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# import undetected_chromedriver as uc
#
# DRIVER_PATH = 'chromedriver.exe'
#
# def init_driver():
#     """
#     مرورگر را با استفاده از undetected_chromedriver راه‌اندازی می‌کند
#     تا شناسایی نشود.
#     """
#     try:
#         options = uc.ChromeOptions()
#         options.add_argument('--log-level=3')
#         # options.add_argument('--headless') # برای مخفی کردن مرورگر
#         driver = uc.Chrome(options=options, driver_executable_path=DRIVER_PATH)
#         print("Browser driver initiated (undetected mode).")
#         return driver
#     except Exception as e:
#         print(f"ERROR starting undetected driver: {e}")
#         return None
#
# def clean_price(price_text):
#     """متن قیمت را به عدد تمیز (float) تبدیل می‌کند"""
#     if not price_text: return None
#     try:
#         price_text = price_text.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789'))
#         cleaned_price = re.sub(r'[^\d.]', '', price_text)
#         return float(cleaned_price) if cleaned_price else None
#     except Exception: return None
#
# def clean_sku(sku_text):
#     """متکد کالا را تمیز می‌کند و فقط دنباله عددی را برمی‌گرداند"""
#     if not sku_text: return None
#     try:
#         # دنبال عددی با ۷ رقم یا بیشتر می‌گردد
#         match = re.search(r'\b(\d{7,})\b', sku_text)
#         if match:
#             return match.group(1)
#         else:
#              numbers = re.findall(r'\d+', sku_text)
#              if numbers:
#                  return numbers[0]
#              return None
#     except Exception:
#         return None


# import re
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# import undetected_chromedriver as uc
#
# DRIVER_PATH = 'chromedriver.exe'
#
#
# def init_driver():
#     """
#     مرورگر را با استفاده از undetected_chromedriver راه‌اندازی می‌کند
#     تا شناسایی نشود.
#     """
#     try:
#         options = uc.ChromeOptions()
#         options.add_argument('--log-level=3')
#         # options.add_argument('--headless') # برای مخفی کردن مرورگر
#         driver = uc.Chrome(options=options, driver_executable_path=DRIVER_PATH)
#         print("Browser driver initiated (undetected mode).")
#         return driver
#     except Exception as e:
#         print(f"ERROR starting undetected driver: {e}")
#         return None

import os
import undetected_chromedriver as uc


def init_driver():
    """
    مرورگر را راه اندازی می کند.
    اگر روی گیت هاب باشد، به صورت مخفی (Headless) اجرا می شود.
    """
    try:
        options = uc.ChromeOptions()
        options.add_argument('--log-level=3')

        # فقط اگر روی سرور گیت هاب بودیم، هدلس شود (چون مانیتور ندارد)
        if os.getenv('GITHUB_ACTIONS') == 'true':
            options.add_argument('--headless')

        # تغییر مهم: مسیر فایل exe رو حذف کردیم تا خودش دانلود کنه
        # اینطوری هم روی کامپیوتر تو کار میکنه هم روی سرور
        driver = uc.Chrome(options=options)

        print("Browser driver initiated.")
        return driver
    except Exception as e:
        print(f"ERROR starting driver: {e}")
        return None




def clean_price(price_text):
    """
    متن قیمت را به عدد تمیز (float) تبدیل می‌کند.
    (فرمت‌های "16.401,00 TL" و "16401.00" را پشتیبانی می‌کند)
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