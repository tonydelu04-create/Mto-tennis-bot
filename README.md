# Bot MTO Tennis — Guida all'attivazione

Questo pacchetto contiene un piccolo programma che controlla i match di
tennis ATP/WTA live e ti manda un messaggio Telegram quando un giocatore
chiama un medical timeout (MTO). Gira gratis su GitHub Actions, quindi
non devi tenere acceso nulla.

Prerequisiti: avere gia' creato il bot Telegram (token + chat id).

## 1. Crea un account GitHub (se non ce l'hai)

Vai su https://github.com/signup e crea un account gratuito.

## 2. Crea un nuovo repository

1. In alto a destra clicca sul "+" poi "New repository".
2. Dai un nome (es. `mto-tennis-bot`).
3. Impostalo come **Private** (cosi' i tuoi dati restano privati).
4. Clicca "Create repository".

## 3. Carica i file di questo pacchetto

1. Nella pagina del repository appena creato, clicca su
   "uploading an existing file" (o "Add file" > "Upload files").
2. Trascina dentro TUTTI i file e le cartelle di questo pacchetto,
   compresa la cartella `.github` con dentro `workflows`
   (assicurati che il percorso resti `.github/workflows/check_mto.yml`).
3. Clicca "Commit changes" in basso per salvare.

## 4. Inserisci il token e il chat id come "Secrets"

Questi dati NON vanno scritti nel codice, ma salvati in modo sicuro:

1. Nel repository vai su "Settings" (in alto).
2. Nel menu a sinistra: "Secrets and variables" > "Actions".
3. Clicca "New repository secret".
   - Nome: `TELEGRAM_TOKEN` — Valore: il token che ti ha dato BotFather.
   - Clicca "Add secret".
4. Ripeti per un secondo secret:
   - Nome: `TELEGRAM_CHAT_ID` — Valore: il tuo chat id.

## 5. Attiva le GitHub Actions

1. Vai sulla scheda "Actions" del repository.
2. Se richiesto, clicca "I understand my workflows, go ahead and enable them".
3. Dovresti vedere il workflow "Controllo Medical Timeout".
4. Per testarlo subito senza aspettare: clicca sul workflow, poi
   "Run workflow" > "Run workflow" (bottone verde).

Da questo momento il controllo partira' automaticamente ogni 5 minuti
circa, e riceverai un messaggio Telegram ogni volta che viene rilevato
un medical timeout in un match ATP/WTA live.

## Cose da sapere

- **Non e' un dato ufficiale**: il programma legge i dati pubblici di
  SofaScore. Se SofaScore cambia il proprio sito, il bot potrebbe
  smettere di funzionare finche' non aggiorniamo il codice.
- **Non e' istantaneo al secondo**: il controllo avviene ogni ~5 minuti,
  a volte GitHub puo' ritardare leggermente l'esecuzione.
- Se qualcosa non funziona, vai sulla scheda "Actions", apri l'ultima
  esecuzione e guarda il log: spesso spiega subito il problema
  (es. secret scritto male).
