#!/usr/bin/env python3
import os, time, json, random, logging, requests, warnings
from dataclasses import dataclass
from typing import List, Optional
try:
    import tomllib  # Py 3.11+
except Exception:
    import tomli as tomllib  # fallback Py <3.11

# Silenciar warning de LibreSSL en macOS (Python del sistema)
try:
    from urllib3.exceptions import NotOpenSSLWarning
    warnings.filterwarnings("ignore", category=NotOpenSSLWarning)
except Exception:
    pass

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

@dataclass
class Product:
    name: str
    url: str
    available_keywords: List[str]
    soldout_keywords: List[str]
    country_code: Optional[str] = None  # "DISCOVERY" o "AR"

def load_config(path: str = "config.toml"):
    with open(path, "rb") as f:
        return tomllib.load(f)

def http_get(url: str, timeout: int = 40) -> requests.Response:
    """GET con headers + reintentos exponenciales para 429/5xx/timeout."""
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    s = requests.Session()
    try:
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        retry = Retry(
            total=3,
            backoff_factor=1.5,                 # 0s, 1.5s, 3s, 4.5s...
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET"]),
            raise_on_status=False,
        )
        s.mount("https://", HTTPAdapter(max_retries=retry))
        s.mount("http://", HTTPAdapter(max_retries=retry))
    except Exception:
        pass
    return s.get(url, headers=headers, timeout=timeout, allow_redirects=True)

def looks_available(html: str, avail: List[str], soldout: List[str]) -> bool:
    h = html.lower()
    hit_avail = any(k.lower() in h for k in avail) if avail else False
    hit_sold  = any(k.lower() in h for k in soldout) if soldout else False
    return hit_avail and not hit_sold

def notify_telegram(bot_token: str, chat_id: str, text: str):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    r = requests.post(url, json=payload, timeout=20)
    r.raise_for_status()

def load_state(path="state.json") -> dict:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_state(state: dict, path="state.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=[logging.FileHandler("log.txt", encoding="utf-8"), logging.StreamHandler()]
    )
    cfg = load_config("config.toml")
    import sys
    logging.info("Python en runtime: %s", sys.version)


    bot_token = os.getenv("TELEGRAM_BOT_TOKEN") or cfg.get("telegram", {}).get("bot_token")
    chat_id   = os.getenv("TELEGRAM_CHAT_ID") or cfg.get("telegram", {}).get("chat_id")
    if not bot_token or not chat_id:
        logging.error("Falta TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID (env o config.toml).")
        return

    state = load_state()
    products: List[Product] = []
    for p in cfg.get("products", []):
        products.append(Product(
            name=p["name"],
            url=p["url"],
            available_keywords=[s.lower() for s in p.get("available_keywords", ["agregar al carrito","en stock","comprar ahora"])],
            soldout_keywords=[s.lower() for s in p.get("soldout_keywords", ["agotado","sin stock","no disponible"])],
            country_code=p.get("country_code")
        ))

    for prod in products:
        try:
            resp = http_get(prod.url)
            html = resp.text
            is_avail = looks_available(html, prod.available_keywords, prod.soldout_keywords)
            key = prod.url
            prev = state.get(key, {"available": False})
            if is_avail and not prev.get("available"):
                label = "¡Hay stock!" if (prod.country_code != "DISCOVERY") else "¡Novedad detectada!"
                msg = f"✅ <b>{label}</b>\n<b>{prod.name}</b>\n{prod.url}"
                notify_telegram(bot_token, chat_id, msg)
                state[key] = {"available": True, "last_seen_available": int(time.time())}
                logging.info("Notificado: %s", prod.name)
            elif not is_avail:
                state[key] = {"available": False, "last_seen_unavailable": int(time.time())}
                logging.info("Sin stock: %s", prod.name)
        except Exception as e:
            logging.exception("Error con %s: %s", prod.name, e)
        # Pausa suave entre páginas para reducir rate-limit/timeouts
        time.sleep(2)

    save_state(state)

if __name__ == "__main__":
    main()
