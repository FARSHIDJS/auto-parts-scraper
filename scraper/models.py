from django.db import models


class Supplier(models.Model):
    """
    تامین‌کننده: تمام سلکتورهای مورد نیاز ربات‌ها را نگه می‌دارد
    """
    name = models.CharField(max_length=200, verbose_name="نام تامین‌کننده")
    website_url = models.URLField(max_length=200, verbose_name="آدرس سایت", null=True, blank=True)

    # --- سلکتورهای ربات کاشف (صفحه دسته‌بندی) ---
    product_link_selector = models.CharField(
        max_length=500,
        verbose_name="سلکتور لینک محصول (در صفحه دسته‌بندی)",
        null=True, blank=True
    )
    next_page_selector = models.CharField(
        max_length=500,
        verbose_name="سلکتور صفحه بعد (Pagination)",
        null=True, blank=True
    )

    # --- سلکتورهای ربات اسکرپر (صفحه محصول) ---
    title_selector = models.CharField(
        max_length=500,
        verbose_name="سلکتور نام محصول",
        null=True, blank=True
    )
    sku_selector = models.CharField(
        max_length=500,
        verbose_name="سلکتور کد (SKU)",
        null=True, blank=True
    )
    brand_selector = models.CharField(
        max_length=500,
        verbose_name="سلکتور مارک (Brand)",
        null=True, blank=True
    )
    description_selector = models.CharField(
        max_length=500,
        verbose_name="سلکتور توضیحات (Description)",
        null=True, blank=True
    )
    price_selector = models.CharField(  # قیمت اصلی
        max_length=500,
        verbose_name="سلکتور قیمت اصلی",
        null=True, blank=True
    )
    sale_price_selector = models.CharField(  # قیمت با تخفیف
        max_length=500,
        verbose_name="سلکتور قیمت با تخفیف (Sale Price)",
        null=True, blank=True
    )
    in_stock_selector = models.CharField(  # موجودی
        max_length=500,
        verbose_name="سلکتور وضعیت موجودی (In Stock)",
        null=True, blank=True
    )
    image_selector = models.CharField(  # عکس‌ها
        max_length=500,
        verbose_name="سلکتور عکس‌های گالری (Images)",
        null=True, blank=True
    )
    specs_selector = models.CharField(  # مشخصات فنی
        max_length=500,
        verbose_name="سلکتور کانتینر مشخصات فنی (Specs)",
        null=True, blank=True
    )

    class Meta:
        verbose_name = "تامین‌کننده"
        verbose_name_plural = "تامین‌کنندگان"

    def __str__(self):
        return self.name


class MonitoredPage(models.Model):
    """
    صفحات دسته‌بندی که ربات کاشف باید آن‌ها را اسکن کند
    """
    name = models.CharField(max_length=200, verbose_name="نام صفحه دسته‌بندی")
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='monitored_pages')
    page_url = models.URLField(max_length=1000, unique=True, verbose_name="آدرس URL صفحه")
    is_active = models.BooleanField(default=True, verbose_name="آیا فعال است؟")
    last_checked = models.DateTimeField(null=True, blank=True, verbose_name="آخرین زمان بررسی")

    class Meta:
        verbose_name = "صفحه دسته‌بندی تحت نظر"
        verbose_name_plural = "صفحات دسته‌بندی تحت نظر"

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    محصول: ربات کاشف این را با URL پر می‌کند، ربات اسکرپر آن را تکمیل می‌کند
    """
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='products',
                                 verbose_name="تامین‌کننده")
    source_url = models.URLField(max_length=1000, unique=True, verbose_name="آدرس صفحه محصول")

    # --- فیلدهایی که ربات اسکرپر پر می‌کند ---
    title = models.CharField(max_length=300, verbose_name="عنوان محصول", null=True, blank=True)
    title_translate = models.CharField(max_length=300, verbose_name="عنوان فارسی محصول", null=True, blank=True)
    supplier_sku = models.CharField(max_length=100, verbose_name="SKU تامین‌کننده", null=True, blank=True)
    brand = models.CharField(max_length=100, verbose_name="مارک", null=True, blank=True)
    description = models.TextField(verbose_name="توضیحات محصول", null=True, blank=True)
    description_translate = models.TextField(verbose_name="توضیحات محصول بعد ترجمه", null=True, blank=True)
    short_description = models.TextField(verbose_name="توضیحات کوتاه (HTML)", null=True, blank=True)
    supplier_price = models.DecimalField(  # قیمت اصلی
        max_digits=15, decimal_places=2,
        verbose_name="قیمت اصلی",
        null=True, blank=True
    )
    sale_price = models.DecimalField(  # قیمت با تخفیف
        max_digits=15, decimal_places=2,
        verbose_name="قیمت بدون تخفیف",
        null=True, blank=True
    )
    is_in_stock = models.BooleanField(default=True, verbose_name="آیا موجود است؟")

    specifications = models.JSONField(  # فیلد مشخصات
        verbose_name="مشخصات فنی (JSON)",
        null=True, blank=True
    )
    specifications_translate = models.JSONField(  # فیلد مشخصات
        verbose_name="مشخصات فنی بعد از ترجمه (JSON)",
        null=True, blank=True
    )
    needtotranslate = models.BooleanField(default=False, verbose_name="آیا نیاز به ترنسلیت دارد؟")
    # ------------------
    is_title_fixed = models.BooleanField(default=False, verbose_name="آیا عنوان اصلاح شده؟")
    is_long_desc_generated = models.BooleanField(default=False, verbose_name="آیا توضیحات بلند ساخته شده؟")
    is_short_desc_generated = models.BooleanField(default=False, verbose_name="آیا توضیحات کوتاه ساخته شده؟")
    last_scraped_at = models.DateTimeField(null=True, blank=True, verbose_name="آخرین زمان اسکرپ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد رکورد")

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ['title']

    def __str__(self):
        return self.title if self.title else self.source_url


class ProductImage(models.Model):
    """
    جدول جدید برای نگهداری تمام عکس‌های گالری یک محصول
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="محصول")
    image_url = models.URLField(max_length=1000, verbose_name="آدرس URL عکس")

    class Meta:
        verbose_name = "تصویر محصول"
        verbose_name_plural = "تصاویر محصول"
        unique_together = ('product', 'image_url')

    def __str__(self):
        return f"تصویر برای {self.product.title}"


class ScrapingLog(models.Model):
    """
    گزارش (لاگ) عملیات‌های ربات‌ها برای عیب‌یابی
    """
    STATUS_CHOICES = [
        ('SUCCESS', 'موفق (آپدیت شد)'),
        ('FAILED', 'ناموفق (خطا)'),
        ('INFO', 'اطلاعات (کشف شد)'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name="وضعیت")
    message = models.TextField(verbose_name="پیام گزارش")
    monitored_page = models.ForeignKey(MonitoredPage, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="زمان ثبت")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs')

    # test comment just
    class Meta:
        verbose_name = "گزارش ربات"
        verbose_name_plural = "گزارش‌های ربات"
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] - {self.get_status_display()}"