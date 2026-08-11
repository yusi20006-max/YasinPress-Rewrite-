import os
import sys

import httpx

from yasinpress.config.loaders import load_env

# 1. بارگذاری تنظیمات
config = load_env()
token = os.getenv("YASINPRESS_EITAA_API_TOKEN")
channel = os.getenv("YASINPRESS_EITAA_CHANNEL_ID")

if not token or not channel:
    print("❌ خطا: متغیرهای YASINPRESS_EITAA_API_TOKEN یا YASINPRESS_EITAA_CHANNEL_ID یافت نشدند.")
    sys.exit(1)


# 2. ساخت URL و ارسال
def test_send():
    print(f"🚀 در حال تلاش برای ارسال پیام به کانال {channel}...")
    url = f"https://eitaayar.ir/api/{token}/sendMessage"
    payload = {"chat_id": channel, "text": "✅ تست سلامت YasinPress-Rewrite: ارسال موفق بود."}

    try:
        response = httpx.post(url, json=payload, timeout=10.0)
        response.raise_for_status()
        print("✅ پیام با موفقیت ارسال شد!")
        print("پاسخ سرور:", response.json())
    except Exception as exc:  # noqa: BLE001 - manual smoke test reports transport failures
        print(f"❌ خطای ارسال: {exc}")


if __name__ == "__main__":
    test_send()
