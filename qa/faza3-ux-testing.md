# Faza 3: UX Testing
Data: 2026-03-21
Tester: Claude Code terminal [ux-tester]

## Summary
- Total teste: 7
- Passed: 4 | Failed: 1 | Partial: 2 | Issues found: 4

## Test Results

### [Test 1] Wizard Flow - Local -> GDrive
- **Status:** PASS
- **Durata transfer:** 1m 14s
- **Fisiere:** 70 files, 21.52 MiB
- **Avg Speed:** 295 KiB/s, Peak: 499 KiB/s
- **Erori:** 0
- **Observatii:** Wizard flow complet functional. Welcome -> Source -> Destination -> Options -> Connect -> Summary -> Start -> Dashboard. Transfer complet cu dialog de completion. Butoanele "Verify transfer integrity" si "Download transfer receipt" prezente. Progres dots vizibile. Provider cards responsive.
- **Screenshots:** 01-wizard-welcome.png, 02-wizard-options.png, 03-wizard-summary.png, 04-dashboard-result.png

### [Test 2] Settings Page
- **Status:** PASS
- **Observatii:** Pagina /settings se incarca corect. SMTP fields vizibile (Host, Port, TLS, From, To, Username, Password). Toggle Enable/Disable functional - campurile sunt disabled cand toggle OFF. Butoane "Send Test Email" si "Save Settings" prezente (disabled cand toggle OFF). Gear icon in header wizard si dashboard duce la /settings. Link "Back to Dashboard" functional.
- **Screenshots:** 05-settings-page.png

### [Test 3] Cloud -> Cloud - Google Drive -> OneDrive
- **Status:** FAIL
- **Eroare:** "File or folder not found. It may have been moved or deleted."
- **Observatii:** Transferul de la gdrive:e2e-screenshots -> onedrive: a esuat. Cauza: fisierele din Test 1 au fost copiate la root-ul GDrive (in subfoldere fresh-install/, edge-cases/, etc.), nu intr-un folder "e2e-screenshots". Cand rclone copiaza un folder local la gdrive:, copiaza CONTINUTUL folderului, nu creeaza un wrapper folder. Deci gdrive:e2e-screenshots nu exista. Dashboard-ul a afisat corect eroarea cu optiunea "Report this problem".
- **Screenshots:** 06-gdrive-to-onedrive-result.png

