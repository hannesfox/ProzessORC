# rule_engine.py
"""
Dieses Modul enthält die Logik zur regelbasierten Zuordnung von .prc-Dateien.
Es geht davon aus, dass die OCR-Kriterien zu einem logischen Prozess führen,
der durch einen numerischen Präfix im Dateinamen (XX_) innerhalb eines
spezifischen Unterordners identifiziert wird. Der Rest des Dateinamens kann variieren.

Regel-Struktur:
  [Keywords],
  Lambda-Bedingung (erwartet: ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r),
  (RELATIVER_UNTERORDNER, PRÄFIX) ODER Aktions-Lambda (erwartet gleiche Argumente wie Bedingung, gibt (RELATIVER_UNTERORDNER, PRÄFIX) zurück)
Beispiel für das dritte Element (statisch): (r"01_Plan-Aussen-Fase-Tasche", "01")
"""

import os
import logging
import re

from sympy import andre

# --- Logging Konfiguration ---
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - (%(module)s) - %(message)s')


# --- Regelbasierte Zuordnung für .prc-Dateien ---

def find_prc_path_by_rules(feature_type_lower: str | None, ocr_all_results: dict,
                           material_root_path: str | None) -> str | None:
    if not feature_type_lower or not ocr_all_results or not material_root_path:
        logger.warning(
            f"find_prc_path_by_rules mit unvollständigen Daten: ft='{feature_type_lower}', ocr_results='{ocr_all_results}', root='{material_root_path}'"
        )
        return None

    # --- Werteextraktion aus OCR ---
    d_float_str = ocr_all_results.get("Durchmesser")
    d_float = None
    if d_float_str:
        try:
            d_float = float(str(d_float_str).replace(",", "."))
        except ValueError:
            logger.warning(f"Konnte Durchmesser '{d_float_str}' nicht in Float umwandeln.")

    tiefe_str = ocr_all_results.get("Tiefe")
    tiefe_float = None
    if tiefe_str:
        try:
            tiefe_float = float(str(tiefe_str).replace(",", "."))
        except ValueError:
            logger.warning(f"Konnte Tiefe '{tiefe_str}' nicht in Float umwandeln.")

    bbox_breite_str = ocr_all_results.get("Begrenzungsbox Breite")
    bbox_breite_float = None
    if bbox_breite_str:
        try:
            bbox_breite_float = float(str(bbox_breite_str).replace(",", "."))
        except ValueError:
            logger.warning(f"Konnte Begrenzungsbox Breite '{bbox_breite_str}' nicht in Float umwandeln.")

    bbox_laenge_str = ocr_all_results.get("Begrenzungsbox Länge")
    bbox_laenge_float = None
    if bbox_laenge_str:
        try:
            bbox_laenge_float = float(str(bbox_laenge_str).replace(",", "."))
        except ValueError:
            logger.warning(f"Konnte Begrenzungsbox Länge '{bbox_laenge_str}' nicht in Float umwandeln.")

    kleinster_radius_str = ocr_all_results.get("Kleinster Radius")
    kleinster_radius_float = None
    if kleinster_radius_str:
        try:
            kleinster_radius_float = float(str(kleinster_radius_str).replace(",", "."))
        except ValueError:
            logger.warning(f"Konnte Kleinster Radius '{kleinster_radius_str}' nicht in Float umwandeln.")

    logger.info(
        f"Suche PRC: Feature='{feature_type_lower}', Ø='{d_float_str}' (num: {d_float}), "
        f"Tiefe='{tiefe_str}' (num: {tiefe_float}), "
        f"BBoxBreite='{bbox_breite_str}' (num: {bbox_breite_float}), BBoxLänge='{bbox_laenge_str}' (num: {bbox_laenge_float}), "
        f"KlRadius='{kleinster_radius_str}' (num: {kleinster_radius_float}), Material-Root='{material_root_path}'"
    )

    # --- Regeldefinitionen --------------------------------------------------------------------------

    base_rules = [

        # --- Planen (kombinierte Regel) ---
        (["plan"],
            lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r:
            tief is not None and 0.0 <= tief <= 62.0 and
            bbox_b is not None and 0.0 < bbox_b <= 2000.0 and
            bbox_l is not None and 0.0 < bbox_l <= 2000.0,
            # Aktions-Lambda
            lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r:
            (r"01_Plan-Aussen-Fase-Tasche", "06") if (
                    0.0 <= bbox_l <= 50.0 and  # X
                    0.0 <= bbox_b <= 60.0 and  # Y
                    0.0 <= tief <= 40.0  # Z
            ) else

            (r"01_Plan-Aussen-Fase-Tasche", "04") if (
                    50.01 <= bbox_l <= 160.0 and
                    0.0 <= bbox_b <= 45.0 and
                    0.0 <= tief <= 40.0
            ) else

            (r"01_Plan-Aussen-Fase-Tasche", "02") if (
                    40.01 <= tief <= 52.0
            ) else

            (r"01_Plan-Aussen-Fase-Tasche", "03") if "plan 10" in ft_lower else # Depo 16 - 10
            (r"01_Plan-Aussen-Fase-Tasche", "07") if "plan 16" in ft_lower else # Depo 16 - 16
            (r"01_Plan-Aussen-Fase-Tasche", "01")  # Depo 16 - 20
        ),

        # --- Nuten --- mit Rückzug muss immer vor nuten stehen !
        (["nuten rückzug"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: bbox_b is not None and 3.1 <= bbox_b <= 4.0,
         (r"07_NUTEN\NUTEN mit Rückzug", "01")),
        (["nuten rückzug"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: bbox_b is not None and 4.1 <= bbox_b <= 6.0,
         (r"07_NUTEN\NUTEN mit Rückzug", "02")),
        (["nuten rückzug"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: bbox_b is not None and 6.1 <= bbox_b <= 8.0,
         (r"07_NUTEN\NUTEN mit Rückzug", "03")),
        (["nuten rückzug"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: bbox_b is not None and 8.1 <= bbox_b <= 9.0,
         (r"07_NUTEN\NUTEN mit Rückzug", "04")),
        (["nuten rückzug"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: bbox_b is not None and 9.1 <= bbox_b <= 14.0,
         (r"07_NUTEN\NUTEN mit Rückzug", "05")),
        (["nuten rückzug"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: bbox_b is not None and 14.1 <= bbox_b <= 18.0,
         (r"07_NUTEN\NUTEN mit Rückzug", "06")),
        (["nuten rückzug"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: bbox_b is not None and 18.1 <= bbox_b <= 22.0,
         (r"07_NUTEN\NUTEN mit Rückzug", "07")),

        # --- Nuten ---
        (["nuten"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: bbox_b is not None and 3.1 <= bbox_b <= 4.0,
         (r"07_NUTEN", "01")),
        (["nuten"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: bbox_b is not None and 4.1 <= bbox_b <= 6.0,
         (r"07_NUTEN", "02")),
        (["nuten"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: bbox_b is not None and 6.1 <= bbox_b <= 8.0,
         (r"07_NUTEN", "03")),
        (["nuten"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: bbox_b is not None and 8.1 <= bbox_b <= 9.0,
         (r"07_NUTEN", "04")),
        (["nuten"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: bbox_b is not None and 9.1 <= bbox_b <= 14.0,
         (r"07_NUTEN", "05")),
        (["nuten"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: bbox_b is not None and 14.1 <= bbox_b <= 18.0,
         (r"07_NUTEN", "06")),
        (["nuten"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: bbox_b is not None and 18.1 <= bbox_b <= 22.0,
         (r"07_NUTEN", "07")),



        # --- Tasche Profit Offene Taschen mit Kleinster Radius erkennung---

        (["tasche profit box"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r:
        tief is not None and 0.0 <= tief <= 18.0 and
        kl_r is not None and 0.0 <= kl_r <= 1.5,
         (r"02_Taschen\Profit", "01")), #FR03

        (["tasche profit box"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r:
        tief is not None and 0.0 <= tief <= 21.0 and
        kl_r is not None and 1.51 <= kl_r <= 2.0,
         (r"02_Taschen\Profit", "02")), #FR04

        (["tasche profit box"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r:
        tief is not None and 0.0 <= tief <= 21.0 and
        kl_r is not None and 2.01 <= kl_r <= 2.5,
         (r"02_Taschen\Profit", "03")), #FR05

        (["tasche profit box"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r:
        tief is not None and 0.0 <= tief <= 20.0 and
        kl_r is not None and 2.51 <= kl_r <= 3.0,
         (r"02_Taschen\Profit", "04")), #FR06

        (["tasche profit box"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r:
        tief is not None and 0.0 <= tief <= 25.0 and
        kl_r is not None and 3.01 <= kl_r <= 4.0,
         (r"02_Taschen\Profit", "05")), #FR08

        (["tasche profit box"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r:
        tief is not None and 0.0 <= tief <= 40.0 and
        kl_r is not None and 4.01 <= kl_r <= 5.0,
         (r"02_Taschen\Profit", "07")), #FR10

        (["tasche profit box"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r:
        tief is not None and 0.0 <= tief <= 35.0 and
        kl_r is not None and 5.01 <= kl_r <= 6.0,
         (r"02_Taschen\Profit", "08")), #FR12

        (["tasche profit box"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r:
        tief is not None and 0.0 <= tief <= 40.0 and
        kl_r is not None and 6.01 <= kl_r <= 9.99,
         (r"02_Taschen\Profit", "10")), #FR16-16SL

        (["tasche profit box"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r:
        tief is not None and 0.0 <= tief <= 40.0 and
        kl_r is not None and 10.0 <= kl_r <= 200.0,
         (r"02_Taschen\Profit", "11")),  # FR16-20SL

        (["tasche profit box"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r:
        tief is not None and 40.01 <= tief <= 52.0 and
        kl_r is not None and 10.0 <= kl_r <= 200.0,
         (r"02_Taschen\Profit", "14")),  # FR16x52-20SL




        #------------Tasche Profit auswahl anhand Taschengröße und tiefe----------------

        (["tasche profit"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r:
        tief is not None and 0.0 <= tief <= 18.0 and
        bbox_l is not None and 0.0 <= bbox_l <= 10.0 and
        bbox_b is not None and 0.0 <= bbox_b <= 10.0,
         (r"02_Taschen\Profit", "01")),  #FR 03

        (["tasche profit"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r:
        tief is not None and 0.0 <= tief <= 21.0 and
        bbox_l is not None and 10.01 <= bbox_l <= 15.0 and
        bbox_b is not None and 10.01 <= bbox_b <= 15.0,
         (r"02_Taschen\Profit", "03")),  # FR 05

        (["tasche profit"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r:
        tief is not None and 0.0 <= tief <= 40.0 and
        bbox_l is not None and 15.01 <= bbox_l <= 30.0 and
        bbox_b is not None and 15.01 <= bbox_b <= 30.0,
         (r"02_Taschen\Profit", "07")),  # FR 10

        (["tasche profit"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r:
        tief is not None and 0.0 <= tief <= 40.0 and
        bbox_l is not None and 30.01 <= bbox_l <= 2000.0 and
        bbox_b is not None and 30.01 <= bbox_b <= 2000.0,
         (r"02_Taschen\Profit", "11")),  # FR 16 -20SL

        (["tasche profit"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r:
        tief is not None and 40.01 <= tief <= 52.0 and
        bbox_l is not None and 30.01 <= bbox_l <= 2000.0 and
        bbox_b is not None and 30.01 <= bbox_b <= 2000.0,
         (r"02_Taschen\Profit", "14")),  # FR 16 -20SL

        #Sondertasche
        (["tasche profit"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r:
        tief is not None and 0.0 <= tief <= 25.0 and
        bbox_l is not None and 50.0 <= bbox_l <= 2000.0 and
        bbox_b is not None and 10.0 <= bbox_b <= 2000.0 and
        kl_r is not None and 2.5 <= kl_r <= 5.0,
         (r"02_Taschen\Profit", "06")),  # FR 10 FR 05



        # --- Passung Fräsen ---
        (["passung fräsen"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 1.52 <= dia <= 2.5,
         (r"06_Passung Fräsen", "01")),
        (["passung fräsen"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 2.51 <= dia <= 3.5,
         (r"06_Passung Fräsen", "02")),
        (["passung fräsen"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 3.51 <= dia <= 4.5,
         (r"06_Passung Fräsen", "03")),
        (["passung fräsen"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 4.51 <= dia <= 6.5,
         (r"06_Passung Fräsen", "04")),
        (["passung fräsen"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 6.51 <= dia <= 8.5,
         (r"06_Passung Fräsen", "05")),
        (["passung fräsen"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 8.51 <= dia <= 10.5,
         (r"06_Passung Fräsen", "06")),
        (["passung fräsen"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 10.51 <= dia <= 14.5,
         (r"06_Passung Fräsen", "07")),
        (["passung fräsen"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 14.51 <= dia <= 18.5,
         (r"06_Passung Fräsen", "08")),
        (["passung fräsen"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 12.51 <= dia <= 23.5,
         (r"06_Passung Fräsen", "09")),

        (["passung fräsen"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r:
        dia is not None and 23.51 <= dia <= 31.0 and
        tief is not None and 0.0 <= tief <= 40.0,
         (r"06_Passung Fräsen", "10")),

        (["passung fräsen"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r:
        dia is not None and 31.01 <= dia <= 39.0 and
        tief is not None and 0.0 <= tief <= 40.0,
         (r"06_Passung Fräsen", "11")),

        (["passung fräsen"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r:
        dia is not None and 31.01 <= dia <= 39.0 and
        tief is not None and 40.01 <= tief <= 52.0,
         (r"06_Passung Fräsen", "13")),

        # --- Bohrung KM (mit Senkung) ---
        (["bohrung km"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 2.5 <= dia <= 3.7,
         (r"05_DGB\nur Senkung", "01")),
        (["bohrung km"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 4.0 <= dia <= 5.0,
         (r"05_DGB\nur Senkung", "02")),
        (["bohrung km"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 5.1 <= dia <= 6.2,
         (r"05_DGB\nur Senkung", "03")),
        (["bohrung km"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 6.3 <= dia <= 8.7,
         (r"05_DGB\nur Senkung", "04")),
        (["bohrung km"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 8.9 <= dia <= 10.0,
         (r"05_DGB\nur Senkung", "05")),
        (["bohrung km"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 10.1 <= dia <= 10.8,
         (r"05_DGB\nur Senkung", "06")),
        (["bohrung km"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 10.9 <= dia <= 12.0,
         (r"05_DGB\nur Senkung", "07")),
        (["bohrung km"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 12.1 <= dia <= 14.0,
         (r"05_DGB\nur Senkung", "08")),
        (["bohrung km"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 16.1 <= dia <= 18.0,
         (r"05_DGB\nur Senkung", "09")),

        # --- Trennen D80x3 ---
        (["trennen"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: True, (r"13_Trennen", "01")),

        # --- Bohrung Allgemein mit Rückzug  ---
        (["bohrung rückzug"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 2.0 <= dia < 6.97,
         (r"05_DGB\+DGB mit Rückzug", "01")),
        (["bohrung rückzug"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 7.02 <= dia < 9.29,
         (r"05_DGB\+DGB mit Rückzug", "01")),
        (["bohrung rückzug"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 6.99 <= dia < 7.01,
         (r"05_DGB\+DGB mit Rückzug", "03")),
        (["bohrung rückzug"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 9.3 <= dia <= 17.5,
         (r"05_DGB\+DGB mit Rückzug", "02")),
        (["bohrung rückzug"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 17.99 <= dia < 18.01,
         (r"05_DGB\+DGB mit Rückzug", "04")),
        (["bohrung rückzug"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 19.99 <= dia < 20.01,
         (r"05_DGB\+DGB mit Rückzug", "05")),
        (["bohrung rückzug"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 21.99 <= dia < 22.01,
         (r"05_DGB\+DGB mit Rückzug", "06")),
        (["bohrung rückzug"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 25.99 <= dia < 26.01,
         (r"05_DGB\+DGB mit Rückzug", "07")),

        # --- Bohrung Allgemein ---
        (["bohrung"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 2.0 <= dia < 6.97,
         (r"05_DGB", "01")),
        (["bohrung"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 7.02 <= dia < 9.29,
         (r"05_DGB", "01")),
        (["bohrung"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 6.99 <= dia < 7.01,
         (r"05_DGB", "03")),
        (["bohrung"], lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 9.3 <= dia <= 17.5,
         (r"05_DGB", "02")),
        (["bohrung"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 17.99 <= dia < 18.01,
         (r"05_DGB", "04")),
        (["bohrung"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 19.99 <= dia < 20.01,
         (r"05_DGB", "05")),
        (["bohrung"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 21.99 <= dia < 22.01,
         (r"05_DGB", "06")),
        (["bohrung"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 25.99 <= dia < 26.01,
         (r"05_DGB", "07")),

        # --- Gewinde --- mit Rückzug muss immer vor gewinde stehen!
        (["gewinde m rückzug"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 2.0 <= dia <= 7.0,
         (r"03_Bohrungen\Bohrungen mit Rückzug", "03")),
        (["gewinde m rückzug"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 7.01 < dia <= 12.5,
         (r"03_Bohrungen\Bohrungen mit Rückzug", "04")),

        # --- Gewinde ---
        (["gewinde m", "gewinde"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 2.0 <= dia <= 7.0,
         (r"03_Bohrungen", "03")),
        (["gewinde m", "gewinde"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 7.01 < dia <= 12.5,
         (r"03_Bohrungen", "04")),

        # --- Reiben --- mit Rückzug muss immer vor reiben stehen!
        (["reib ohne o rückzug"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 3.0 <= dia <= 8.05,
         (r"03_Bohrungen\Bohrungen mit Rückzug", "05")),
        (["reib ohne o rückzug"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 10.0 <= dia <= 12.05,
         (r"03_Bohrungen\Bohrungen mit Rückzug", "06")),
        (["reib mit o rückzug"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 3.0 <= dia <= 8.05,
         (r"03_Bohrungen\Bohrungen mit Rückzug", "01")),
        (["reib mit o rückzug"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 10.0 <= dia <= 12.05,
         (r"03_Bohrungen\Bohrungen mit Rückzug", "02")),

        # --- Reiben ---
        (["reib ohne o"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 3.0 <= dia <= 8.05,
         (r"03_Bohrungen", "05")),
        (["reib ohne o"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 10.0 <= dia <= 12.05,
         (r"03_Bohrungen", "06")),
        (["reib mit o"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 3.0 <= dia <= 8.05,
         (r"03_Bohrungen", "01")),
        (["reib mit o"],
         lambda ft_lower, ocr_res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 10.0 <= dia <= 12.05,
         (r"03_Bohrungen", "02")),
    ]

    keywords_requiring_exact_search_logic = {"reib mit o", "reib ohne o"}  # ggf. anpassen

    logger.debug(f"--- Beginn Regelprüfung für Feature-Typ: '{feature_type_lower}' ---")

    # Umbenennung des dritten Elements für Klarheit im Loop
    for keywords_in_rule, condition_func, action_provider_or_static_tuple in base_rules:

        keyword_match_successful = False
        # --- Keyword-Matching (Ihre bestehende Logik, ggf. leicht angepasst) ---
        apply_exact_search_for_this_rule = any(
            kw_from_rule in keywords_requiring_exact_search_logic for kw_from_rule in keywords_in_rule)

        if apply_exact_search_for_this_rule:
            for kw in keywords_in_rule:
                # Exakte Suche verwendet Wortgrenzen
                if re.search(r'\b' + re.escape(kw) + r'\b', feature_type_lower, re.IGNORECASE):
                    keyword_match_successful = True
                    logger.debug(
                        f"EXAKTE SUCHE (Regel '{keywords_in_rule}'): Keyword '{kw}' in '{feature_type_lower}' gefunden.")
                    break
            if not keyword_match_successful and keywords_in_rule:  # Fallback, falls \b nicht passt
                for kw in keywords_in_rule:
                    if kw in feature_type_lower:  # Standard 'in' prüft Substring
                        keyword_match_successful = True
                        logger.debug(
                            f"EXAKTE SUCHE FALLBACK (Regel '{keywords_in_rule}'): Keyword '{kw}' in '{feature_type_lower}' gefunden.")
                        break
                if not keyword_match_successful and keywords_in_rule:
                    logger.debug(
                        f"EXAKTE SUCHE (Regel '{keywords_in_rule}'): Keines der Keywords passte exakt in '{feature_type_lower}'.")
        else:  # Standard Substring Suche
            for kw in keywords_in_rule:
                if kw in feature_type_lower:
                    keyword_match_successful = True
                    logger.debug(
                        f"STANDARD SUCHE (Regel '{keywords_in_rule}'): Keyword '{kw}' in '{feature_type_lower}' gefunden.")
                    break
            if not keyword_match_successful and keywords_in_rule:  # Nur loggen wenn Keywords da waren, aber nicht gematcht haben
                logger.debug(
                    f"STANDARD SUCHE (Regel '{keywords_in_rule}'): Keines der Keywords als Substring in '{feature_type_lower}' gefunden.")
        # --- Ende Keyword-Matching ---

        if keyword_match_successful:
            # --- Bedingungsprüfung ---
            # Argumente entsprechend der neuen Signatur übergeben
            if condition_func(feature_type_lower, ocr_all_results, d_float, bbox_breite_float, tiefe_float,
                              bbox_laenge_float, kleinster_radius_float):

                target_tuple_for_action = None
                # Prüfen, ob action_provider_or_static_tuple eine Funktion (Aktions-Lambda) ist
                if callable(action_provider_or_static_tuple):
                    # Ja, also aufrufen, um das (subdir, prefix)-Tupel zu bekommen
                    # Argumente entsprechend der neuen Signatur übergeben
                    target_tuple_for_action = action_provider_or_static_tuple(
                        feature_type_lower, ocr_all_results, d_float,
                        bbox_breite_float, tiefe_float, bbox_laenge_float, kleinster_radius_float
                    )
                    if target_tuple_for_action is None:
                        logger.debug(f"Aktions-Lambda für Regel '{keywords_in_rule}' gab None zurück. Überspringe.")
                        continue  # Nächste Regel prüfen
                else:
                    # Nein, es ist ein statisches Tupel
                    target_tuple_for_action = action_provider_or_static_tuple

                # Versuche nun, das Ergebnis zu entpacken
                try:
                    relative_subdir, desired_prefix_str = target_tuple_for_action
                except (TypeError, ValueError) as e:
                    logger.error(
                        f"Regel '{keywords_in_rule}' (Keywords: {keywords_in_rule}) lieferte ungültiges 'target_tuple_for_action': {target_tuple_for_action}. Fehler: {e}")
                    continue  # Nächste Regel prüfen

                logger.info(f"REGEL-MATCH: Keywords='{keywords_in_rule}'. Bedingung erfüllt. "
                            f"Ziel-Unterordner: '{relative_subdir}', Gewünschter Präfix: '{desired_prefix_str}_'.")

                actual_search_dir = os.path.normpath(os.path.join(material_root_path, relative_subdir))

                if not os.path.isdir(actual_search_dir):
                    logger.warning(
                        f"Zielverzeichnis '{actual_search_dir}' für Regel '{keywords_in_rule}' (basierend auf '{relative_subdir}') nicht gefunden.")
                    continue

                found_matching_files = []
                prefix_to_search = desired_prefix_str + "_"

                logger.debug(
                    f"Suche in '{actual_search_dir}' nach Dateien, die mit '{prefix_to_search}' beginnen und auf '.prc' enden.")

                try:
                    dir_listing = sorted(os.listdir(actual_search_dir))
                except OSError as e:
                    logger.error(f"Fehler beim Lesen des Verzeichnisses '{actual_search_dir}': {e}")
                    continue

                for item_in_dir in dir_listing:
                    if item_in_dir.startswith(prefix_to_search) and item_in_dir.lower().endswith(".prc"):
                        full_path = os.path.join(actual_search_dir, item_in_dir)
                        if os.path.isfile(full_path):
                            found_matching_files.append(full_path)
                            logger.info(f"Datei-Match aufgrund Präfix '{prefix_to_search}': '{full_path}'")

                if found_matching_files:
                    selected_file_path = found_matching_files[0]
                    logger.info(
                        f"FINALE AUSWAHL (erste Datei mit Präfix '{prefix_to_search}'): '{selected_file_path}'.")
                    return selected_file_path
                else:
                    logger.info(
                        f"Keine .prc-Datei mit Präfix '{prefix_to_search}' im Verzeichnis '{actual_search_dir}' gefunden.")

            else:  # condition_func nicht erfüllt
                log_values = (
                    f"Ø(dia):{d_float}, BBoxB(bbox_b):{bbox_breite_float}, Tiefe(tief):{tiefe_float}, "
                    f"BBoxL(bbox_l):{bbox_laenge_float}, KlRad(kl_r):{kleinster_radius_float}"
                )
                logger.debug(
                    f"Bedingung für Keywords '{keywords_in_rule}' (Feature: '{feature_type_lower}') NICHT erfüllt. OCR-Werte: {log_values}")

    logger.warning(
        f"Keine passende Regel mit existierender Datei (basierend auf Präfix-Suche) für Feature='{feature_type_lower}', OCR-Daten='{ocr_all_results}' in '{material_root_path}' gefunden.")
    return None