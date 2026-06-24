"""
丸久小山園 抹茶補貨監控 - GitHub Actions 版本
每次由 GitHub 定時觸發，執行一次後結束
"""

import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import time

# ── 從 GitHub Secrets 讀取（不用改這裡）──
GMAIL_USER     = os.environ["GMAIL_USER"]
GMAIL_APP_PASS = os.environ["GMAIL_APP_PASS"]
NOTIFY_EMAILS  = os.environ["NOTIFY_EMAILS"].split(",")   # 逗號分隔多個信箱

# ── 監控商品清單 ──
PRODUCTS = [
    {"name": "Yugen（幽玄）¥2,000〜",           "url": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1171020c1"},
    {"name": "Aoarashi（青嵐）¥2,120〜",        "url": "https://www.marukyu-koyamaen.co.jp/english/shop/products/11a1040c1"},
    {"name": "Isuzu（五十鈴）¥2,520〜",         "url": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1191040c1"},
    {"name": "Wako（和光）¥2,400〜",            "url": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1161020c1"},
    {"name": "Chigi no Shiro（千木白）¥2,920〜", "url": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1181040c1"},
    {"name": "Kinrin（金輪）¥3,000〜",          "url": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1151020c1"},
    {"name": "Unkaku（雲鶴）¥3,700〜",          "url": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1141020c1"},
    {"name": "Eiju（英壽）¥4,700〜",            "url": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1131020c1"},
    {"name": "Choan（長安）¥7,150〜",           "url": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1121020c1"},
    {"name": "Kiwami Choan（極長安）¥12,600〜",  "url": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1g36020c1"},
    {"name": "Tenju（天壽）¥20,100〜",          "url": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1111020c1"},
]

OUT_OF_STOCK_TEXT = "This product is currently out of stock and unavailable."

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def check_stock(product):
    try:
        r = requests.get(product["url"], headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        return OUT_OF_STOCK_TEXT not in soup.get_text()
    except Exception as e:
        print(f"  ⚠ 無法取得 {product['name']}：{e}")
        return False


def send_email(available_products):
    subject = f"🍵 丸久小山園抹茶補貨通知！{len(available_products)} 款有貨，快去買！"

    body_lines = ["以下商品現在可以購買了，請盡快下單！\n"]
    for p in available_products:
        body_lines.append(f"  ✅ {p['name']}")
        body_lines.append(f"     {p['url']}\n")
    body_lines.append("\n立即前往購物頁面：")
    body_lines.append("https://www.marukyu-koyamaen.co.jp/english/shop/products/catalog/matcha/principal")
    body_lines.append("\n（本通知由自動監控系統發送，每 30 分鐘檢查一次）")

    msg = MIMEMultipart()
    msg["From"]    = GMAIL_USER
    msg["To"]      = ", ".join(NOTIFY_EMAILS)
    msg["Subject"] = subject
    msg.attach(MIMEText("\n".join(body_lines), "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASS)
        server.sendmail(GMAIL_USER, NOTIFY_EMAILS, msg.as_string())
    print(f"  ✉ 通知已寄出至：{', '.join(NOTIFY_EMAILS)}")


def main():
    print("=== 丸久小山園抹茶補貨檢查開始 ===")
    available = []

    for p in PRODUCTS:
        in_stock = check_stock(p)
        status = "✅ 有貨" if in_stock else "❌ 缺貨"
        print(f"  {status}  {p['name']}")
        if in_stock:
            available.append(p)
        time.sleep(2)

    print(f"\n結果：{len(available)} 款有貨 / {len(PRODUCTS)} 款")

    if available:
        print("🎉 發現有貨商品，寄送通知中...")
        send_email(available)
    else:
        print("→ 全部缺貨，本次不發通知")

    print("=== 檢查完成 ===")


if __name__ == "__main__":
    main()
