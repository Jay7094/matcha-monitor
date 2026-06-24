"""
丸久小山園 抹茶 補貨通知腳本
Marukyu Koyamaen Matcha Stock Checker

使用方式:
  pip install requests beautifulsoup4
  python matcha_stock_checker.py

設定 Gmail 發送通知:
  需先開啟 Google 帳號的「應用程式密碼」功能
  https://myaccount.google.com/apppasswords
"""

import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import logging
from datetime import datetime

# ─────────────────────────────────────────
#   ★ 請填寫你的設定
# ─────────────────────────────────────────

# Gmail 寄件設定（需要開啟「應用程式密碼」）
GMAIL_USER     = "jay7094@gmail.com"
GMAIL_APP_PASS = "lnzs yywl qoys fqah"

# ★ 多個收件人，用逗號分開
NOTIFY_EMAILS = [
    "jay7094@gmail.com",
    "miki12201989@gmail.com",
    "puppetj7@gmail.com",
]

# 檢查頻率（秒）- 預設 30 分鐘
CHECK_INTERVAL = 30 * 60

# 要監控的商品（可以刪掉你不感興趣的）
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

# ─────────────────────────────────────────
#   核心邏輯（不需要修改）
# ─────────────────────────────────────────

OUT_OF_STOCK_TEXT = "This product is currently out of stock and unavailable."

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("matcha_checker.log", encoding="utf-8"),
    ]
)
log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# 記錄上次各商品的狀態，避免重複通知
last_status = {}   # True = 有貨, False = 缺貨


def check_stock(product):
    """回傳 True 表示有貨，False 表示缺貨"""
    try:
        r = requests.get(product["url"], headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        page_text = soup.get_text()
        in_stock = OUT_OF_STOCK_TEXT not in page_text
        return in_stock
    except Exception as e:
        log.warning(f"  ⚠ 無法取得 {product['name']} 頁面：{e}")
        return False


def send_email(available_products):
    """發送補貨通知 Email 給多位收件人"""
    subject = f"🍵 丸久小山園抹茶補貨通知！({len(available_products)} 款有貨)"

    body_lines = ["以下商品現在可以購買了：\n"]
    for p in available_products:
        body_lines.append(f"  ✅ {p['name']}")
        body_lines.append(f"     {p['url']}\n")

    body_lines.append("\n立即前往購物：")
    body_lines.append("https://www.marukyu-koyamaen.co.jp/english/shop/products/catalog/matcha/principal")
    body_lines.append("\n（本通知由自動監控腳本發送）")

    body = "\n".join(body_lines)

    msg = MIMEMultipart()
    msg["From"]    = GMAIL_USER
    msg["To"]      = ", ".join(NOTIFY_EMAILS)   # 顯示所有收件人
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASS)
            server.sendmail(GMAIL_USER, NOTIFY_EMAILS, msg.as_string())  # ← 傳入 list 寄給所有人
        log.info(f"  ✉ 通知 Email 已送出至：{', '.join(NOTIFY_EMAILS)}")
    except Exception as e:
        log.error(f"  ✗ Email 發送失敗：{e}")


def run_check():
    log.info(f"=== 開始檢查 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    newly_available = []

    for p in PRODUCTS:
        in_stock = check_stock(p)
        was_in_stock = last_status.get(p["url"])

        status_str = "✅ 有貨" if in_stock else "❌ 缺貨"
        log.info(f"  {status_str}  {p['name']}")

        # 只在「從缺貨變成有貨」時通知
        if in_stock and was_in_stock is False:
            newly_available.append(p)

        last_status[p["url"]] = in_stock
        time.sleep(2)

    if newly_available:
        log.info(f"🎉 {len(newly_available)} 款商品補貨！準備發送通知...")
        send_email(newly_available)
    else:
        log.info("  → 無新補貨，繼續監控中...\n")


def main():
    log.info("丸久小山園抹茶補貨監控已啟動")
    log.info(f"監控 {len(PRODUCTS)} 款商品，每 {CHECK_INTERVAL // 60} 分鐘檢查一次")
    log.info(f"通知對象：{', '.join(NOTIFY_EMAILS)}\n")

    while True:
        run_check()
        log.info(f"下次檢查時間：{datetime.fromtimestamp(time.time() + CHECK_INTERVAL).strftime('%H:%M:%S')}\n")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
