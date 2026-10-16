import os
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import requests

# ==========================================
# НАСТРОЙКИ НА ТЕЛЕГРАМ БОТА:
TELEGRAM_TOKEN = os.getenv("8624759346:AAHTRUvUeFXvsxUyMoo_GFDBzmI3nLWelYs")
CHAT_ID = os.getenv("8995251916")
SENT_FILE = "sent_links_new.txt"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def load_sent_links():
  if os.path.exists(SENT_FILE):
    with open(SENT_FILE, "r", encoding="utf-8") as f:
      return set(line.strip() for line in f)
  return set()


def save_sent_link(link):
  with open(SENT_FILE, "a", encoding="utf-8") as f:
    f.write(link + "\n")


def send_telegram(title, link, source):
  """Изпраща нотификация в Telegram"""
  msg = (
      f"🚀 <b>Нова възможност / Грант!</b>\n\n"
      f"📌 <b>Източник:</b> {source}\n"
      f"📝 <b>Заглавие:</b> {title}\n\n"
      f"🔗 <a href='{link}'>Прочети повече тук</a>"
  )
  url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {
      "chat_id": CHAT_ID,
      "text": msg,
      "parse_mode": "HTML",
      "disable_web_page_preview": False,
  }
  try:
    requests.post(url, json=payload, timeout=10)
  except Exception as e:
    print(f"Грешка при изпращане: {e}")


# ==========================================
# 1. RSS ФИЙДОВЕ
# ==========================================
RSS_SOURCES = [
    ("EUFunds.bg", "https://eufunds.bg/bg/node/feed"),
    ("Opportunity Desk", "https://opportunitydesk.org/feed/"),
    ("EU-Startups", "https://www.eu-startups.com/feed/"),
    ("Funds for NGOs", "https://www.fundsforngos.org/feed/"),
    ("Startup Grind", "https://medium.com/feed/startup-grind"),
    ("Scholarship Positions", "https://scholarship-positions.com/feed/"),
    ("Dealroom News", "https://dealroom.co/feed"),
    ("SBIR.gov Announcements", "https://www.sbir.gov/rss/solicitations.xml"),
    (
        "Marie Skłodowska-Curie Actions",
        "https://marie-sklodowska-curie-actions.ec.europa.eu/rss.xml",
    ),
    ("ERC News", "https://erc.europa.eu/news-events/news/rss.xml"),
]


def check_rss_feeds():
  sent = load_sent_links()
  for source_name, url in RSS_SOURCES:
    try:
      res = requests.get(url, headers=HEADERS, timeout=15)
      if res.status_code == 200:
        root = ET.fromstring(res.content)
        for item in root.findall("./channel/item"):
          title = (
              item.find("title").text if item.find("title") is not None else ""
          )
          link = item.find("link").text if item.find("link") is not None else ""
          if link and link not in sent:
            send_telegram(title, link, source_name)
            save_sent_link(link)
            print(f"[{source_name}] Изпратено: {title}")
    except Exception as e:
      print(f"Грешка при RSS ({source_name}): {e}")


# ==========================================
# 2. STARTUP NETWORKS (Включен скрапер за линкове и Blue Ridge Labs)
# ==========================================
def check_startup_networks():
  """Проверка на Startup Networks за нови публикувани възможности"""
  url = "https://www.startupnetworks.co.uk/links/"
  sent = load_sent_links()
  try:
    res = requests.get(url, headers=HEADERS, timeout=15)
    if res.status_code == 200:
      soup = BeautifulSoup(res.text, "html.parser")
      for a in soup.find_all("a", href=True):
        if "/links/link/" in a["href"]:
          title = a.text.strip()
          link = (
              a["href"]
              if a["href"].startswith("http")
              else "https://www.startupnetworks.co.uk" + a["href"]
          )

          # Премахваме излишните суфикси от линка (напр. #google_vignette)
          clean_link = link.split("#")[0]

          if len(title) > 10 and clean_link not in sent:
            send_telegram(title, clean_link, "Startup Networks UK")
            save_sent_link(clean_link)
            print(f"[Startup Networks] Изпратено: {title}")
  except Exception as e:
    print(f"Грешка при Startup Networks: {e}")


# ==========================================
# 3. БЪЛГАРСКИ И ЕВРОПЕЙСКИ ОФИЦИАЛНИ ИЗТОЧНИЦИ
# ==========================================
def check_isun():
  url = "https://eumis2020.government.bg/bg/s/Procedure/Active"
  sent = load_sent_links()
  try:
    res = requests.get(url, headers=HEADERS, timeout=15)
    if res.status_code == 200:
      soup = BeautifulSoup(res.text, "html.parser")
      for a in soup.find_all("a", href=True):
        if "/Procedure/Info/" in a["href"]:
          title = a.text.strip()
          link = "https://eumis2020.government.bg" + a["href"]
          if title and link not in sent:
            send_telegram(title, link, "ИСУН 2020 (Отворени процедури)")
            save_sent_link(link)
            print(f"[ИСУН 2020] Изпратено: {title}")
  except Exception as e:
    print(f"Грешка при ИСУН: {e}")


def check_eic():
  url = "https://eic.ec.europa.eu/news_en"
  sent = load_sent_links()
  try:
    res = requests.get(url, headers=HEADERS, timeout=15)
    if res.status_code == 200:
      soup = BeautifulSoup(res.text, "html.parser")
      for a in soup.find_all("a", href=True):
        if "/news/" in a["href"] and len(a.text.strip()) > 15:
          title = a.text.strip()
          link = (
              a["href"]
              if a["href"].startswith("http")
              else "https://eic.ec.europa.eu" + a["href"]
          )
          if link not in sent:
            send_telegram(title, link, "European Innovation Council (EIC)")
            save_sent_link(link)
            print(f"[EIC] Изпратено: {title}")
  except Exception as e:
    print(f"Грешка при EIC: {e}")


# ==========================================
# ГЛАВНО ИЗПЪЛНЕНИЕ (ВСИЧКИ ФУНКЦИИ СА ВКЛЮЧЕНИ)
# ==========================================
if __name__ == "__main__":
  print("Стартиране на проверката за всички източници...")
  check_rss_feeds()
  check_startup_networks()  # <--- ВКЛЮЧЕНО
  check_isun()
  check_eic()
  print("Проверката приключи успешно!")
