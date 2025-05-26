Regelübersicht:

| Kategorie                    | Keywords                          | Parameter / Bedingung                              | Wertebereich                                     | Ziel (`path`, `code`)              |
| ---------------------------- | --------------------------------- | -------------------------------------------------- | ------------------------------------------------ | ---------------------------------- |
| **Nuten mit Rückzug**        | `["nuten rückzug"]`               | `bbox_b`                                           | 3.1 – 4.0                                        | `07_NUTEN\NUTEN mit Rückzug`, "01" |
|                              |                                   |                                                    | 4.1 – 6.0                                        | `07_NUTEN\NUTEN mit Rückzug`, "02" |
|                              |                                   |                                                    | 6.1 – 8.0                                        | `07_NUTEN\NUTEN mit Rückzug`, "03" |
|                              |                                   |                                                    | 8.1 – 9.0                                        | `07_NUTEN\NUTEN mit Rückzug`, "04" |
|                              |                                   |                                                    | 9.1 – 14.0                                       | `07_NUTEN\NUTEN mit Rückzug`, "05" |
|                              |                                   |                                                    | 14.1 – 18.0                                      | `07_NUTEN\NUTEN mit Rückzug`, "06" |
|                              |                                   |                                                    | 18.1 – 22.0                                      | `07_NUTEN\NUTEN mit Rückzug`, "07" |
| **Nuten**                    | `["nuten"]`                       | `bbox_b`                                           | 3.1 – 4.0                                        | `07_NUTEN`, "01"                   |
|                              |                                   |                                                    | 4.1 – 6.0                                        | `07_NUTEN`, "02"                   |
|                              |                                   |                                                    | 6.1 – 8.0                                        | `07_NUTEN`, "03"                   |
|                              |                                   |                                                    | 8.1 – 9.0                                        | `07_NUTEN`, "04"                   |
|                              |                                   |                                                    | 9.1 – 14.0                                       | `07_NUTEN`, "05"                   |
|                              |                                   |                                                    | 14.1 – 18.0                                      | `07_NUTEN`, "06"                   |
|                              |                                   |                                                    | 18.1 – 22.0                                      | `07_NUTEN`, "07"                   |
| **Plan**                     | `["plan"]`                        | Kombination aus `tief`, `kl_r`, `bbox_l`, `bbox_b` | ≤ 40 tief & kl\_r=5 → "05"                       | `01_Plan-Aussen-Fase-Tasche`, "05" |
|                              |                                   |                                                    | ≤ 40 tief & kl\_r∈{15,10,0.2,0} → "01"           | `01_Plan-Aussen-Fase-Tasche`, "01" |
|                              |                                   |                                                    | 40.01 – 52 tief & kl\_r≤20 → "02"                | `01_Plan-Aussen-Fase-Tasche`, "02" |
|                              |                                   |                                                    | ≤ 40.5 tief & kl\_r≤5 & bbox\_l≤40 → "06"        | `01_Plan-Aussen-Fase-Tasche`, "06" |
|                              |                                   |                                                    | ≤ 40.5 tief & kl\_r≤10 & 40.1≤bbox\_l≤180 → "04" | `01_Plan-Aussen-Fase-Tasche`, "04" |
| **Tasche Profit**            | `["tasche profit"]`               | `tief` & `kl_r`                                    | kl\_r 0 – 1.5   → "01"                           | `02_Taschen\Profit`, "01"          |
|                              |                                   |                                                    | 1.51 – 2.0     → "02"                            | `02_Taschen\Profit`, "02"          |
|                              |                                   |                                                    | 2.01 – 2.5     → "03"                            | `02_Taschen\Profit`, "03"          |
|                              |                                   |                                                    | 2.51 – 3.0     → "04"                            | `02_Taschen\Profit`, "04"          |
|                              |                                   |                                                    | 3.01 – 4.0     → "05"                            | `02_Taschen\Profit`, "05"          |
|                              |                                   |                                                    | 4.01 – 5.0     → "07"                            | `02_Taschen\Profit`, "07"          |
|                              |                                   |                                                    | 5.01 – 6.0     → "08"                            | `02_Taschen\Profit`, "08"          |
|                              |                                   |                                                    | 6.01 – 8.0     → "10"                            | `02_Taschen\Profit`, "10"          |
|                              |                                   | klein (11 – 39.99 bbox) & 5.0 – 20 kl\_r → "07"    | `02_Taschen\Profit`, "07" (kleine Tasche)        |                                    |
|                              |                                   | bbox ≥ 40 & kl\_r 4.01 – 5 & tief ≤ 40 → "09"      | `02_Taschen\Profit`, "09"                        |                                    |
|                              |                                   | bbox ≥ 40 & kl\_r 21.01 – 200 & tief ≤ 40 → "11"   | `02_Taschen\Profit`, "11"                        |                                    |
| **Passung Fräsen**           | `["passung fräsen"]`              | `dia`                                              | 1.52 – 2.5   → "01"                              | `06_Passung Fräsen`, "01"          |
|                              |                                   |                                                    | 2.51 – 3.5   → "02"                              | `06_Passung Fräsen`, "02"          |
|                              |                                   |                                                    | 3.51 – 4.5   → "03"                              | `06_Passung Fräsen`, "03"          |
|                              |                                   |                                                    | 4.51 – 6.5   → "04"                              | `06_Passung Fräsen`, "04"          |
|                              |                                   |                                                    | 6.51 – 8.5   → "05"                              | `06_Passung Fräsen`, "05"          |
|                              |                                   |                                                    | 8.51 – 10.5  → "06"                              | `06_Passung Fräsen`, "06"          |
|                              |                                   |                                                    | 10.51 – 14.5 → "07"                              | `06_Passung Fräsen`, "07"          |
|                              |                                   |                                                    | 14.51 – 18.5 → "08"                              | `06_Passung Fräsen`, "08"          |
|                              |                                   |                                                    | 12.51 – 23.5 → "09"                              | `06_Passung Fräsen`, "09"          |
|                              |                                   | 23.51 – 31 dia & tief ≤ 40 → "10"                  | `06_Passung Fräsen`, "10" (16er)                 |                                    |
|                              |                                   | 31.01 – 39 dia & tief ≤ 40 → "11"                  | `06_Passung Fräsen`, "11" (16×52)                |                                    |
|                              |                                   | 31.01 – 39 dia & 40.01 – 52 tief → "13"            | `06_Passung Fräsen`, "13"\`                      |                                    |
| **Bohrung KM (mit Senkung)** | `["bohrung km"]`                  | `dia`                                              | 2.5 – 3.7   → "01"                               | `05_DGB\nur Senkung`, "01"         |
|                              |                                   |                                                    | 4.0 – 5.0   → "02"                               | `05_DGB\nur Senkung`, "02"         |
|                              |                                   |                                                    | 5.1 – 6.2   → "03"                               | `05_DGB\nur Senkung`, "03"         |
|                              |                                   |                                                    | 6.3 – 8.7   → "04"                               | `05_DGB\nur Senkung`, "04"         |
|                              |                                   |                                                    | 8.9 – 10.0  → "05"                               | `05_DGB\nur Senkung`, "05"         |
|                              |                                   |                                                    | 10.1 – 10.8 → "06"                               | `05_DGB\nur Senkung`, "06"         |
|                              |                                   |                                                    | 10.9 – 12.0 → "07"                               | `05_DGB\nur Senkung`, "07"         |
|                              |                                   |                                                    | 12.1 – 14.0 → "08"                               | `05_DGB\nur Senkung`, "08"         |
|                              |                                   |                                                    | 16.1 – 18.0 → "09"                               | `05_DGB\nur Senkung`, "09"         |
| **Trennen**                  | `["trennen"]`                     | immer wahr                                         | –                                                | `13_Trennen`, "01"                 |
| **Bohrung mit Rückzug**      | `["bohrung rückzug"]`             | `dia`                                              | 2.0 – 6.97  → "01"                               | `05_DGB\+DGB mit Rückzug`, "01"    |
|                              |                                   |                                                    | 6.99 – 7.01 → "03"                               | `05_DGB\+DGB mit Rückzug`, "03"    |
|                              |                                   |                                                    | 7.02 – 9.29 → "01"                               | `05_DGB\+DGB mit Rückzug`, "01"    |
|                              |                                   |                                                    | 9.3 – 17.5  → "02"                               | `05_DGB\+DGB mit Rückzug`, "02"    |
|                              |                                   |                                                    | 17.99 – 18.01 → "04"                             | `05_DGB\+DGB mit Rückzug`, "04"    |
|                              |                                   |                                                    | 19.99 – 20.01 → "05"                             | `05_DGB\+DGB mit Rückzug`, "05"    |
|                              |                                   |                                                    | 21.99 – 22.01 → "06"                             | `05_DGB\+DGB mit Rückzug`, "06"    |
|                              |                                   |                                                    | 25.99 – 26.01 → "07"                             | `05_DGB\+DGB mit Rückzug`, "07"    |
| **Bohrung allgemein**        | `["bohrung"]`                     | analog Rückzug (ohne Rückzug)                      | 2.0 – 6.97  → "01"<br>6.99 – 7.01 → "03"<br>…    | `05_DGB`, "01"–"07"                |
| **Gewinde**                  | `["gewinde m","gewinde"]`         | `dia`                                              | 2.0 – 7.0   → "03"<br>7.01 – 12.5 → "04"         | `03_Bohrungen`, "03"/"04"          |
| **Reiben**                   | `["reib ohne o","reiben ohne o"]` | `dia`                                              | 3.0 – 8.05  → "05"<br>10.0 – 12.05 → "06"        | `03_Bohrungen`, "05"/"06"          |
|                              | `["reib mit o","reiben mit o"]`   | `dia`                                              | 3.0 – 8.05  → "01"<br>10.0 – 12.05 → "02"        | `03_Bohrungen`, "01"/"02"          |


