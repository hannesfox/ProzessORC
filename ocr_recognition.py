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

def ocr_line_parse(gray_img: np.ndarray) -> tuple[dict, str]:
    """Führt OCR durch und extrahiert spezifische Daten."""
    if gray_img is None or gray_img.size == 0:
        logger.error("Ungültiges Graustufenbild an ocr_line_parse übergeben.")
        raise ValueError("Ungültiges Graustufenbild für OCR erhalten.")

    # --- Beginn des Upscaling-Blocks ---
    #
    scale_factor = 1.5
    logger.info(f"Upscaling Graustufenbild mit Faktor: {scale_factor}")

    height, width = gray_img.shape
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)


    upscaled_gray_img = cv2.resize(gray_img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
    logger.debug(f"Originalgröße: {width}x{height}, Skalierte Größe: {new_width}x{new_height}")


    # --- Ende des Upscaling-Blocks ---

    config = f"--oem 3 --psm 4 --dpi 300 -l {TESS_LANG}"   #4 war gut
    full_text = ""
    try:
        # Verwende das skalierte Bild für die OCR
        full_text = pytesseract.image_to_string(upscaled_gray_img, config=config)
        logger.info(f"--- OCR Roh-Text (nach Upscaling) ---\n{full_text}\n--------------------")
    except pytesseract.TesseractNotFoundError as tess_err:
        logger.error(f"Tesseract nicht gefunden oder Pfad falsch konfiguriert: {tess_err}")
        raise
    except Exception as e:
        logger.error(f"Fehler während der OCR-Verarbeitung: {e}", exc_info=True)
        raise RuntimeError(f"Fehler während der OCR: {e}") from e

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
        "Feature-Typ": r".*(?:Feature|Festure|Feauture|Fenture)[-\s]*Typ\s*[:.\-–\s|]*([^\n]+)",
        "Name": r".*Name\s*[:.\-–\s|]*([^\n]+)",
        "Kleinster Radius": r".*Kleinster\s+Radius\s*[:.\-–\s|]*([^\n]+)"
    }

    def parse_number(value_str: str, format_str: str | None = "{:.3f}") -> str | None:
        if not isinstance(value_str, str): return None
        cleaned_str = value_str.replace(",", ".").strip()
        cleaned_str = re.sub(r"[^\d.\s-]*$", "", cleaned_str).strip()
        cleaned_str = re.sub(r"^[^\d-]*", "", cleaned_str).strip()
        match = re.search(r"(-?\d+(?:\.\d+)?)", cleaned_str)
        if match:
            num_str = match.group(1)
            try:
                val = float(num_str)
                logger.debug(f"PARSE_NUMBER: Input='{value_str}', Cleaned='{cleaned_str}', MatchedNum='{num_str}', FloatVal={val}")
                return format_str.format(val) if format_str else num_str
            except ValueError:
                logger.warning(f"PARSE_NUMBER: Konnte extrahierten Wert '{num_str}' (von Rohwert '{value_str}') nicht in Float umwandeln. Gebe extrahierten String '{num_str}' zurück.")
                return num_str
        elif value_str.strip():
             logger.warning(f"PARSE_NUMBER: Konnte keine klare Zahl in '{value_str}' (bereinigt: '{cleaned_str}') parsen. Gebe bereinigten String '{cleaned_str}' zurück.")
             return cleaned_str
        logger.debug(f"PARSE_NUMBER: Input='{value_str}' (bereinigt: '{cleaned_str}') führt zu Rückgabe None (oder leerem String, der wie None behandelt wird).")
        return None


    lines = full_text.splitlines()
    processed_keys = set()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        for key, pattern_str in patterns.items():
            if key in processed_keys and results[key] is not None:
                if key == "Durchmesser":
                    logger.debug(f"DURCHMESSER-SKIP: Schlüssel '{key}' bereits in processed_keys und results[{key}]='{results[key]}'. Überspringe Zeile: '{line}' für dieses Pattern.")
                continue

            match = re.search(pattern_str, line, re.IGNORECASE)

            if match:
                try:
                    raw_value = match.group(1).strip()
                except IndexError:
                    logger.error(f"Fehler beim Extrahieren von group(1) für Key '{key}' mit Pattern '{pattern_str}' in Zeile '{line}'. Match-Objekt: {match.groups()}")
                    continue

                parsed_value = None

                if key in ["Tiefe", "Durchmesser", "Begrenzungsbox Breite", "Begrenzungsbox Länge", "Kleinster Radius"]:
                    parsed_value = parse_number(raw_value, None if key == "Durchmesser" else "{:.6f}")
                    if key == "Durchmesser":
                        logger.info(f"DURCHMESSER-VERSUCH: Roh='{raw_value}', Geparsed='{parsed_value}' (Pattern='{pattern_str}', Zeile='{line}')")

                elif key == "Elementnummer":
                    if raw_value.isdigit():
                        parsed_value = raw_value
                    else:
                        logger.warning(f"Ungültiger Rohwert für Elementnummer: '{raw_value}' in Zeile '{line}'. Versuche, Ziffern zu extrahieren.")
                        num_match = re.search(r"(\d+)", raw_value)
                        if num_match:
                            parsed_value = num_match.group(1)
                            logger.info(f"Extrahierte Elementnummer '{parsed_value}' aus '{raw_value}'.")
                else:
                    parsed_value = raw_value if raw_value else None

                if parsed_value is not None and parsed_value.strip() != "":
                    results[key] = parsed_value
                    processed_keys.add(key)

                    log_action = "Gefunden"
                    if key in ["Tiefe", "Durchmesser", "Begrenzungsbox Breite", "Begrenzungsbox Länge", "Elementnummer", "Kleinster Radius"] and raw_value != parsed_value:
                        log_action += " & Geparsed"
                    logger.info(f"{log_action}: {key} = '{results[key]}' (Roh: '{raw_value}') in Zeile: '{line}'")

                elif key == "Durchmesser" and (parsed_value is None or parsed_value.strip() == ""):
                    logger.info(f"DURCHMESSER-VERWORFEN: Rohwert '{raw_value}' für Schlüssel '{key}' konnte nicht als gültige Zahl geparsed werden (Ergebnis: '{parsed_value}'). Zeile: '{line}'. Pattern: '{pattern_str}'")

    logger.info(f"OCR Parsing Ergebnisse (FINAL): {results}")
    return results, full_text