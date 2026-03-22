# Faza 3B: UX Testing Advanced
Data: 2026-03-22
Tester: Claude Code terminal [ux-tester-advanced]

## Summary
- Total teste: 13 (Test 8-20)
- Passed: 6 | Failed: 1 | Partial: 5 | Skipped: 1 | Issues found: 8

## Test Results

### [Test 8] Pause / Resume pe transfer activ
- **Status:** Partial
- **Observatii:** Pause functioneaza corect - status se schimba la "Stopped", butonul devine "Resume", Current Speed arata "Paused". Resume porneste un nou proces rclone care verifica fisierele deja transferate. Insa dupa resume, progress bar-ul se reseteaza si nu arata 100% chiar daca toate fisierele sunt verificate (55/55). Status ramane "Stopped" in loc de "Complete".
- **Screenshots:** 01-pause-clicked.png, 02-resumed.png, 03-pause-resume-complete.png

### [Test 9] Bandwidth Limit in timpul transferului
- **Status:** Pass
- **Observatii:** Dropdown-ul "Speed: Unlimited" pe dashboard functioneaza excelent. Schimbarea la 1 MB/s reduce viteza imediat (553 KiB/s vs 3 MB/s). Toast confirma "Speed limit: 1 MB/s". Revenirea la Unlimited functioneaza. Optiuni: 1, 2, 5, 10, 20, 50 MB/s.
- **Screenshots:** 04-bandwidth-limited.png

### [Test 10] New Transfer din dashboard
- **Status:** Partial
- **Observatii:** Butonul "New Transfer" de pe dashboard duce la wizard, dar arata summary-ul transferului ANTERIOR in loc sa porneasca un wizard nou/curat. Utilizatorul trebuie sa dea Back manual de mai multe ori.
- **Screenshots:** 05-new-transfer-from-dashboard.png

### [Test 11] Theme toggle (Dark/Light)
- **Status:** Partial
- **Observatii:** Toggle-ul functioneaza vizual - schimba intre dark si light mode. Insa tema NU persista dupa refresh. Dupa reload, pagina revine la light mode indiferent de setarea anterioara.
- **Screenshots:** 06-light-mode.png

### [Test 12] Multi-destination transfer
- **Status:** Partial
- **Observatii:** Feature-ul de multi-destination EXISTA. Butonul "+ Add another destination" apare dupa selectarea primei destinatii. Se pot selecta 2+ destinatii (GDrive + OneDrive). UI arata "2 destinations selected" cu butoane de remove (x). Insa exista un bug: dupa ce adaugi 2 destinatii si apesi din nou pe "+ Add another destination", butonul Next se dezactiveaza si nu exista mod de a anula - utilizatorul ramane blocat.
- **Screenshots:** 07-multi-dest.png

### [Test 13] Wizard cu Proton Drive (rate-limited provider)
- **Status:** Partial
- **Observatii:** Transferul catre Proton Drive porneste dar intampina probleme semnificative. Viteza scade dramatic (de la ~1 MB/s la 4 KiB/s). 15-22 erori "File or folder not found. It may have been moved or deleted." in timpul transferului. Dashboard-ul arata date inconsistente (23.4% progress dar 20.04 MiB transferat din 20 MB folder asteptat). Nu s-au observat protectii automate vizibile in UI pentru rate limiting.
- **Screenshots:** 08-proton-transfer.png, 09-proton-complete.png

### [Test 14] Transfer History si Resume din History
- **Status:** Pass
- **Observatii:** Link-ul "Transfer History" din footer deschide un dialog cu toate sesiunile anterioare. Afiseaza: source -> dest, size, numar fisiere, numar sesiuni, data. Fiecare transfer are buton "Resume" functional. Dialog are buton "Close". 7 transferuri vizibile din sesiunile curente si anterioare.
- **Screenshots:** 10-transfer-history.png

### [Test 15] Presets - Save si Run
- **Status:** Pass
- **Observatii:** Butonul "Save as Preset" pe summary step functioneaza. Dialog cu input pre-populat (ex: "01.11.2023 -> protondrive"). Dupa save, preset-ul apare pe dashboard in sectiunea "Presets" cu butoane "Run" si "Delete". Arata detalii: nume, config, "Used 0x", "Last: Never".
- **Screenshots:** 11-preset-saved.png, 12-preset-run.png

### [Test 16] Error handling - Transfer la un remote inexistent
- **Status:** Fail
- **Observatii:** CloudHop accepta "fakeremote" ca destinatie FARA nicio validare. Wizard-ul trece prin toti pasii fara eroare. Transfer-ul porneste pe dashboard ("Local -> fakeremote") dar se opreste imediat cu "Stopped", 0 B transferat, FARA mesaj de eroare care sa explice ca remote-ul nu exista. Utilizatorul nu stie de ce transferul a esuat.
- **Screenshots:** 13-error-fake-remote.png

### [Test 17] Wizard Browse Button
- **Status:** Pass
- **Observatii:** Butonul "Browse Folders" exista pe step-ul Source cand selectezi Local Folder. Apare alaturi de textbox-ul pentru Folder Path si zona de drag & drop ("Drag a folder here").
- **Screenshots:** (observat in Test 8 setup)

