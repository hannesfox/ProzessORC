# ocr_recognition.py
"""
Dieses Modul enthält Hilfsfunktionen für den OCR-Prozess:
- Bildschirmaufnahme
- Bildvorverarbeitung
- OCR-Texterkennung und Parsing.
"""

import os
import re
import cv2
import numpy as np
from PIL import ImageGrab, Image
import pytesseract
import time
import logging

# --- Logging  ---
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - (%(module)s) - %(message)s')

# --- OCR Konfiguration ---
SCREEN_REGION = (7, 496, 364, 1382)  # (links, oben, rechts, unten) - ANPASSEN!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
TESS_LANG = "deu"
TESS_CMD_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # ANPASSEN!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# --- Tesseract Pfad  ---
tesseract_cmd_set = False
if TESS_CMD_PATH and os.path.exists(TESS_CMD_PATH):
    try:
        pytesseract.pytesseract.tesseract_cmd = TESS_CMD_PATH
        tesseract_cmd_set = True
        logger.info(f"Tesseract Pfad erfolgreich gesetzt auf: {TESS_CMD_PATH}")
    except Exception as e:
        logger.error(f"Fehler beim Setzen des Tesseract Pfades: {e}")
elif TESS_CMD_PATH:
    logger.warning(f"Angegebener Tesseract Pfad existiert nicht: {TESS_CMD_PATH}")
else:
    logger.info("Kein spezifischer Tesseract Pfad (TESS_CMD_PATH) angegeben, versuche Systempfad.")

try:
    tess_version = pytesseract.get_tesseract_version()
    logger.info(f"Tesseract erfolgreich gefunden und Version überprüft: {tess_version}")
except pytesseract.TesseractNotFoundError:
    logger.error("Tesseract nicht gefunden.")
except Exception as e:
    logger.error(f"Fehler beim Überprüfen der Tesseract-Version: {e}")

# --- OCR Funktionen ---

def capture_to_cv2(bbox: tuple[int, int, int, int]) -> np.ndarray:
    """Erfasst Screenshot des Bereichs bbox und konvertiert zu OpenCV-Format."""
    try:
        pil_img = ImageGrab.grab(bbox=bbox, all_screens=True)
        if pil_img is None:
            raise RuntimeError("ImageGrab.grab (all_screens=True) lieferte None zurück.")
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception as e:
        logger.warning(f"Fehler bei ImageGrab (all_screens=True): {e}. Versuche Standard-Grab...")
        time.sleep(0.2)
        try:
            pil_img = ImageGrab.grab(bbox=bbox)
            if pil_img is None:
                 raise RuntimeError("ImageGrab.grab lieferte None zurück.")
            logger.info("Erneuter Versuch der Screenshot-Erfassung (Standard) erfolgreich.")
            return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        except Exception as e2:
            logger.error(f"Erneuter Fehler bei ImageGrab: {e2}", exc_info=True)
            raise RuntimeError(f"Screenshot konnte nicht erfasst werden: {e2}") from e2

def preprocess(cv_img: np.ndarray) -> np.ndarray:
    """Wendet Graustufen-Vorverarbeitung an."""
    if cv_img is None or cv_img.size == 0:
        logger.error("Ungültiges Bild an preprocess übergeben.")
        raise ValueError("Ungültiges Bild für Vorverarbeitung erhalten.")
    return cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)


# In ocr_recognition.py

