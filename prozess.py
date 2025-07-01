# prozess.py
"""
Dieses Modul implementiert einen systemweiten Hotkey-Listener, der als reiner Auslöser dient.

- Überwacht eine Tastenkombination.
- Prüft bei Auslösung, ob ein bestimmter Prozess läuft.
- Ruft bei Erfolg eine übergebene Callback-Funktion auf.
"""
import logging
import time

try:
    import keyboard
    import psutil
except ImportError as e:
    logging.critical(f"Kritischer Fehler: Notwendige Bibliotheken nicht gefunden: {e}. "
                     f"Bitte installieren: pip install keyboard psutil")
    raise

# --- Konfiguration (BITTE HIER ANPASSEN) ---
HOTKEY_COMBINATION = "ctrl+alt+s"
TARGET_PROCESS_NAME = "esprit.exe"  # Wichtig: Dein Zielprozess

logger = logging.getLogger(__name__)


def check_if_process_running(process_name: str) -> bool:
    """Prüft, ob ein Prozess mit dem angegebenen Namen gerade läuft."""
    logger.debug(f"Suche nach laufendem Prozess: '{process_name}'")
    for proc in psutil.process_iter(['name']):
        if proc.info['name'].lower() == process_name.lower():
            logger.info(f"Prozess '{process_name}' gefunden.")
            return True
    logger.info(f"Prozess '{process_name}' wurde nicht gefunden.")
    return False


def on_hotkey_pressed(trigger_callback):
    """
    Callback-Funktion für den Hotkey. Prüft den Prozess und ruft bei Erfolg den übergebenen Callback auf.
    """
    logger.info(f"Hotkey '{HOTKEY_COMBINATION}' erkannt.")
    if check_if_process_running(TARGET_PROCESS_NAME):
        logger.info("Prozess gefunden, rufe den Trigger-Callback auf (start_ocr_process_thread).")
        trigger_callback()
    else:
        logger.warning(f"Aktion wird nicht ausgeführt, da der Prozess '{TARGET_PROCESS_NAME}' nicht läuft.")


def start_hotkey_listener(ocr_trigger_callback):
    """
    Registriert den systemweiten Hotkey und startet den Listener.

    :param ocr_trigger_callback: Die Funktion, die aufgerufen werden soll, wenn der Hotkey gedrückt wird
                                und der Prozess läuft. (In unserem Fall: start_ocr_process_thread)
    """
    try:
        # Das Lambda ist nötig, um unseren Callback an die keyboard-Funktion zu übergeben.
        keyboard.add_hotkey(HOTKEY_COMBINATION, lambda: on_hotkey_pressed(ocr_trigger_callback))

        logger.info(f"Systemweiter Hotkey '{HOTKEY_COMBINATION}' wurde registriert. Listener ist aktiv.")
        # Diese Schleife hält den Thread am Leben.
        while True:
            time.sleep(3600)
    except Exception as e:
        logger.error(f"Fehler beim Initialisieren des Hotkey-Listeners: {e}", exc_info=True)