# main.py
"""
Hauptanwendung für den Material Selector mit Flet.
Nutzt ocr_recognition.py für die OCR-Funktionalität und rule_engine.py für die Regelauswahl.
"""
import flet as ft
import os
import pyperclip
import threading
import time
import logging

# Importiere
import ocr_recognition
import rule_engine

# Importiere pytesseract
from pytesseract import TesseractNotFoundError

# --- Logging Konfiguration ---
logging.basicConfig(level=logging.INFO,  # Hauptlevel
                    format='%(asctime)s - %(levelname)s - (%(module)s) - %(message)s')

# --- Globale Variablen ---
current_material_root_path: str | None = None
highlighted_tile: ft.ListTile | None = None
snackbar_queue = []
snackbar_lock = threading.Lock()


# --- Flet App  ---

def main(page: ft.Page):
    """Die Hauptfunktion, die die Flet-Anwendung initialisiert und ausführt."""
    page.title = "ProzessKI-App "
    if page.platform in [ft.PagePlatform.WINDOWS, ft.PagePlatform.LINUX, ft.PagePlatform.MACOS]:
        page.window.width = 850
        page.window.height = 1050
        #page.window.center()
        page.window.top = 197  #pos für meinen rechner sonst 0
        page.window.left = 3435 #pos für meinen rechner sonst 0
        page.theme_mode = ft.ThemeMode.DARK
    #page.theme_mode = ft.ThemeMode.LIGHT

    # ordner für Materialien
    root_paths = [
        r"K:\Esprit\Prozesse\+1,7131( 1.1730, 1.8928, 1.2162 )",
        r"K:\Esprit\Prozesse\+1.2311(1.7225, 1.2344, 1.8519)",
        r"K:\Esprit\Prozesse\+1.2316 ( 1.2738, 1.2083,1.2842 )",
        r"K:\Esprit\Prozesse\+1.2379", r"K:\Esprit\Prozesse\+1.3343",
        r"K:\Esprit\Prozesse\+1.4112 Niro", r"K:\Esprit\Prozesse\+3.3547 ALU",
        r"K:\Esprit\Prozesse\+Kunststoff", r"K:\Esprit\Prozesse\+3D",
    ]
    path_stack: list[str] = []

    # --- Snackbar Handling ---
    def _process_snackbar_queue(page_ref: ft.Page):
        """Verarbeitet eine Snackbar aus der Queue."""
        with snackbar_lock:
            if not snackbar_queue: return
            message, error, duration = snackbar_queue[0]
            snackbar = ft.SnackBar(
                content=ft.Text(message, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.RED_ACCENT_700 if error else ft.Colors.GREEN_ACCENT_700),
                open=False,
            )

            def show_and_remove():
                try:
                    page_ref.overlay.append(snackbar)
                    page_ref.update()
                    time.sleep(0.1)
                    snackbar.open = True
                    page_ref.update()
                    time.sleep(duration / 1000)
                    snackbar.open = False
                    page_ref.update()
                    time.sleep(0.5)
                except Exception as e_show:
                    logging.error(f"Fehler beim Anzeigen/Schließen der Snackbar: {e_show}", exc_info=True)
                finally:
                    try:
                        if page_ref.overlay and snackbar in page_ref.overlay:
                            page_ref.overlay.remove(snackbar)
                            page_ref.update()
                    except Exception as e_remove:
                        logging.error(f"Fehler beim Entfernen der Snackbar: {e_remove}", exc_info=True)
                    with snackbar_lock:
                        if snackbar_queue and (message, error, duration) == snackbar_queue[0]:
                            snackbar_queue.pop(0)
                    if snackbar_queue:
                        threading.Thread(target=_process_snackbar_queue, args=(page_ref,), daemon=True).start()

            threading.Thread(target=show_and_remove, daemon=True).start()

    def _show_snackbar_message(page_ref: ft.Page, message: str, error: bool = False, duration: int = 3000):
        """Fügt eine Snackbar zur Queue hinzu."""
        with snackbar_lock:
            snackbar_queue.append((message, error, duration))
            if len(snackbar_queue) == 1:
                threading.Thread(target=_process_snackbar_queue, args=(page_ref,), daemon=True).start()

    # --- UI Elemente  ---
    def reset_highlights():
        """Entfernt die Hervorhebung."""
        global highlighted_tile
        if highlighted_tile:
            highlighted_tile.bgcolor = None
            logging.debug(f"Hervorhebung entfernt von Tile mit Key: {highlighted_tile.key}")
            highlighted_tile = None
            # Caller handles page.update()

    # MODIFIED: Header definition for potential tooltip
    header = ft.Text(
        "📁 Wähle einen Material-Ordner",
        size=20,
        weight="bold",
        tooltip="Aktuell ausgewählter Pfad"  # Initialer Tooltip
    )
    listview = ft.ListView(expand=True, spacing=0, padding=5)
    back_button = ft.ElevatedButton("⮜ Zurück", tooltip="Zum übergeordneten Ordner", disabled=True,
                                    on_click=lambda e: go_back())
    ocr_button = ft.ElevatedButton(
        "📷 Scan Esprit Feature",
        icon=ft.Icons.CAMERA_ALT_OUTLINED,
        tooltip="Scannt Esprit Eigenschaften, versucht passenden Prozess zu finden...",
        disabled=True,  # Der Button ist initial oft deaktiviert
        on_click=lambda e: start_ocr_process_thread(),
        # HIER DIE ÄNDERUNG FÜR DIE SCHRIFT-/ICONFARBE:
        style=ft.ButtonStyle(
            color=ft.Colors.CYAN_ACCENT_700  # Setzt die Vordergrundfarbe (Text und Icon)
        )
    )

    def close_dialog(dlg: ft.AlertDialog):
        """Schließt den übergebenen AlertDialog."""
        dlg.open = False
        page.update()

    # --- Kernlogik:  ---
    def load_items(paths_to_load: list[str], highlight_path: str | None = None):
        """Lädt Ordner und .prc-Dateien in die ListView und hebt ggf. hervor."""
        reset_highlights()
        listview.controls.clear()
        dirs, prcs = [], []
        processed_paths = set()

        for p in paths_to_load:
            try:
                if not os.path.exists(p):
                    logging.warning(f"Pfad existiert nicht, wird übersprungen: {p}")
                    continue
                norm_p = os.path.normpath(os.path.normcase(p))
                if norm_p in processed_paths:
                    logging.debug(f"Doppelter Pfad übersprungen: {p}")
                    continue
                processed_paths.add(norm_p)

                if os.path.isdir(p):
                    if os.access(p, os.R_OK):
                        dirs.append(p)
                    else:
                        logging.warning(f"Keine Leseberechtigung für Ordner: {p}")
                elif p.lower().endswith(".prc") and os.path.isfile(p):
                    if os.access(p, os.R_OK):
                        prcs.append(p)
                    else:
                        logging.warning(f"Keine Leseberechtigung für Datei: {p}")

            except OSError as e:
                logging.warning(f"OS-Fehler beim Zugriff auf Pfad {p}: {e}")
            except Exception as e:
                logging.error(f"Unerwarteter Fehler beim Verarbeiten von Pfad {p}: {e}", exc_info=True)

        dirs.sort(key=lambda x: os.path.basename(x).lower())
        prcs.sort(key=lambda x: os.path.basename(x).lower())

        for p in dirs:
            listview.controls.append(ft.ListTile(
                title=ft.Text(os.path.basename(p)),
                leading=ft.Icon(ft.Icons.FOLDER, color=ft.Colors.AMBER_700),
                on_click=lambda e, folder_path=p: open_folder(folder_path),
                hover_color=ft.Colors.with_opacity(0.1, ft.Colors.BLUE_GREY_50),
                key=p
            ))
        for p in prcs:
            listview.controls.append(ft.ListTile(
                title=ft.Text(os.path.basename(p)),
                leading=ft.Icon(ft.Icons.DESCRIPTION, color=ft.Colors.BLUE_GREY_300),
                on_click=lambda e, file_path=p: copy_prc_path_and_show_dialog(file_path),
                hover_color=ft.Colors.with_opacity(0.1, ft.Colors.BLUE_GREY_50),
                key=p,
                data=p
            ))
        logging.info(
            f"{len(dirs)} Ordner und {len(prcs)} .prc-Dateien geladen für Pfad: {path_stack[-1] if path_stack else 'Root Auswahl'}")

        highlight_applied = False
        if highlight_path:
            logging.info(f"Versuche, Pfad nach Laden hervorzuheben: {highlight_path}")
            global highlighted_tile
            norm_highlight_path = os.path.normpath(os.path.normcase(highlight_path))
            found_tile = None
            for control in listview.controls:
                if isinstance(control, ft.ListTile) and hasattr(control, 'data') and control.data:
                    control_data_norm = os.path.normpath(os.path.normcase(str(control.data)))
                    if control_data_norm == norm_highlight_path:
                        #control.bgcolor = ft.Colors.GREEN_ACCENT_700
                        control.bgcolor = ft.Colors.CYAN_ACCENT_700
                        highlighted_tile = control
                        found_tile = control
                        highlight_applied = True
                        logging.debug(
                            f"Tile für '{os.path.basename(highlight_path)}' nach Laden gefunden und hervorgehoben.")
                        break
            if not highlight_applied:
                logging.warning(
                    f"Pfad '{highlight_path}' sollte hervorgehoben werden, aber Tile wurde nach Laden nicht gefunden.")

        page.update()

        if highlight_applied and found_tile:
            time.sleep(0.1)
            try:
                logging.debug(f"Scrolle zu hervorgehobenem Tile: {highlight_path}")
                listview.scroll_to(key=highlight_path, duration=500, curve=ft.AnimationCurve.EASE_IN_OUT)
            except Exception as scroll_err:
                logging.warning(f"Fehler beim Scrollen zu Key '{highlight_path}' nach Laden: {scroll_err}")

    def open_folder(folder: str, highlight_path: str | None = None):
        """Wechselt in den Ordner und lädt Inhalt, hebt ggf. hervor."""
        global current_material_root_path
        nonlocal path_stack, header, back_button, ocr_button
        logging.info(f"Öffne Ordner: {folder}" + (
            f" (versuche '{os.path.basename(highlight_path)}' hervorzuheben)" if highlight_path else ""))

        norm_folder = os.path.normpath(os.path.normcase(folder))
        last_stack_item = os.path.normpath(os.path.normcase(path_stack[-1])) if path_stack else None

        if last_stack_item != norm_folder:
            path_stack.append(folder)
            logging.debug(f"Ordner zur Pfad-Stack hinzugefügt: {folder}. Stack-Tiefe: {len(path_stack)}")

        # MODIFIED: Show full path in header
        current_display_path = path_stack[-1]  # folder ist dasselbe wie path_stack[-1] hier
        header.value = f"📁 {current_display_path}"
        header.tooltip = current_display_path

        if len(path_stack) == 1:
            current_material_root_path = folder
            back_button.disabled = True
            ocr_button.disabled = False
        else:
            back_button.disabled = False
            ocr_button.disabled = False

        try:
            if not os.access(folder, os.R_OK):
                raise PermissionError(f"Keine Leseberechtigung für Ordner: {folder}")
            entries = [os.path.join(folder, n) for n in sorted(os.listdir(folder), key=str.lower)]
            load_items(entries, highlight_path=highlight_path)

        except (FileNotFoundError, PermissionError) as e:
            logging.error(f"Fehler beim Öffnen oder Lesen von Ordner '{os.path.basename(folder)}': {e}")
            _show_snackbar_message(page, f"Fehler: {e}", error=True, duration=4000)
            if not highlight_path: go_back()  # Nur zurückgehen, wenn nicht versucht wurde zu highlighten
        except Exception as e:
            logging.error(f"Unerwarteter Fehler beim Öffnen von Ordner '{os.path.basename(folder)}': {e}",
                          exc_info=True)
            _show_snackbar_message(page, f"Unerwarteter Fehler: {e}", error=True, duration=4000)
            if not highlight_path: go_back()

    def copy_prc_path_and_show_dialog(file_path: str):
        logging.info(f"Attempting to copy path: {file_path}")
        global highlighted_tile
        reset_highlights()
        logging.debug("Highlights reset.")

        try:
            logging.debug(f"Calling pyperclip.copy for: {file_path}")
            pyperclip.copy(file_path)
            logging.info(f"Successfully called pyperclip.copy for: {file_path}")
            filename = os.path.basename(file_path)
            logging.debug(f"Basename: {filename}")

            _show_snackbar_message(page, f"✅ Pfad kopiert: {filename}", duration=2500)
            logging.debug("Snackbar message added to queue.")

            # --- Hervorhebung ---
            found_tile = None
            norm_file_path = os.path.normpath(os.path.normcase(file_path))
            logging.debug(f"Searching for tile with normalized path: {norm_file_path}")
            for control in listview.controls:
                if isinstance(control, ft.ListTile) and hasattr(control, 'data') and control.data:
                    control_data_norm = os.path.normpath(os.path.normcase(str(control.data)))
                    if control_data_norm == norm_file_path:
                        logging.debug(f"Found matching tile for {filename}. Applying highlight.")
                        control.bgcolor = ft.Colors.DEEP_ORANGE_ACCENT_700
                        highlighted_tile = control
                        found_tile = control
                        break
            if not found_tile:
                logging.warning(
                    f"Tile for {filename} (path: {file_path}) not found in current listview controls for highlighting.")
            else:
                logging.debug(f"Tile for {filename} highlighted.")

            # --- Dialog ---
            try:
                path_parts = file_path.split(os.sep)
                display_path = f"...{os.sep}{path_parts[-2]}{os.sep}{path_parts[-1]}" if len(
                    path_parts) >= 2 else filename
            except Exception:
                logging.warning("Could not create short display path.", exc_info=True)
                display_path = filename
            logging.debug(f"Display path for dialog: {display_path}")

            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("Pfad kopiert"),
                content=ft.Text(display_path, max_lines=3, overflow=ft.TextOverflow.ELLIPSIS),
                actions=[ft.TextButton("OK", on_click=lambda e: close_dialog(dlg))],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.dialog = dlg
            dlg.open = True
            logging.debug("Dialog set and opened.")
            page.update()
            logging.debug("Page update requested after dialog.")

        except pyperclip.PyperclipException as e:
            logging.error(f"PyperclipException occurred for path {file_path}: {e}", exc_info=True)
            _show_snackbar_message(page, "❌ Fehler: Zwischenablage nicht verfügbar.", error=True, duration=4000)
            page.update()
        except Exception as e:
            logging.error(f"Unexpected Exception in copy_prc_path_and_show_dialog for path {file_path}: {e}",
                          exc_info=True)
            _show_snackbar_message(page, f"❌ Unerwarteter Fehler: {e}", error=True, duration=4000)
            page.update()
        logging.debug(f"Finished copy_prc_path_and_show_dialog for: {file_path}")

    def go_back():
        """Navigiert eine Ebene im Pfad-Stack zurück."""
        global current_material_root_path
        nonlocal path_stack, header, back_button, ocr_button

        if not path_stack:
            logging.warning("go_back aufgerufen, aber Pfad-Stack ist leer.")
            return

        current_level = path_stack[-1]
        logging.info(f"Zurück-Navigation von: {current_level}")
        path_stack.pop()

        if path_stack:
            parent_folder = path_stack[-1]
            logging.info(f"Gehe zurück zu: {parent_folder}")

            # MODIFIED: Show full path in header
            header.value = f"📁 {parent_folder}"
            header.tooltip = parent_folder

            if len(path_stack) == 1:  # Zurück zum Root-Materialordner
                back_button.disabled = True
                ocr_button.disabled = False  # OCR ist im Root-Materialordner möglich
                current_material_root_path = parent_folder  # Dies ist jetzt der Root-Pfad
            else:  # Zurück zu einem Unterordner
                back_button.disabled = False
                ocr_button.disabled = False  # OCR auch in Unterordnern möglich

            try:
                if not os.access(parent_folder, os.R_OK):
                    raise PermissionError(f"Keine Leseberechtigung für zurücknavigierten Ordner: {parent_folder}")
                entries = [os.path.join(parent_folder, n) for n in sorted(os.listdir(parent_folder), key=str.lower)]
                load_items(entries)
            except Exception as e:
                logging.error(f"Fehler beim Laden der Elemente nach 'Zurück' zu '{parent_folder}': {e}", exc_info=True)
                _show_snackbar_message(page, f"Fehler beim Zurückgehen: {e}", error=True)
                # Im Fehlerfall zur Root-Auswahl zurücksetzen
                path_stack.clear()
                current_material_root_path = None
                header.value = "📁 Wähle einen Material-Ordner"
                header.tooltip = "Wähle einen Material-Wurzelordner aus dem Menü."
                back_button.disabled = True
                ocr_button.disabled = True
                listview.controls.clear()
                reset_highlights()
                page.update()
        else:  # path_stack ist jetzt leer, zurück zur initialen Auswahl
            logging.info("Zurück zur Material-Root-Auswahl.")
            current_material_root_path = None
            header.value = "📁 Wähle einen Material-Ordner"
            header.tooltip = "Wähle einen Material-Wurzelordner aus dem Menü."
            back_button.disabled = True
            ocr_button.disabled = True
            listview.controls.clear()
            reset_highlights()
            page.update()

    # --- Drawer und AppBar ---
    drawer_destinations = []
    for p in root_paths:
        label = os.path.basename(p) if p else "Ungültiger Pfad"
        icon = ft.Icons.FOLDER_SPECIAL_OUTLINED if p else ft.Icons.ERROR_OUTLINE
        drawer_destinations.append(ft.NavigationDrawerDestination(icon=icon, label=label))

    drawer = ft.NavigationDrawer(
        controls=[
            ft.Container(height=12),
            ft.Text("Materialien", weight="bold", style=ft.TextThemeStyle.TITLE_MEDIUM),
            ft.Divider(thickness=1),
            *drawer_destinations
        ],
        on_change=lambda e: select_root(e.control.selected_index) if e.control.selected_index is not None else None
    )

    page.appbar = ft.AppBar(
        leading=ft.IconButton(
            icon=ft.Icons.MENU,
            tooltip="Material-Ordner Auswahl öffnen",
            on_click=lambda e: toggle_drawer()
        ),
        title=ft.Text("Material Selector")
    )
    page.drawer = drawer

    def toggle_drawer():
        """Öffnet oder schließt den Navigation Drawer."""
        page.drawer.open = not page.drawer.open
        page.update()

    def select_root(index: int):
        """Wählt einen Material-Wurzelordner aus der Drawer-Liste aus."""
        global current_material_root_path
        nonlocal path_stack, header, back_button, ocr_button

        if not (0 <= index < len(root_paths)):
            logging.error(f"Ungültiger Index {index} für Root-Auswahl erhalten.")
            return

        page.drawer.open = False
        selected_folder = root_paths[index]

        if not selected_folder or not os.path.isdir(selected_folder):
            logging.error(f"Ausgewählter Root-Pfad ist ungültig oder kein Ordner: {selected_folder}")
            _show_snackbar_message(page, f"❌ Fehler: Ungültiger Ordnerpfad ausgewählt.", error=True, duration=4000)
            page.update()
            return

        logging.info(f"Material-Root ausgewählt: {selected_folder}")
        current_material_root_path = selected_folder

        # MODIFIED: Show full path in header
        header.value = f"📁 {selected_folder}"
        header.tooltip = selected_folder

        back_button.disabled = True
        ocr_button.disabled = False  # OCR Button aktivieren, da ein Root-Pfad gesetzt ist
        path_stack = [selected_folder]
        reset_highlights()

        try:
            if not os.access(selected_folder, os.R_OK):
                raise PermissionError(f"Keine Leseberechtigung für Root-Ordner: {selected_folder}")
            entries = [os.path.join(selected_folder, n) for n in sorted(os.listdir(selected_folder), key=str.lower)]
            load_items(entries)

        except (FileNotFoundError, PermissionError) as e:
            logging.error(f"Fehler beim Laden des Root-Ordners '{os.path.basename(selected_folder)}': {e}")
            _show_snackbar_message(page, f"Fehler beim Laden: {e}", error=True, duration=4000)
            current_material_root_path = None
            header.value = "📁 Wähle einen Material-Ordner"
            header.tooltip = "Fehler beim Laden. Bitte einen anderen Ordner wählen."
            ocr_button.disabled = True  # OCR Button deaktivieren bei Fehler
            listview.controls.clear()
            path_stack = []
            page.update()
        except Exception as e:
            logging.error(f"Unerwarteter Fehler beim Laden des Root-Ordners '{os.path.basename(selected_folder)}': {e}",
                          exc_info=True)
            _show_snackbar_message(page, f"Unerwarteter Fehler: {e}", error=True, duration=4000)
            current_material_root_path = None
            header.value = "📁 Wähle einen Material-Ordner"
            header.tooltip = "Unerwarteter Fehler. Bitte einen anderen Ordner wählen."
            ocr_button.disabled = True  # OCR Button deaktivieren bei Fehler
            listview.controls.clear()
            path_stack = []
            page.update()

    # --- OCR Prozess Integration ---
    def run_ocr_process(page_ref: ft.Page):
        """Führt OCR im Hintergrund aus und aktualisiert die UI direkt."""
        global current_material_root_path, highlighted_tile
        nonlocal path_stack  # path_stack wird für Navigation benötigt

        ocr_button.text = "Scanne..."
        ocr_button.icon = ft.Icons.HOURGLASS_TOP_ROUNDED
        ocr_button.disabled = True
        page_ref.update()

        if not current_material_root_path:
            logging.warning("OCR-Prozess gestartet, aber kein Material-Ordner ausgewählt.")
            _show_snackbar_message(page_ref, "Fehler: Kein Material-Ordner ausgewählt.", error=True)
            ocr_button.text = "📷 Scan & Select"
            ocr_button.icon = ft.Icons.CAMERA_ALT_OUTLINED
            # ocr_button.disabled bleibt True, wenn kein Root-Pfad gesetzt ist
            page_ref.update()
            return

        target_prc_path_local = None
        error_message_local = None
        ocr_results_local = {}  # Initialisiere als leeres Dict

        try:
            logging.info(f"Starte OCR für Region: {ocr_recognition.SCREEN_REGION}")
            cv_img = ocr_recognition.capture_to_cv2(ocr_recognition.SCREEN_REGION)
            gray_img = ocr_recognition.preprocess(cv_img)
            ocr_results_local, full_text = ocr_recognition.ocr_line_parse(gray_img)

            found_feature_type_str = ocr_results_local.get("Feature-Typ")

            if found_feature_type_str and current_material_root_path:
                feature_type_lower_cleaned = found_feature_type_str.lower().strip()
                logging.info(
                    f"OCR fand Feature-Typ: '{found_feature_type_str}' (verwendet als: '{feature_type_lower_cleaned}'). OCR-Gesamtergebnis: {ocr_results_local}")

                target_prc_path_local = rule_engine.find_prc_path_by_rules(
                    feature_type_lower_cleaned, ocr_results_local, current_material_root_path
                    # Übergebe alle OCR-Ergebnisse
                )
                if not target_prc_path_local:
                    dia_val = ocr_results_local.get('Durchmesser', 'N/A')
                    bbox_w_val = ocr_results_local.get('Begrenzungsbox Breite', 'N/A')
                    error_message_local = f"ℹ️ Keine Regel/Datei für '{found_feature_type_str}' (Ø:{dia_val}, BBoxB:{bbox_w_val}) gefunden."
            elif not found_feature_type_str:
                error_message_local = "ℹ️ Kein 'Feature-Typ'-Feld im Scan gefunden. Regeln können nicht angewendet werden."
                logging.warning(f"OCR-Ergebnis ohne Feature-Typ: {ocr_results_local}")
            else:
                error_message_local = "ℹ️ Interner Fehler: Material-Pfad fehlt für Regelsuche."
                logging.error(f"Material-Root-Path ist None in run_ocr_process, obwohl zuvor geprüft.")

        except TesseractNotFoundError:
            error_message_local = "❌ Fehler: Tesseract OCR nicht gefunden. Bitte Installation prüfen."
            logging.error("TesseractNotFoundError im OCR-Thread.")
        except RuntimeError as e:
            error_message_local = f"❌ Fehler bei Screenshot/OCR: {e}"
            logging.exception("RuntimeError während OCR-Prozess im Thread.")
        except Exception as e:
            error_message_local = f"❌ Unerwarteter Fehler im OCR-Prozess: {e}"
            logging.exception("Unerwarteter Fehler im OCR-Thread.")

        logging.debug(f"Finalisiere UI nach OCR: Path='{target_prc_path_local}', Error='{error_message_local}'")

        if target_prc_path_local:
            try:
                current_dir = os.path.normpath(path_stack[-1]) if path_stack else None
                target_dir = os.path.normpath(os.path.dirname(target_prc_path_local)) if target_prc_path_local else None

                pyperclip.copy(target_prc_path_local)
                filename = os.path.basename(target_prc_path_local)

                # Nachricht anpassen
                display_feature = ocr_results_local.get("Feature-Typ", "Unbekanntes Feature")
                display_value = ""
                if "nuten" in display_feature.lower():
                    display_value = f"(BBoxB: {ocr_results_local.get('Begrenzungsbox Breite', 'N/A')})"
                else:
                    display_value = f"(Ø: {ocr_results_local.get('Durchmesser', 'N/A')})"

                snackbar_msg = f"✅ Pfad für '{display_feature}' {display_value} kopiert: {filename}"
                _show_snackbar_message(page_ref, snackbar_msg, duration=4000)
                logging.info(f"PRC-Pfad '{target_prc_path_local}' in Zwischenablage kopiert.")

                if current_dir and target_dir and target_dir != current_dir:
                    logging.info(
                        f"Navigation erforderlich: Von '{current_dir}' zu '{target_dir}' für Datei '{filename}'")
                    # Hier rufen wir open_folder auf, das den Header automatisch korrekt setzt
                    open_folder(target_dir, highlight_path=target_prc_path_local)
                elif current_dir and target_dir == current_dir:
                    logging.info(f"Keine Navigation erforderlich, versuche direktes Hervorheben von '{filename}'.")
                    norm_target_path = os.path.normpath(os.path.normcase(target_prc_path_local))
                    found_tile_direct = None
                    reset_highlights()

                    for control in listview.controls:
                        if isinstance(control, ft.ListTile) and hasattr(control, 'data') and control.data:
                            control_data_norm = os.path.normpath(os.path.normcase(str(control.data)))
                            if control_data_norm == norm_target_path:
                                #control.bgcolor = ft.Colors.GREEN_ACCENT_700
                                control.bgcolor = ft.Colors.CYAN_ACCENT_700
                                highlighted_tile = control
                                found_tile_direct = control
                                logging.debug(f"Tile für '{filename}' direkt gefunden und hervorgehoben.")
                                break
                    page_ref.update()

                    if found_tile_direct:
                        time.sleep(0.1)
                        try:
                            logging.debug(f"Scrolle zu direkt hervorgehobenem Tile: {target_prc_path_local}")
                            listview.scroll_to(key=target_prc_path_local, duration=500,
                                               curve=ft.AnimationCurve.EASE_IN_OUT)
                        except Exception as scroll_err:
                            logging.warning(
                                f"Fehler beim Scrollen zu Key '{target_prc_path_local}' (direkt): {scroll_err}")
                    else:
                        logging.warning(
                            f"Datei '{filename}' sollte im aktuellen Verzeichnis '{current_dir}' sein, aber Tile nicht gefunden.")
                        _show_snackbar_message(page_ref,
                                               f"⚠️ Datei '{filename}' nicht in Liste gefunden, obwohl im Ordner erwartet. Pfad wurde kopiert.",
                                               duration=4500)
                else:
                    logging.error("Interner Fehler: Aktuelles oder Zielverzeichnis konnte nicht bestimmt werden.")
                    _show_snackbar_message(page_ref, "❌ Interner Fehler: Verzeichnisinformation fehlt.", error=True)

            except pyperclip.PyperclipException as clip_err:
                logging.error(f"Fehler beim Kopieren in die Zwischenablage nach OCR: {clip_err}")
                _show_snackbar_message(page_ref, "❌ Fehler: Zwischenablage nicht verfügbar.", error=True, duration=4000)
            except Exception as proc_err:
                logging.error(f"Fehler beim Verarbeiten des OCR-Ergebnisses: {proc_err}", exc_info=True)
                _show_snackbar_message(page_ref, f"❌ Fehler bei Ergebnisverarbeitung: {proc_err}", error=True,
                                       duration=4000)

        elif error_message_local:
            # is_error = "❌" in error_message_local or "Fehler" in error_message_local.lower()
            # _show_snackbar_message(page_ref, error_message_local, error=is_error, duration=5000)
            _show_snackbar_message(page_ref, error_message_local, error=True, duration=5000)

        logging.debug("Setze OCR-Button-Status zurück.")
        ocr_button.disabled = not bool(current_material_root_path)
        ocr_button.text = "📷 Scan & Select"
        ocr_button.icon = ft.Icons.CAMERA_ALT_OUTLINED
        page_ref.update()

    def start_ocr_process_thread():
        """Startet den OCR-Prozess in einem separaten Thread, um UI-Blockaden zu vermeiden."""
        if ocr_button.disabled:
            logging.warning("OCR-Button Klick ignoriert, da er deaktiviert ist.")
            return

        logging.info("Starte OCR-Prozess in einem Hintergrund-Thread.")
        thread = threading.Thread(target=run_ocr_process, args=(page,), daemon=True)
        thread.start()

    # --- Layout Aufbau ---
    page.add(
        ft.Column(
            [
                header,
                ft.Row(
                    [back_button, ocr_button],
                    alignment=ft.MainAxisAlignment.START
                ),
                ft.Divider(height=5, thickness=1),
                listview
            ],
            expand=True
        )
    )
    # Initialer Tooltip für den Header
    header.tooltip = "Wähle einen Material-Wurzelordner aus dem Menü."

    logging.info("Flet App initialisiert. Warte auf Benutzerauswahl eines Material-Ordners.")
    page.update()


# --- App Start ---
if __name__ == "__main__":
    logging.info("Starte Flet Anwendung...")
    try:
        ft.app(target=main, assets_dir="assets")
    except Exception as app_e:
        logging.exception(f"Schwerwiegender Fehler beim Starten oder Ausführen der Flet App: {app_e}")
        print(f"\nFATAL ERROR: Could not run Flet app.")
        print(f"Please check the log file for details.")
        print(f"Error: {app_e}")