### [Test 4] Local -> Dropbox (subfolder mic, 20MB)
- **Status:** PASS
- **Durata transfer:** 11s
- **Fisiere:** 23 files, 20.04 MiB
- **Avg Speed:** 1.74 MiB/s
- **Erori:** 0
- **Observatii:** Transfer rapid si complet. Dialog de completion functional. Recently Completed arata fisierele transferate (poze Serb Monica/*.JPG). File Types chart arata .jpg: 8.
- **Bug minor:** Dashboard arata "Files: 23 / 70 (32.9%)" - contorul total (70) este ramas de la sesiunea anterioara (Test 1), nu reflecta transferul curent de 23 fisiere. Dialogul de completion arata corect "23 files".
- **Screenshots:** 07-dropbox-result.png

### [Test 5] Transfer fisier PDF singur - Local -> Google Drive
- **Status:** PARTIAL (by design)
- **Observatii:** Wizard-ul afiseaza eroare de validare: "This path is not a directory. Please select a folder." cand se introduce un path catre un fisier (nu folder). Wizard-ul nu suporta transfer de fisiere individuale - doar foldere. Validarea functioneaza corect (mesaj clar, nu crash). Aceasta e o limitare de design, nu un bug.
- **Screenshots:** 08-pdf-result.png

### [Test 6] Edge Cases
- **Status:** PARTIAL (mixed results)

**6.1 Refresh mid-wizard:**
- Wizard-ul pastreaza starea dupa refresh (revine pe step-ul curent, nu se reseteaza la Welcome). Comportament acceptabil - persist wizard state.
- **Screenshot:** 09-refresh-midwizard.png

**6.2 Back navigation:**
- Browser Back functioneaza normal - duce la pagina anterioara din history (dashboard). Nu sunt erori.

**6.3 404 page:**
- Pagina 404 custom excelenta - cloud mascota confuza, mesaj "Even the cloud is confused", link "Help the cloud find its way" -> /. Design polished.
- **Screenshot:** 10-404-page.png

**6.4 Dashboard fara transfer activ:**
- Dashboard-ul arata ultimul transfer completat (nu un state "idle" propriu-zis). Informatii de session, charts, recently completed - toate vizibile. Banner-ul de completion ramane vizibil.
- **Screenshot:** 11-dashboard-idle.png

**6.5 Wizard cu path invalid:**
- Validare server-side functionala: "This path does not exist. Please check and try again." in rosu sub camp. Next button ramane activ dar nu avanseaza.
- **Screenshot:** 12-invalid-path.png

**6.6 Special characters in URL:**
- /static/wizard.css?v=test123 returneaza CSS valid (nu 404). Query params nu afecteaza servirea static files.

**6.7 Gear icon test:**
- Gear icon prezent in wizard header (link Settings -> /settings). PASS.
- Gear icon prezent in dashboard header (link Settings -> /settings). PASS.
- Click functioneaza din ambele pagini.

### [Test 7] Transfer mare - Local -> OneDrive (ISTORIC CT, 304MB)
- **Status:** PASS
- **Durata transfer:** 35s
- **Fisiere:** 1 file (DICOM CT Serb Madalina.zip), 303.82 MiB
- **Avg Speed:** 8.61 MiB/s, Peak: 9.01 MiB/s
- **Erori:** 0
- **Observatii:** Transfer foarte rapid (internet rapid). Folderul ISTORIC CT contine un singur fisier ZIP mare. Nu s-au putut captura screenshots de progres intermediar - transferul s-a terminat in 35s. Dialog de completion corect. Session timeline, file types chart vizibile.
- **Bug minor:** Contorul "Files: 1 / 70 (1.4%)" - totalul 70 e stale din sesiunea anterioara.
- **Screenshots:** 13-large-transfer-start.png, 16-large-transfer-complete.png

## Findings

### [F301] Source subfolder nu se reseteaza cand schimbi tipul sursei
- **Severitate:** Medium
- **Pagina:** wizard
- **Problema:** Cand setezi un Source Subfolder pentru o sursa cloud (ex: "e2e-screenshots" pentru GDrive), apoi schimbi sursa la "Local Folder", subfolder-ul vechi ramane intern si se adauga la path-ul local. Campul Source Subfolder nu apare in UI pentru surse locale, dar valoarea persista. Rezultat: path-ul din Summary devine "/path/local/e2e-screenshots" (incorect). Problema persista chiar si dupa page refresh si localStorage.clear() - starea e persistata server-side.
- **Reproductie:** Set source=GDrive, set subfolder="test" in Options -> Go back -> Change source to Local -> Enter path -> Go to Summary -> Path shows "/your/path/test"
- **Screenshot:** N/A (observat in snapshot text)
- **Status:** Open

### [F302] Contorul total fisiere (denominator) e stale intre transferuri
- **Severitate:** Low
- **Pagina:** dashboard
- **Problema:** Dashboard-ul afiseaza "Files: X / 70" unde 70 e numarul de fisiere din primul transfer, nu din transferul curent. Dialogul de completion afiseaza numarul corect, dar progress bar-ul si stats-urile de pe dashboard pastreaza totalul vechi.
- **Reproductie:** Ruleaza Transfer 1 (70 fisiere) -> Ruleaza Transfer 2 (23 fisiere) -> Dashboard arata "23 / 70 (32.9%)" in loc de "23 / 23 (100%)"
- **Screenshot:** 07-dropbox-result.png, 16-large-transfer-complete.png
- **Status:** Open

### [F303] Wizard nu suporta transfer de fisiere individuale
- **Severitate:** Low (feature request)
- **Pagina:** wizard
- **Problema:** Source path accepta doar directoare, nu fisiere individuale. Mesajul de eroare e clar: "This path is not a directory. Please select a folder." Ar fi util sa permita si selectarea de fisiere individuale.
- **Screenshot:** 08-pdf-result.png
- **Status:** Open

### [F304] Cloud-to-cloud: subfolder sursa nu exista dupa copy la root
- **Severitate:** Medium
- **Pagina:** wizard + transfer
- **Problema:** Daca copiezi un folder local la cloud root (fara dest subfolder), fisierele ajung direct la root, nu intr-un folder cu numele sursei. Apoi cand incerci un transfer cloud-to-cloud cu acel nume de folder ca source subfolder, nu gaseste folder-ul. Utilizatorul se asteapta ca "e2e-screenshots" sa existe pe GDrive dupa ce a copiat folderul local cu acelasi nume.
- **Screenshot:** 06-gdrive-to-onedrive-result.png
- **Status:** Open

## Cleanup
- gdrive: Sters fresh-install/, edge-cases/, proton/, onedrive/ (62 fisiere) - DONE
- onedrive: Sters DICOM CT Serb Madalina.zip - DONE
- dropbox: poze Serb Monica/ sters - DONE
- Originalele de pe Desktop: NEATINSE

## Logs
- /tmp/cloudhop-fix/qa/faza3-logs/server.log
- /tmp/cloudhop-fix/qa/faza3-logs/cloudhop-server.log
- /tmp/cloudhop-fix/qa/faza3-logs/cloudhop_*.log (3 fisiere)
