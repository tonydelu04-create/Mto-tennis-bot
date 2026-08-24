"""
MTO Checker - controlla i match di tennis live (ATP/WTA) e invia una
notifica Telegram quando viene rilevato un medical timeout (MTO).

Fonte dati: API pubblica (non ufficiale) di SofaScore.
Notifiche: Bot Telegram (token e chat id passati come variabili d'ambiente).

Il programma tiene traccia degli eventi gia' notificati in un file
"sent_incidents.json" cosi' da non mandare due volte lo stesso avviso.
"""

import json
import os
import sys
import time
from pathlib import Path

import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

SOFASCORE_LIVE_URL = "https://api.sofascore.com/api/v1/sport/tennis/events/live"
SOFASCORE_INCIDENTS_URL = "https://api.sofascore.com/api/v1/event/{event_id}/incidents"

STATE_FILE = Path(__file__).parent / "sent_incidents.json"

# Parole chiave che indicano un medical timeout negli eventi/incidenti
# restituiti da SofaScore. Elenco volutamente ampio per non perdere segnali.
MEDICAL_KEYWORDS = [
    "medical",
    "mto",
    "physio",
    "treatment",
    "injury timeout",
    "injury time-out",
    "injury time out",
]

# Parole che, se presenti, escludono un falso positivo innocuo
# (es. "medical certificate", "physiotherapist bio" in un testo non legato all'evento)
EXCLUDE_KEYWORDS = ["certificate", "sponsor"]

HEADERS = {
    # Un User-Agent "normale" riduce il rischio di essere bloccati
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def load_sent_ids():
    if STATE_FILE.exists():
        try:
            return set(json.loads(STATE_FILE.read_text()))
        except (json.JSONDecodeError, ValueError):
            return set()
    return set()


def save_sent_ids(ids):
    # Teniamo solo gli ultimi 2000 id per non far crescere il file all'infinito
    trimmed = list(ids)[-2000:]
    STATE_FILE.write_text(json.dumps(trimmed))


def send_telegram_message(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERRORE: TELEGRAM_TOKEN o TELEGRAM_CHAT_ID mancanti.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"Errore invio Telegram: {e}")
        return False


def get_live_tennis_events():
    try:
        resp = requests.get(SOFASCORE_LIVE_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json().get("events", [])
    except requests.RequestException as e:
        print(f"Errore nel recupero dei match live: {e}")
        return []


def get_event_incidents(event_id):
    url = SOFASCORE_INCIDENTS_URL.format(event_id=event_id)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        return resp.json().get("incidents", [])
    except requests.RequestException as e:
        print(f"Errore nel recupero incidenti per evento {event_id}: {e}")
        return []


def _collect_strings(value, out):
    """Raccoglie ricorsivamente tutti i valori testuali/numerici da un
    oggetto JSON annidato (dict, list, o valore semplice)."""
    if isinstance(value, dict):
        for v in value.values():
            _collect_strings(v, out)
    elif isinstance(value, list):
        for v in value:
            _collect_strings(v, out)
    elif value is not None:
        out.append(str(value))


def is_medical_incident(incident):
    # Non ci fidiamo di pochi campi specifici: lo schema esatto usato da
    # SofaScore per il tennis non e' documentato ufficialmente e potrebbe
    # cambiare o variare da match a match. Scansioniamo quindi TUTTO il
    # contenuto dell'incidente, in qualunque campo si trovi.
    pieces = []
    _collect_strings(incident, pieces)
    combined = " ".join(pieces).lower()

    if any(exclude in combined for exclude in EXCLUDE_KEYWORDS):
        return False

    return any(keyword in combined for keyword in MEDICAL_KEYWORDS)


def build_match_label(event):
    home = event.get("homeTeam", {}).get("name", "?")
    away = event.get("awayTeam", {}).get("name", "?")
    tournament = event.get("tournament", {}).get("name", "")
    return home, away, tournament


def format_score(event):
    try:
        hs = event.get("homeScore", {})
        as_ = event.get("awayScore", {})
        sets = []
        for i in range(1, 6):
            h = hs.get(f"period{i}")
            a = as_.get(f"period{i}")
            if h is None or a is None:
                break
            sets.append(f"{h}-{a}")
        return " ".join(sets) if sets else "N/D"
    except Exception:
        return "N/D"


def check_once():
    sent_ids = load_sent_ids()
    events = get_live_tennis_events()
    print(f"Match live trovati: {len(events)}")

    new_sent = set(sent_ids)

    for event in events:
        event_id = event.get("id")
        if event_id is None:
            continue

        incidents = get_event_incidents(event_id)
        for incident in incidents:
            incident_id = incident.get("id") or f"{event_id}-{incident.get('time')}-{incident.get('incidentType')}"
            unique_key = f"{event_id}:{incident_id}"

            if unique_key in new_sent:
                continue

            if is_medical_incident(incident):
                home, away, tournament = build_match_label(event)
                score = format_score(event)
                message = (
                    "🚑 <b>Medical Timeout!</b>\n"
                    f"🎾 {home} vs {away}\n"
                    f"🏆 {tournament}\n"
                    f"📊 Punteggio: {score}"
                )
                sent_ok = send_telegram_message(message)
                if sent_ok:
                    print(f"Notifica inviata: {home} vs {away}")
                    new_sent.add(unique_key)

    save_sent_ids(new_sent)


if __name__ == "__main__":
    check_once()