def ocr_line_parse(gray_img: np.ndarray) -> tuple[dict, str]:
    """
    Führt OCR durch und extrahiert spezifische Daten.
    Verwendet eine Zwei-Durchlauf-Strategie, um spezifische Erkennungsfehler zu korrigieren.
    """
    if gray_img is None or gray_img.size == 0:
        logger.error("Ungültiges Graustufenbild an ocr_line_parse übergeben.")
        raise ValueError("Ungültiges Graustufenbild für OCR erhalten.")

    # --- Bildvorverarbeitung (Upscaling + Binarisierung für bessere Erkennung) ---
    scale_factor = 2.0  # Ein höherer Skalierungsfaktor gibt Tesseract mehr Pixel zum Arbeiten
    logger.info(f"Upscaling Graustufenbild mit Faktor: {scale_factor}")
    height, width = gray_img.shape
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)
    upscaled_gray_img = cv2.resize(gray_img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

    # Adaptives Thresholding ist oft besser als nur Graustufen
    processed_img = cv2.adaptiveThreshold(upscaled_gray_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11,
                                          2)

    # Debug-Bild speichern, um zu sehen, was Tesseract bekommt
    cv2.imwrite("debug_ocr_final_image.png", processed_img)
    logger.info("Debug-Bild zur Überprüfung als 'debug_ocr_final_image.png' gespeichert.")

    # --- 1. ERSTER OCR-DURCHLAUF (Standard mit psm 4) ---
    config_pass1 = f"--oem 3 --psm 4 --dpi 300 -l {TESS_LANG}"
    full_text_pass1 = ""
    try:
        logger.info(f"Starte OCR-Durchlauf 1 mit Konfiguration: {config_pass1}")
        full_text_pass1 = pytesseract.image_to_string(processed_img, config=config_pass1)
        logger.info(f"--- OCR Roh-Text (Durchlauf 1) ---\n{full_text_pass1}\n--------------------")
    except Exception as e:
        logger.error(f"Fehler während OCR-Durchlauf 1: {e}", exc_info=True)
        # Wenn der erste Durchlauf fehlschlägt, können wir nicht fortfahren
        raise RuntimeError(f"Kritischer Fehler im ersten OCR-Durchlauf: {e}") from e

    # --- Initiales Parsen der Ergebnisse aus dem ersten Durchlauf ---
    # Die Parsing-Logik (parse_number, Regex, etc.) bleibt genau wie bei Ihnen.
    # Ich habe sie hier zur Vollständigkeit eingefügt.
    results = {
        "Elementtyp": None, "Elementnummer": None, "Begrenzungsbox Breite": None,
        "Begrenzungsbox Länge": None, "Tiefe": None, "Durchmesser": None,
        "Feature-Typ": None, "Name": None, "Kleinster Radius": None
    }
    patterns = {
        "Elementtyp": r".*Elementtyp\s*[:.\-–\s|]*([^\n]+)",
        "Elementnummer": r".*Elementnummer\s*[:.\-–\s|]*(\d+)",
        "Tiefe": r".*Tiefe\s*[:.\-–\s|]*,?\s*([^\n]+)",
        "Durchmesser": r"^(?:[^\S\n]*(?:Durchmesser|Duahmaser|Duchmesser|Durchmeser|Bohezurchmaser|Durngangg|Boden))\s*[:.\-–\s|]*([^\n]+)",
        "Begrenzungsbox Breite": r".*Begrenzungsbox\s+Breite\s*[:.\-–\s|]*([^\n]+)",
        "Begrenzungsbox Länge": r".*Begrenzungsbox\s+Länge\s*[:.\-–\s|]*([^\n]+)",
        "Feature-Typ": r".*(?:F?eature|Festure|Feauture|Fenture)[-\s]*Typ\s*[:.\-–\s|]*([^\n]+)",
        "Name": r".*Name\s*[:.\-–\s|]*([^\n]+)",
        "Kleinster Radius": r".*Kleinster\s+Radius\s*[:.\-–\s|]*([^\n]+)"
    }

    def parse_number(value_str: str, format_str: str | None = "{:.3f}") -> str | None:
        if not isinstance(value_str, str): return None
        # Ihre parse_number Funktion ist gut, wir behalten sie bei.
        cleaned_str = value_str.replace(",", ".").strip()
        cleaned_str = re.sub(r"[^\d.\s-]*$", "", cleaned_str).strip()
        cleaned_str = re.sub(r"^[^\d-]*", "", cleaned_str).strip()
        match = re.search(r"(-?\d+(?:\.\d+)?)", cleaned_str)
        if match:
            num_str = match.group(1)
            try:
                val = float(num_str)
                return format_str.format(val) if format_str else num_str
            except ValueError:
                return num_str  # Gib den gefundenen String zurück, wenn er keine Zahl ist
        return cleaned_str if value_str.strip() else None

    lines = full_text_pass1.splitlines()
    processed_keys = set()
    for line in lines:
        line = line.strip()
        if not line: continue
        for key, pattern_str in patterns.items():
            if key in processed_keys and results[key] is not None: continue
            match = re.search(pattern_str, line, re.IGNORECASE)
            if match:
                raw_value = match.group(1).strip()
                parsed_value = None
                if key in ["Tiefe", "Durchmesser", "Begrenzungsbox Breite", "Begrenzungsbox Länge", "Kleinster Radius"]:
                    parsed_value = parse_number(raw_value, None if key == "Durchmesser" else "{:.6f}")
                elif key == "Elementnummer":
                    parsed_value = re.search(r"(\d+)", raw_value).group(1) if re.search(r"(\d+)",
                                                                                        raw_value) else raw_value
                else:
                    parsed_value = raw_value if raw_value else None

                if parsed_value is not None and str(parsed_value).strip() != "":
                    results[key] = str(parsed_value)
                    processed_keys.add(key)
                    logger.info(f"Gefunden (Durchlauf 1): {key} = '{results[key]}' (Roh: '{raw_value}')")

    # --- 2. PRÜFUNG AUF PROBLEM-FALL & GEZIELTE KORREKTUR ---
    # Prüfen, ob der bekannte Fehler bei "Begrenzungsbox Länge" aufgetreten ist.
    problematic_value = "10.000000"
    if results.get("Begrenzungsbox Länge") == problematic_value:
        logger.warning(f"Problemfall erkannt: 'Begrenzungsbox Länge' ist '{problematic_value}'. Starte Korrekturlauf.")

        config_pass2 = f"--oem 3 --psm 11 --dpi 300 -l {TESS_LANG}"  # psm 11 für die Korrektur
        full_text_pass2 = ""
        try:
            logger.info(f"Starte OCR-Durchlauf 2 (Korrektur) mit Konfiguration: {config_pass2}")
            full_text_pass2 = pytesseract.image_to_string(processed_img, config=config_pass2)
            logger.info(f"--- OCR Roh-Text (Durchlauf 2) ---\n{full_text_pass2}\n--------------------")

            # Jetzt parsen wir den Text aus dem zweiten Durchlauf, aber NUR für den fehlerhaften Schlüssel
            for line_pass2 in full_text_pass2.splitlines():
                match_pass2 = re.search(patterns["Begrenzungsbox Länge"], line_pass2, re.IGNORECASE)
                if match_pass2:
                    raw_value_pass2 = match_pass2.group(1).strip()
                    parsed_value_pass2 = parse_number(raw_value_pass2, "{:.6f}")

                    # Nur wenn ein neuer, anderer Wert gefunden wurde, wird er aktualisiert.
                    if parsed_value_pass2 and parsed_value_pass2 != problematic_value:
                        logger.info(
                            f"KORREKTUR ERFOLGREICH: 'Begrenzungsbox Länge' von '{results['Begrenzungsbox Länge']}' auf '{parsed_value_pass2}' geändert.")
                        results["Begrenzungsbox Länge"] = parsed_value_pass2
                        break  # Wir haben die Korrektur, Schleife beenden.

        except Exception as e:
            logger.error(
                f"Fehler während des Korrekturlaufs (Durchlauf 2): {e}. Ergebnis aus Durchlauf 1 wird beibehalten.")

    logger.info(f"OCR Parsing Ergebnisse (FINAL): {results}")
    return results, full_text_pass1  # Wir geben den Text des ersten Durchlaufs zurück, da er die richtige Struktur hat