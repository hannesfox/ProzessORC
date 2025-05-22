# rule_engine.py
"""
Dieses Modul enthält die Logik zur regelbasierten Zuordnung von .prc-Dateien.
Es geht davon aus, dass die OCR-Kriterien zu einem logischen Prozess führen,
der durch einen numerischen Präfix im Dateinamen (XX_) innerhalb eines
spezifischen Unterordners identifiziert wird. Der Rest des Dateinamens kann variieren.

Regel-Struktur:
  [Keywords],
  Lambda-Bedingung,
  (RELATIVER_UNTERORDNER_ZUM_MATERIAL_ROOT, NUMERISCHER_DATEIPRÄFIX_ALS_STRING_OHNE_UNTERSTRICH)
Beispiel für das dritte Element: (r"01_Plan-Aussen-Fase-Tasche", "01")
"""

import os
import logging
import re

# --- Logging Konfiguration ---
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - (%(module)s) - %(message)s')

# --- Regelbasierte Zuordnung für .prc-Dateien ---

def find_prc_path_by_rules(feature_type_lower: str | None, ocr_all_results: dict, material_root_path: str | None) -> str | None:
    if not feature_type_lower or not ocr_all_results or not material_root_path:
        logger.warning(
            f"find_prc_path_by_rules mit unvollständigen Daten: ft='{feature_type_lower}', ocr_results='{ocr_all_results}', root='{material_root_path}'"
        )
        return None

    # --- Werteextraktion aus OCR ---
    d_float_str = ocr_all_results.get("Durchmesser")
    d_float = None
    if d_float_str:
        try: d_float = float(str(d_float_str).replace(",", "."))
        except ValueError: logger.warning(f"Konnte Durchmesser '{d_float_str}' nicht in Float umwandeln.")

    tiefe_str = ocr_all_results.get("Tiefe")
    tiefe_float = None
    if tiefe_str:
        try: tiefe_float = float(str(tiefe_str).replace(",", "."))
        except ValueError: logger.warning(f"Konnte Tiefe '{tiefe_str}' nicht in Float umwandeln.")

    bbox_breite_str = ocr_all_results.get("Begrenzungsbox Breite")
    bbox_breite_float = None
    if bbox_breite_str:
        try: bbox_breite_float = float(str(bbox_breite_str).replace(",", "."))
        except ValueError: logger.warning(f"Konnte Begrenzungsbox Breite '{bbox_breite_str}' nicht in Float umwandeln.")

    bbox_laenge_str = ocr_all_results.get("Begrenzungsbox Länge")
    bbox_laenge_float = None
    if bbox_laenge_str:
        try: bbox_laenge_float = float(str(bbox_laenge_str).replace(",", "."))
        except ValueError: logger.warning(f"Konnte Begrenzungsbox Länge '{bbox_laenge_str}' nicht in Float umwandeln.")

    kleinster_radius_str = ocr_all_results.get("Kleinster Radius")
    kleinster_radius_float = None
    if kleinster_radius_str:
        try: kleinster_radius_float = float(str(kleinster_radius_str).replace(",", "."))
        except ValueError: logger.warning(f"Konnte Kleinster Radius '{kleinster_radius_str}' nicht in Float umwandeln.")

    logger.info(
        f"Suche PRC: Feature='{feature_type_lower}', Ø='{d_float_str}' (num: {d_float}), "
        f"Tiefe='{tiefe_str}' (num: {tiefe_float}), "
        f"BBoxBreite='{bbox_breite_str}' (num: {bbox_breite_float}), BBoxLänge='{bbox_laenge_str}' (num: {bbox_laenge_float}), "
        f"KlRadius='{kleinster_radius_str}' (num: {kleinster_radius_float}), Material-Root='{material_root_path}'"
    )
    
    
    
    # --- Regeldefinitionen ---
    # 
    # 
    #
    # 
    base_rules = [
        
        # --- Nuten ---
        # 
        (["nuten"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: bbox_b is not None and 3.1 <= bbox_b <= 4.0,  (r"07_NUTEN", "01")), # FR03
        (["nuten"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: bbox_b is not None and 4.1 <= bbox_b <= 6.0,  (r"07_NUTEN", "02")),
        (["nuten"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: bbox_b is not None and 6.1 <= bbox_b <= 8.0,  (r"07_NUTEN", "03")),
        (["nuten"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: bbox_b is not None and 8.1 <= bbox_b <= 9.0,  (r"07_NUTEN", "04")),
        (["nuten"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: bbox_b is not None and 9.1 <= bbox_b <= 14.0, (r"07_NUTEN", "05")),
        (["nuten"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: bbox_b is not None and 14.1 <= bbox_b <= 18.0,(r"07_NUTEN", "06")),
        (["nuten"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: bbox_b is not None and 18.1 <= bbox_b <= 22.0,(r"07_NUTEN", "07")), # FR12


        # --- Plan ---
        # Plan 42-62 16 20
        (["plan"],
         lambda res, dia, bbox_b, tief, bbox_l, kl_r:
            tief is not None and 0.0 <= tief <= 40.0 and
            kl_r is not None and 0.0 <= kl_r <= 20.0 and
            bbox_l is not None and 40.1 <= bbox_l <= 2000.0 and
            bbox_b is not None and 60.1 <= bbox_b <= 2000.0,
         (r"01_Plan-Aussen-Fase-Tasche", "01")), 

        # Plan 42-62 16x52 20
        (["plan"], 
         lambda res, dia, bbox_b, tief, bbox_l, kl_r:
            tief is not None and 40.01 <= tief <= 52.0 and
            kl_r is not None and 0.0 <= kl_r <= 20.0 and
            bbox_l is not None and 40.1 <= bbox_l <= 2000.0 and
            bbox_b is not None and 60.1 <= bbox_b <= 2000.0,
         (r"01_Plan-Aussen-Fase-Tasche", "02")),

        # Plan  10er fräser
        (["plan"],
         lambda res, dia, bbox_b, tief, bbox_l, kl_r:
         tief is not None and 0.0 <= tief <= 40.5 and
         kl_r is not None and 0.0 <= kl_r <= 5.0 and
         bbox_l is not None and 0.0 <= bbox_l <= 40.0 and
         bbox_b is not None and 0.0 <= bbox_b <= 60.0,
         (r"01_Plan-Aussen-Fase-Tasche", "06")),

        # Plan  16er fräser
        (["plan"],
         lambda res, dia, bbox_b, tief, bbox_l, kl_r:
         tief is not None and 0.0 <= tief <= 40.5 and
         kl_r is not None and 0.0 <= kl_r <= 10.0 and
         bbox_l is not None and 40.1 <= bbox_l <= 180.0 and
         bbox_b is not None and 0.0 <= bbox_b <= 60.0,
         (r"01_Plan-Aussen-Fase-Tasche", "04")),


        # --- Tasche Profit ---
        (["tasche profit"], lambda res, dia, bbox_b, tief, bbox_l, kl_r:
                tief is not None and 0.0 <= tief <= 18.0 and
                kl_r is not None and 0.0 <= kl_r <= 1.5,
            (r"02_Taschen\Profit", "01")),# FR03

        (["tasche profit"], lambda res, dia, bbox_b, tief, bbox_l, kl_r:
                tief is not None and 0.0 <= tief <= 21.0 and
                kl_r is not None and 1.51 <= kl_r <= 2.0,
            (r"02_Taschen\Profit", "02")),  # FR04

        (["tasche profit"], lambda res, dia, bbox_b, tief, bbox_l, kl_r:
                tief is not None and 0.0 <= tief <= 21.0 and
                kl_r is not None and 2.01 <= kl_r <= 2.5,
             (r"02_Taschen\Profit", "03")),  # FR05

        (["tasche profit"], lambda res, dia, bbox_b, tief, bbox_l, kl_r:
                tief is not None and 0.0 <= tief <= 20.0 and
                kl_r is not None and 2.51 <= kl_r <= 3.0,
             (r"02_Taschen\Profit", "04")),  # FR06

        (["tasche profit"], lambda res, dia, bbox_b, tief, bbox_l, kl_r:
                tief is not None and 0.0 <= tief <= 25.0 and
                kl_r is not None and 3.01 <= kl_r <= 4.0,
             (r"02_Taschen\Profit", "05")),  # FR08

        (["tasche profit"], lambda res, dia, bbox_b, tief, bbox_l, kl_r:
                tief is not None and 0.0 <= tief <= 40.0 and
                kl_r is not None and 4.01 <= kl_r <= 5.0,
             (r"02_Taschen\Profit", "07")),  # FR10

        (["tasche profit"], lambda res, dia, bbox_b, tief, bbox_l, kl_r:
                tief is not None and 0.0 <= tief <= 35.0 and
                kl_r is not None and 5.01 <= kl_r <= 6.0,
             (r"02_Taschen\Profit", "08")),  # FR12

        (["tasche profit"], lambda res, dia, bbox_b, tief, bbox_l, kl_r:
                tief is not None and 0.0 <= tief <= 45.0 and
                kl_r is not None and 6.01 <= kl_r <= 8.0,
             (r"02_Taschen\Profit", "10")),  # FR16

        (["tasche profit"], lambda res, dia, bbox_b, tief, bbox_l, kl_r:
                tief is not None and 0.0 <= tief <= 40.0 and
                kl_r is not None and 4.01 <= kl_r <= 5.0 and
                bbox_l is not None and 40.0 <= bbox_l <= 1000.0 and
                bbox_b is not None and 40.0 <= bbox_b <= 1000.0,
             (r"02_Taschen\Profit", "09")),  # FR16-10


        # --- Passung Fräsen ---
        # 
        (["passung fräsen"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 1.52 <= dia <= 2.5,   (r"06_Passung Fräsen", "01")), #FR 1,5mm
        (["passung fräsen"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 2.51 <= dia <= 3.5,  (r"06_Passung Fräsen", "02")),  #FR 2mm
        (["passung fräsen"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 3.51 <= dia <= 4.5,  (r"06_Passung Fräsen", "03")),  #FR 3mm
        (["passung fräsen"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 4.51 <= dia <= 6.5,  (r"06_Passung Fräsen", "04")),  #FR 4mm
        (["passung fräsen"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 6.51 <= dia <= 8.5,  (r"06_Passung Fräsen", "05")),  #FR 5mm
        (["passung fräsen"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 8.51 <= dia <= 10.5, (r"06_Passung Fräsen", "06")),  #FR 6mm
        (["passung fräsen"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 10.51 <= dia <= 14.5,(r"06_Passung Fräsen", "07")),  #FR 8mm
        (["passung fräsen"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 14.51 <= dia <= 18.5,(r"06_Passung Fräsen", "08")),  #FR 10mm
        (["passung fräsen"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 12.51 <= dia <= 23.5,(r"06_Passung Fräsen", "09")),  #FR 12mm
        
        (["passung fräsen"], # Für 16, spezifische Tiefen
         lambda res, dia, bbox_b, tief, bbox_l, kl_r:
            dia is not None and 23.51 <= dia <= 31.0 and
            tief is not None and 0.0 <= tief <= 40.0, # zuerst
         (r"06_Passung Fräsen", "10")), # Präfix für 16er
        
        (["passung fräsen"],
         lambda res, dia, bbox_b, tief, bbox_l, kl_r:
            dia is not None and 31.01 <= dia <= 39.0 and
            tief is not None and 0.0 <= tief <= 40.0,
         (r"06_Passung Fräsen", "11")), # Präfix für 16x52 20SL
        
        (["passung fräsen"],
         lambda res, dia, bbox_b, tief, bbox_l, kl_r:
            dia is not None and 31.01 <= dia <= 39.0 and
            tief is not None and 40.01 <= tief <= 52.0,
         (r"06_Passung Fräsen", "13")), #
        

        # --- Bohrung KM (mit Senkung) ---
        (["bohrung km"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 2.5 <= dia <= 3.7,   (r"05_DGB\nur Senkung", "01")),
        (["bohrung km"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 4.0 <= dia <= 5.0,   (r"05_DGB\nur Senkung", "02")),
        (["bohrung km"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 5.1 <= dia <= 6.2,   (r"05_DGB\nur Senkung", "03")),
        (["bohrung km"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 6.3 <= dia <= 8.7,   (r"05_DGB\nur Senkung", "04")),
        (["bohrung km"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 8.9 <= dia <= 10.0,  (r"05_DGB\nur Senkung", "05")),
        (["bohrung km"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 10.1 <= dia <= 10.8, (r"05_DGB\nur Senkung", "06")),
        (["bohrung km"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 10.9 <= dia <= 12.0, (r"05_DGB\nur Senkung", "07")),
        (["bohrung km"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 12.1 <= dia <= 14.0, (r"05_DGB\nur Senkung", "08")),
        (["bohrung km"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 16.1 <= dia <= 18.0, (r"05_DGB\nur Senkung", "09")),


        
        # --- Trennen D80x3 ---
        (["trennen"],
         lambda res, dia, bbox_b, tief, bbox_l, kl_r: True,
         (r"13_Trennen", "01")
        ),


        # --- Bohrung Allgemein ---
        (["bohrung"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 2.0 <= dia < 6.97,   (r"05_DGB", "01")), #bis 7mm
        (["bohrung"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 7.02 <= dia < 9.29,   (r"05_DGB", "01")), #ab  7mm
        (["bohrung"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 6.99 <= dia < 7.01,   (r"05_DGB", "03")), #nur 7mm
        (["bohrung"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 9.3 <= dia <= 17.5, (r"05_DGB", "02")),   # 9,3-17,5mm
        (["bohrung"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 17.99 <= dia < 18.01, (r"05_DGB", "04")),  # WPB 18mm
        (["bohrung"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 19.99 <= dia < 20.01, (r"05_DGB", "05")),  # WPB 20mm
        (["bohrung"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 21.99 <= dia < 22.01, (r"05_DGB", "06")),  # WPB 22mm
        (["bohrung"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 25.99 <= dia < 26.01, (r"05_DGB", "07")),  # WPB 26mm

        # --- Gewinde ---
        (["gewinde m", "gewinde"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 2.0 <= dia <= 7.0,  (r"03_Bohrungen", "03")), # M3-M8
        (["gewinde m", "gewinde"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 7.01 < dia <= 12.5, (r"03_Bohrungen", "04")), # M10-M12


        # --- Reiben ---
        (["reib ohne o", "reiben ohne o"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 3.0 <= dia <= 8.05,   (r"03_Bohrungen", "05")), # reib ohne 4-8
        (["reib ohne o", "reiben ohne o"], lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 10.0 <= dia <= 12.05, (r"03_Bohrungen", "06")), # reib ohne 10-12
        (["reib mit o", "reiben mit o"],   lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 3.0 <= dia <= 8.05,   (r"03_Bohrungen", "01")), # reib mit 4-8
        (["reib mit o", "reiben mit o"],   lambda res, dia, bbox_b, tief, bbox_l, kl_r: dia is not None and 10.0 <= dia <= 12.05, (r"03_Bohrungen", "02")), # reib mit 10-12
    ]

    keywords_requiring_exact_search_logic = {"reib mit o", "reiben mit o", "reib ohne o", "reiben ohne o"}

    logger.debug(f"--- Beginn Regelprüfung für Feature-Typ: '{feature_type_lower}' ---")

    for keywords_in_rule, condition_func, target_location_info in base_rules:
        relative_subdir, desired_prefix_str = target_location_info

        keyword_match_successful = False
        apply_exact_search_for_this_rule = any(kw_from_rule in keywords_requiring_exact_search_logic for kw_from_rule in keywords_in_rule)

        # --- Keyword-Matching ---
        if apply_exact_search_for_this_rule:
            for kw in keywords_in_rule:
                if re.search(r'\b' + re.escape(kw), feature_type_lower):
                    keyword_match_successful = True
                    logger.debug(f"EXAKTE SUCHE (Regel '{keywords_in_rule}'): Keyword '{kw}' in '{feature_type_lower}' gefunden.")
                    break
            if not keyword_match_successful and keywords_in_rule:
                 logger.debug(f"EXAKTE SUCHE (Regel '{keywords_in_rule}'): Keines der Keywords passte exakt in '{feature_type_lower}'.")
        else:
            for kw in keywords_in_rule:
                if kw in feature_type_lower:
                    keyword_match_successful = True
                    logger.debug(f"STANDARD SUCHE (Regel '{keywords_in_rule}'): Keyword '{kw}' in '{feature_type_lower}' gefunden.")
                    break
            if not keyword_match_successful and keywords_in_rule:
                logger.debug(f"STANDARD SUCHE (Regel '{keywords_in_rule}'): Keines der Keywords als Substring in '{feature_type_lower}' gefunden.")

        if keyword_match_successful:
            # --- Bedingungsprüfung ---
            if condition_func(ocr_all_results, d_float, bbox_breite_float, tiefe_float, bbox_laenge_float, kleinster_radius_float):
                logger.info(f"REGEL-MATCH: Keywords='{keywords_in_rule}'. Bedingung erfüllt. "
                            f"Ziel-Unterordner: '{relative_subdir}', Gewünschter Präfix: '{desired_prefix_str}_'.")

                actual_search_dir = os.path.normpath(os.path.join(material_root_path, relative_subdir))

                if not os.path.isdir(actual_search_dir):
                    logger.warning(f"Zielverzeichnis '{actual_search_dir}' für Regel '{keywords_in_rule}' (basierend auf '{relative_subdir}') nicht gefunden.")
                    continue # Nächste Regel prüfen

                found_matching_files = []
                prefix_to_search = desired_prefix_str + "_" # z.B. "01_"

                logger.debug(f"Suche in '{actual_search_dir}' nach Dateien, die mit '{prefix_to_search}' beginnen und auf '.prc' enden.")

                try:
                    # Sortiere das Directory-Listing,
                    # falls mehrere Dateien mit dem gleichen Präfix existieren.
                    dir_listing = sorted(os.listdir(actual_search_dir))
                except OSError as e:
                    logger.error(f"Fehler beim Lesen des Verzeichnisses '{actual_search_dir}': {e}")
                    continue # Nächste Regel prüfen

                for item_in_dir in dir_listing:
                    # Stelle sicher, dass es eine Datei ist
                    # und die Namensbedingungen erfüllt
                    if item_in_dir.startswith(prefix_to_search) and item_in_dir.lower().endswith(".prc"):
                        full_path = os.path.join(actual_search_dir, item_in_dir)
                        if os.path.isfile(full_path): # Zusätzliche Prüfung, ob es wirklich eine Datei ist
                            found_matching_files.append(full_path)
                            logger.info(f"Datei-Match aufgrund Präfix '{prefix_to_search}': '{full_path}'")
                
                if found_matching_files:
                    # Nimm die erste gefundene Datei.
                    # Wenn der Präfix den Prozess eindeutig identifizieren soll, ist dies die richtige Datei.
                    selected_file_path = found_matching_files[0] 
                    logger.info(f"FINALE AUSWAHL (erste Datei mit Präfix '{prefix_to_search}'): '{selected_file_path}'.")
                    return selected_file_path
                else:
                    logger.info(f"Keine .prc-Datei mit Präfix '{prefix_to_search}' im Verzeichnis '{actual_search_dir}' gefunden.")
            
            else: # condition_func nicht erfüllt
                log_values = (
                    f"Ø(dia):{d_float}, BBoxB(bbox_b):{bbox_breite_float}, Tiefe(tief):{tiefe_float}, "
                    f"BBoxL(bbox_l):{bbox_laenge_float}, KlRad(kl_r):{kleinster_radius_float}"
                )
                logger.debug(f"Bedingung für Keywords '{keywords_in_rule}' NICHT erfüllt. OCR-Werte: {log_values}")

    logger.warning(f"Keine passende Regel mit existierender Datei (basierend auf Präfix-Suche) für Feature='{feature_type_lower}', OCR-Daten='{ocr_all_results}' in '{material_root_path}' gefunden.")
    return None