### [Test 18] Dashboard - Error Log View
- **Status:** Pass
- **Observatii:** Sectiunea "Errors" apare pe dashboard cand exista erori (observat in testul Proton Drive). Arata mesajele de eroare si include un buton "Report this problem" care deschide GitHub issue cu nota "Opens GitHub so you can describe what happened. No personal data is shared."
- **Screenshots:** (observat in 09-proton-complete.png)

### [Test 19] Responsive - Window mic
- **Status:** Pass
- **Observatii:** La 768x600 (tablet-like), atat wizard-ul cat si dashboard-ul se redimensioneaza corect. Toate elementele sunt accesibile, textul nu se suprapune, butoanele raman vizibile. Layout-ul se adapteaza bine.
- **Screenshots:** 16-responsive-wizard.png, 17-responsive-dashboard.png

### [Test 20] Concurrent access - 2 taburi
- **Status:** Skip
- **Observatii:** Se pot deschide 2 taburi independente (dashboard + wizard). Ambele functioneaza. Insa testarea completa a CSRF tokens si state sync intre taburi depaseste capacitatea instrumentelor de testare utilizate.
- **Screenshots:** (fara screenshot dedicat)

## Findings

### [F305] Update banner sugereaza downgrade
- **Severitate:** Medium
- **Pagina:** dashboard
- **Problema:** Alert banner spune "CloudHop 0.11.0 is available (you have 0.12.0)" cu link catre v0.11.0. Compara versiuni cu != (string) in loc de comparatie semantica, sugerand downgrade.
- **Screenshot:** 00-update-banner-bug.png
- **Status:** Open (confirmat de user)

### [F306] Progress bar nu se actualizeaza corect dupa Resume
- **Severitate:** High
- **Pagina:** dashboard
- **Problema:** Dupa Pause/Resume, progress bar-ul se reseteaza si arata doar progresul noii sesiuni, nu totalul. Arata 39% in loc de 100% chiar daca toate fisierele sunt verified (55/55). Status ramane "Stopped" in loc de "Complete/Done". Transferurile necesita multiple resume-uri pentru a finaliza.
- **Screenshot:** 03-pause-resume-complete.png
- **Status:** Open

### [F307] Multi-destination - buton "+ Add" blocheaza wizard-ul
- **Severitate:** Medium
- **Pagina:** wizard (destination step)
- **Problema:** Dupa adaugarea a 2 destinatii, daca user-ul apasa din nou pe "+ Add another destination", butonul Next se dezactiveaza si nu exista optiune de cancel/undo. Utilizatorul ramane blocat si trebuie sa navigheze manual cu URL.
- **Screenshot:** 07-multi-dest.png
- **Status:** Open

### [F308] Theme toggle nu persista dupa refresh
- **Severitate:** Low
- **Pagina:** toate paginile
- **Problema:** Schimbarea temei (dark/light) functioneaza vizual dar nu se salveaza in localStorage/cookie. Dupa refresh, tema revine la default (light).
- **Screenshot:** 06-light-mode.png
- **Status:** Open

### [F309] "New Transfer" nu reseteaza wizard-ul
- **Severitate:** Low
- **Pagina:** wizard (via dashboard "New Transfer" link)
- **Problema:** Click pe "New Transfer" de pe dashboard duce la wizard dar arata configuratia transferului anterior (summary step). Ar trebui sa porneasca un wizard fresh de la step 1.
- **Screenshot:** 05-new-transfer-from-dashboard.png
- **Status:** Open

### [F310] Remote inexistent acceptat fara validare
- **Severitate:** High
- **Pagina:** wizard + dashboard
- **Problema:** Wizard-ul permite selectarea "Other" si introducerea unui remote name inexistent ("fakeremote") fara nicio validare. Transferul porneste si esueaza silentios pe dashboard (0 B transferat, "Stopped") fara mesaj de eroare care sa indice cauza. Utilizatorul nu primeste niciun feedback actionabil.
- **Screenshot:** 13-error-fake-remote.png
- **Status:** Open

### [F311] Proton Drive - erori frecvente si viteza scazuta
- **Severitate:** Medium
- **Pagina:** dashboard (transfer Proton Drive)
- **Problema:** Transfer-ul catre Proton Drive genereaza 15-22 erori "File or folder not found". Viteza scade dramatic (de la 1 MB/s la 4 KiB/s). Nu se observa in UI aplicarea automata a protectiilor specifice Proton Drive (transfers=2, checkers=4, tpslimit=4).
- **Screenshot:** 09-proton-complete.png
- **Status:** Open

### [F312] Butoane Pause si Resume vizibile simultan
- **Severitate:** Low
- **Pagina:** dashboard
- **Problema:** La pornirea unui transfer nou, atat butonul "Pause transfer" cat si "Resume transfer" sunt vizibile simultan pe dashboard. Ar trebui sa fie vizibil doar unul la un moment dat, in functie de starea transferului.
- **Screenshot:** 08-proton-transfer.png
- **Status:** Open
