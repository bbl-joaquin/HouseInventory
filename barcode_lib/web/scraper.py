import json
import time
from pathlib import Path
from typing import List
from urllib.parse import urlparse
import random

import requests
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import Chrome

CONFIG_PATH = Path(__file__).parent / "webconfig.json"
CACHE_PATH = Path(__file__).parent / "product_cache.json"

# Crear cache si no existe
if not CACHE_PATH.exists():
    CACHE_PATH.write_text(json.dumps({}))

def get_priority_sites() -> List[str]:
    return json.loads(CONFIG_PATH.read_text())["priority"]

def load_cache() -> dict:
    return json.loads(CACHE_PATH.read_text())

def save_cache(cache: dict):
    CACHE_PATH.write_text(json.dumps(cache, indent=2, ensure_ascii=False))

def google_search(sku: str, domains: List[str]) -> str:
    print(f"[Search] Starting search for SKU: {sku}")
    headers = {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
            "Mozilla/5.0 (X11; Linux x86_64)..."
        ])
    }
    query = f"{sku} " + " ".join([f"site:{domain}" for domain in domains])
    params = {"q": query, "hl": "es"}
    url = "https://www.google.com/search"

    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.select("a"):
            href = link.get("href")
            if href and "url?q=" in href:
                actual = href.split("url?q=")[1].split("&")[0]
                if any(domain in actual for domain in domains):
                    print(f"[Search] Found: {actual}")
                    return actual
    except Exception as e:
        print(f"[Search] Error: {e}")

    print("[Search] No result found at all.")
    return None


def scrape_product_info(sku: str) -> dict:
    cache = load_cache()

    if sku in cache:
        print(f"[Cache] Found in local cache: {sku}")
        return cache[sku]

    priority_sites = get_priority_sites()
    SITE_BATCH_SIZE = 5
    url = None

    for i in range(0, len(priority_sites), SITE_BATCH_SIZE):
        batch = priority_sites[i:i + SITE_BATCH_SIZE]
        url = google_search(sku, batch)
        if url:
            break  # Salimos si encontramos un resultado

    print(f"[Scraper] URL selected: {url}")

    if not url:
        product_info = _unknown_product()
    else:
        product_info = scrape_generic(url)

    # Guardar en cache
    cache[sku] = product_info
    save_cache(cache)

    return product_info


def scrape_generic(url: str) -> dict:
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/113.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code != 200:
            return _error_product(resp.status_code, resp.reason)

        soup = BeautifulSoup(resp.text, "html.parser")

        name_tag = soup.find("h1") or soup.title
        name = name_tag.text.strip() if name_tag else "Producto desconocido"

        image = None
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if any(k in src.lower() for k in ["product", "main", "item"]) and src.endswith((".jpg", ".png", ".jpeg")):
                image = src
                break

        return {
            "product": name,
            "brand": "Desconocida",
            "category": "General",
            "image": image
        }

    except Exception as e:
        print(f"[Scraper] Error scraping: {e}")
        return _unknown_product()

def _unknown_product():
    return {
        "product": "Producto desconocido",
        "brand": "Desconocida",
        "category": "General",
        "image": None
    }

def _error_product(code: int, reason: str):
    return {
        "product": f"Error {code} {reason}",
        "brand": "Desconocida",
        "category": "General",
        "image": None
    }

