from django.core.management.base import BaseCommand
from scraper.models import ProductImage


class Command(BaseCommand):
    help = 'Upgrade image resolution (126x126 -> 400x400) ONLY for products needing translation'

    def handle(self, *args, **kwargs):
        # فیلتر ترکیبی:
        # 1. لینک عکس شامل "mnresize/126/126" باشد
        # 2. محصول مربوط به این عکس (product) تیک needtotranslate داشته باشد
        low_res_images = ProductImage.objects.filter(
            image_url__contains="mnresize/126/126",
            product__needtotranslate=True
        )

        total = low_res_images.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("✅ هیچ عکس بی‌کیفیتی برای محصولات در حال ترجمه پیدا نشد."))
            return

        self.stdout.write(self.style.WARNING(f"تعداد {total} عکس برای ارتقا پیدا شد (فقط محصولات ترجمه نشده)."))

        updated_count = 0
        for img in low_res_images:
            try:
                current_url = img.image_url

                if current_url:
                    # جایگزینی سایز
                    new_url = current_url.replace("mnresize/126/126", "mnresize/500/500")

                    img.image_url = new_url
                    img.save()

                    updated_count += 1

                    if updated_count % 100 == 0:
                        self.stdout.write(f"   > {updated_count} عکس آپدیت شد...")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error on Image ID {img.id}: {e}"))
                continue

        self.stdout.write(
            self.style.SUCCESS(f"🎉 تمام شد! تعداد {updated_count} عکس مربوط به محصولات هدف، با موفقیت ارتقا یافتند."))