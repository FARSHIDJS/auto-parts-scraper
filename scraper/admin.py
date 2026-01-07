from django.contrib import admin
from django.db.models import F, Q  # <-- جدید: برای مقایسه فیلدها اضافه شد

# مطمئن شوید که ProductImage را هم ایمپورت می‌کنید
from .models import Supplier, MonitoredPage, Product, ProductImage, ScrapingLog


# -------------------------------------------------------------------
# NEW: فیلتر سفارشی برای محصولات تخفیف‌دار
# -------------------------------------------------------------------
class SaleStatusFilter(admin.SimpleListFilter):
    """
    این فیلتر سفارشی، یک گزینه "وضعیت تخفیف" به پنل ادمین اضافه می‌کند.
    """
    title = 'وضعیت تخفیف'  # عنوانی که در پنل ادمین نمایش داده می‌شود
    parameter_name = 'on_sale'  # پارامتری که در URL استفاده می‌شود

    def lookups(self, request, model_admin):
        """
        گزینه‌های فیلتر را برمی‌گرداند.
        ('مقدار_در_url', 'متن_نمایشی')
        """
        return (
            ('yes', 'فقط تخفیف‌دارها'),
            ('no', 'تخفیف‌ندارها'),
        )

    def queryset(self, request, queryset):
        """
        Queryset را بر اساس انتخاب کاربر فیلتر می‌کند.
        """
        if self.value() == 'yes':
            # محصولاتی را برگردان که قیمت تخفیف دارند (نال نیست)
            # و قیمت تخفیف از قیمت اصلی کمتر است
            return queryset.filter(
                sale_price__isnull=False,
                sale_price__lt=F('supplier_price')
            )

        if self.value() == 'no':
            # محصولاتی را برگردان که قیمت تخفیف ندارند (نال است)
            # یا قیمت تخفیف مساوی یا بیشتر از قیمت اصلی است
            return queryset.filter(
                Q(sale_price__isnull=True) |
                Q(sale_price__gte=F('supplier_price'))
            )


# -------------------------------------------------------------------


class ProductImageInline(admin.TabularInline):
    """
    این کلاس اجازه می‌دهد که عکس‌ها را مستقیماً در صفحه محصول اضافه یا ویرایش کنیم
    """
    model = ProductImage
    extra = 1  # به صورت پیش‌فرض ۱ فیلد خالی برای آپلود عکس جدید نشان می‌دهد
    readonly_fields = ('image_url',)  # چون ربات این فیلد را پر می‌کند


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'website_url')
    search_fields = ('name',)

    fieldsets = (
        (None, {
            'fields': ('name', 'website_url')
        }),
        ('سلکتورهای ربات کاشف (صفحه دسته‌بندی)', {
            'fields': ('product_link_selector', 'next_page_selector'),
            'classes': ('collapse',)
        }),
        ('سلکتورهای ربات اسکرپر (صفحه محصول)', {
            'fields': ('title_selector', 'sku_selector', 'brand_selector',
                       'description_selector', 'price_selector',
                       'sale_price_selector', 'in_stock_selector',
                       'image_selector', 'specs_selector'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MonitoredPage)
class MonitoredPageAdmin(admin.ModelAdmin):
    list_display = ('name', 'supplier', 'page_url', 'is_active', 'last_checked')
    list_filter = ('supplier', 'is_active')
    search_fields = ('name', 'page_url')
    list_editable = ('is_active',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title_translate', 'supplier', 'supplier_sku',
                    'supplier_price', 'sale_price', 'is_in_stock'
                    ,'needtotranslate',
                    'is_title_fixed','is_long_desc_generated','is_short_desc_generated')

    # --- list_filter آپدیت شد ---
    list_filter = (
        SaleStatusFilter,  # <-- فیلتر سفارشی جدید جایگزین 'sale_price' شد
        'supplier',
        'is_in_stock',
        'last_scraped_at',
        'needtotranslate'
    )
    # ---------------------------

    search_fields = ('title', 'supplier_sku', 'source_url')
    readonly_fields = ('last_scraped_at', 'created_at')

    fieldsets = (
        ('اطلاعات اصلی (ربات کاشف)', {
            'fields': ('supplier', 'source_url')
        }),
        ('اطلاعات تکمیلی (ربات اسکرپر)', {
            'fields': (
                'title','title_translate', 'supplier_sku', 'brand',
                'supplier_price', 'sale_price', 'is_in_stock',
                'description', 'specifications',
                'last_scraped_at', 'created_at','needtotranslate','specifications_translate'
                ,'description_translate','short_description',
                'is_title_fixed', 'is_long_desc_generated', 'is_short_desc_generated'
            )
        }),
    )

    inlines = [ProductImageInline]


@admin.register(ScrapingLog)
class ScrapingLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'status', 'message_display', 'monitored_page')
    list_filter = ('status', 'timestamp', 'monitored_page')
    search_fields = ('message',)
    readonly_fields = ('timestamp', 'status', 'message', 'monitored_page')

    # CHANGED: اضافه کردن یک تابع کمکی برای خلاصه‌سازی پیام‌ها
    def message_display(self, obj):
        return (obj.message[:75] + '...') if len(obj.message) > 75 else obj.message

    message_display.short_description = "Message"

# (نیازی به ثبت جداگانه ProductImage نیست چون به صورت Inline استفاده شده)