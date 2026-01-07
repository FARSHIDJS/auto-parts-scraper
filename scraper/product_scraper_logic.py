import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from urllib.parse import urljoin, urlparse, urlunparse

# ایمپورت توابع کمکی از موتور اصلی
from .scraper_logic import clean_price, clean_sku

# --- CHANGED: پارامتر is_first_page اضافه شد ---
def scrape_product_page(driver, product_url, supplier, is_first_page=False):
    """
    جزئیات دقیق یک صفحه محصول را استخراج می‌کند.
    (فرض بر این است که کوکی قبلاً بسته شده)
    """
    if not driver:
        return None, "Driver not initialized"

    data = {
        'title': None, 'sku': None, 'brand': None, 'description': None,
        'price': None, 'sale_price': None, 'is_in_stock': True,
        'images': [], 'specs': {}
    }

    try:
        # --- CHANGED: اگر صفحه اول نیست، آن را باز کن ---
        if not is_first_page:
            driver.get(product_url)
            time.sleep(2)  # صبر برای اجرای JS صفحه محصول
        else:
            print("  (صفحه از قبل باز است، از driver.get صرف نظر شد)")

        # --- ۱. بستن پاپ‌آپ کوکی (حذف شد) ---
        # (منطق کوکی به فایل scrape_products.py منتقل شد)

        # --- ۲. استخراج داده‌ها (با پشتیبانی از XPath و CSS) ---

        # تابع کمکی داخلی برای تشخیص نوع سلکتور
        def find_element_smart(selector):
            if not selector: return None
            if selector.startswith("/") or selector.startswith("("):
                return driver.find_element(By.XPATH, selector)
            else:
                return driver.find_element(By.CSS_SELECTOR, selector)

        def find_elements_smart(selector):
            if not selector: return []
            if selector.startswith("/") or selector.startswith("("):
                return driver.find_elements(By.XPATH, selector)
            else:
                return driver.find_elements(By.CSS_SELECTOR, selector)

        if supplier.title_selector:
            try:
                data['title'] = find_element_smart(supplier.title_selector).text.strip()
            except (NoSuchElementException, AttributeError):
                print(f"  ! سلکتور عنوان پیدا نشد")

        if supplier.sku_selector:
            try:
                data['sku'] = clean_sku(find_element_smart(supplier.sku_selector).text)
                print('sku'+str(clean_sku(find_element_smart(supplier.sku_selector).text)))
            except (NoSuchElementException, AttributeError):
                print(f"  ! سلکتور SKU پیدا نشد")

        if supplier.brand_selector:
            try:
                data['brand'] = find_element_smart(supplier.brand_selector).text.strip()
                print(find_element_smart(supplier.brand_selector).text.strip())
            except (NoSuchElementException, AttributeError):
                print(f"  ! سلکتور مارک پیدا نشد")

        if supplier.description_selector:
            try:
                data['description'] = find_element_smart(supplier.description_selector).get_attribute('innerHTML')
            except (NoSuchElementException, AttributeError):
                print(f"  ! سلکتور توضیحات پیدا نشد")

        # --- ۳. استخراج قیمت‌ها ---
        original_price = None
        current_price = None

        if supplier.price_selector:
            try:
                original_price = clean_price(find_element_smart(supplier.price_selector).text)
                print('original:'+str(original_price))
            except (NoSuchElementException, AttributeError):
                print('pydanashod')

        if supplier.sale_price_selector:
            try:
                current_price = clean_price(find_element_smart(supplier.sale_price_selector).text)
                print('current:'+str(current_price))
            except (NoSuchElementException, AttributeError):
                if not original_price: print(f"  ! سلکتور قیمت فعلی (sale_price) پیدا نشد")

        if original_price and current_price:
            data['price'] = original_price
            data['sale_price'] = current_price
        elif current_price:
            data['price'] = current_price
            data['sale_price'] = None
        elif original_price:
            data['price'] = original_price
            data['sale_price'] = None

        # --- ۴. استخراج وضعیت موجودی ---
        if supplier.in_stock_selector:
            try:
                find_element_smart(supplier.in_stock_selector)
                data['is_in_stock'] = False  # اگر سلکتور (دکمه "تمام شد" غیرفعال) پیدا شد
            except (NoSuchElementException, AttributeError):
                data['is_in_stock'] = True  # اگر پیدا نشد، یعنی موجود است

        # --- ۵. استخراج گالری عکس‌ها ---
        if supplier.image_selector:
            try:
                image_elements = find_elements_smart(supplier.image_selector)
                for img_tag in image_elements:
                    src = img_tag.get_attribute('src')
                    if src:
                        parsed_url = urlparse(urljoin(supplier.website_url, src))
                        img_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))
                        if img_url not in data['images']:
                            data['images'].append(img_url)
            except Exception as e:
                print(f"  ! خطایی در استخراج عکس‌ها رخ داد: {e}")

        # --- ۶. استخراج مشخصات فنی (JSON) - منطق جدید ---
        if supplier.specs_selector:
            try:
                # سلکتور ما: div#product-attributes
                specs_container = find_element_smart(supplier.specs_selector)

                # پیدا کردن تمام بخش‌های مشخصات (مثل ÜRÜN BİLGİSİ, KASA YAPISI, ...)
                sections = specs_container.find_elements(By.XPATH, "./div")

                for section in sections:
                    try:
                        # پیدا کردن عنوان بخش (مثلا: KASA YAPISI)
                        section_title = section.find_element(By.CSS_SELECTOR,
                                                             "span.product-attribute-label").text.strip()

                        # پیدا کردن تمام ردیف‌های داده داخل آن بخش
                        spec_rows = section.find_elements(By.CSS_SELECTOR, "div.attributes > div")

                        for row in spec_rows:
                            row_text = row.text.strip()
                            if ":" in row_text:
                                # جدا کردن Key و Value بر اساس ":"
                                key, value = row_text.split(":", 1)
                                data['specs'][key.strip()] = value.strip()
                            elif row_text:
                                # اگر ":" وجود نداشت (مثل بعضی ردیف‌های Ürün Bilgisi)
                                data['specs'][f"{section_title}_{len(data['specs'])}"] = row_text

                    except Exception:
                        pass  # اگر ساختار یک بخش متفاوت بود، رد شو
            except Exception as e:
                print(f"  ! خطایی در استخراج مشخصات فنی رخ داد: {e}")

        return data, "Success"

    except Exception as e:
        # این بخش خطا را می‌گیرد و به عنوان 'status' برمی‌گرداند
        return None, f"خطای ناشناخته در اسکرپ صفحه محصول: {e}"