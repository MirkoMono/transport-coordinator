# Transport Coordinator — Demomanual (svenska)

Den här guiden visar hur du kör **demonstrationen** på din Mac och testar hela flödet: importera crew, geokoda adresser, optimera rutter och öppna förarvy.

**Ingen Docker krävs** för demon. Internet behövs för geokodning (Nominatim/OpenStreetMap).

---

## 1. Vad gör appen?

**FLX / Transport Coordinator** hjälper en transportkoordinator att:

1. Ta emot en lista med **personer och upphämtningsadresser**
2. **Geokoda** adresserna (hitta koordinater på kartan)
3. **Optimera** vilken bil som hämtar vem, i vilken ordning
4. Visa resultat på **karta**, exportera **PDF** och öppna **förarvy** på mobil

Demon innehåller **12 fiktiva crew-medlemmar** i Stockholmsområdet.

---

## 2. Krav

| Program | Version | Installera (Mac) |
|---------|---------|------------------|
| **Python** | 3.12+ | `brew install python@3.12` |
| **Node.js** | 22+ | `brew install node` |
| **Git** | valfritt | `brew install git` |

Kontrollera:

```bash
python3.12 --version
node --version
```

---

## 3. Hämta appen (första gången)

### Alternativ A — Git (rekommenderas)

```bash
git clone https://github.com/MirkoMono/transport-coordinator.git
cd transport-coordinator
```

### Alternativ B — ZIP från GitHub

1. Öppna https://github.com/MirkoMono/transport-coordinator  
2. Klicka **Code → Download ZIP**  
3. Packa upp och öppna mappen `transport-coordinator` i Terminal

### Installera beroenden (engångs)

```bash
make setup-local
```

Detta skapar Python-miljö, installerar paket och laddar ner webberoenden. Tar några minuter första gången.

---

## 4. Starta appen

### Snabbast — ett kommando

```bash
./scripts/start.sh
```

Webbläsaren öppnas på http://localhost:5173

### Skrivbordsgenväg (Mac)

```bash
./scripts/install-desktop-shortcut.sh
```

Två ikoner läggs på **Skrivbordet**:

- **Start Transport Coordinator** — startar appen och öppnar webbläsaren  
- **Stop Transport Coordinator** — stänger API och webb

> Första gången du dubbelklickar **Start** kan macOS fråga om tillåtelse att köra skriptet. Välj **Öppna** i Systeminställningar → Integritet om det behövs.

### Stoppa appen

```bash
./scripts/stop.sh
```

eller dubbelklicka **Stop** på skrivbordet.

---

## 5. Demogenomgång — steg för steg

När appen körs ska du se **FLX** högst upp och flikarna **COORDINATOR | DRIVER**.

### Steg 1 — Production och set

1. Se till att du är på fliken **Routes** (nederst).
2. Fyll i **Production** — t.ex. `Dag 14` eller `Demo`.
3. Fyll i **Set / destination** — t.ex. `Filmstaden` eller en adress i Stockholm.
4. Klicka utanför fältet (blur) så adressen **geokodas**. Du ser meddelandet *Set geocoded.*

Set-adressen blir **depå** — dit bilarna ska köra efter upphämtningar.

### Steg 2 — Ladda demo

1. Under **Import method**, välj **CSV (addresses)**.
2. Klicka **Load demo (12)** — 12 rader med namn och adresser fylls i.

### Steg 3 — Importera och geokoda

1. Klicka **Import & geocode**.
2. Vänta cirka **12 sekunder** (en adress i taget mot Nominatim).
3. Kontrollera rutan **Pickups** — den ska visa t.ex. `12/12 geocoded`.

Om någon adress misslyckas visas ett lägre tal. Demon ska ge 12/12.

### Steg 4 — Call time

Ställ **Call time** — standard är `08:00`. Gäller alla i demon.

### Steg 5 — Optimera rutter

1. Klicka **Optimize routes**.
2. Efter någon sekund visas **Results** med fordon, sträcka (km) och stoppordning.

### Steg 6 — Karta

1. Gå till fliken **Map** (nederst).
2. Du ser upphämtningspunkter, depå (set) och färgade ruttlinjer per fordon.

### Steg 7 — PDF (valfritt)

Under **Results**, klicka **PDF** för att ladda ner förarmanifest.

### Steg 8 — Förarvy

1. Klicka **DRIVER** högst upp (eller öppna http://localhost:5173/driver).
2. Välj fordon i listan.
3. Varje stopp visar namn, adress och länk till kartnavigering.

Förarvy läser senaste körningen från samma webbläsare (localStorage).

---

## 6. Testa på mobiltelefon

**Ja — det går**, på samma Wi‑Fi som din Mac.

### Starta i mobil-läge

```bash
./scripts/stop.sh          # stoppa om redan igång
./scripts/start.sh --mobile
```

Terminalen visar en adress som t.ex.:

```
http://192.168.1.42:5173
```

### På telefonen

1. Anslut telefonen till **samma Wi‑Fi** som datorn.
2. Öppna Safari (iPhone) eller Chrome (Android).
3. Skriv in adressen från terminalen — t.ex. `http://192.168.1.42:5173`
4. Förarvy: lägg till `/driver` i slutet.

### Tips

- Om sidan inte laddas: kontrollera att Mac-brandväggen tillåter inkommande anslutningar för Node, eller testa med brandvägg tillfälligt av.
- Hitta Mac-IP manuellt: `ipconfig getifaddr en0`
- På iPhone kan du **Lägg till på hemskärmen** (Dela → Lägg till på hemskärmen) för PWA-liknande förarvy.

---

## 7. Vanliga problem

| Problem | Lösning |
|---------|---------|
| `Run setup first: make setup-local` | Kör `make setup-local` en gång |
| API svarar inte | Kör `./scripts/stop.sh` och sedan `./scripts/start.sh` igen |
| `Import and geocode addresses first` | Klicka **Import & geocode** innan Optimize |
| Set geocoding failed | Skriv en tydligare adress, t.ex. gatuadress + stad |
| AI call sheet är grå | Normalt — AI kräver Docker + Ollama. Demon fungerar med CSV |
| Port 5173 upptagen | `./scripts/stop.sh` eller stäng annan Vite-process |

Loggar vid felsökning:

```bash
tail -f .run/api.log
tail -f .run/web.log
```

---

## 8. Dela med andra

Se **[dela-appen.md](dela-appen.md)** — kort guide för att skicka repo-länk, krav och skrivbordsgenväg till kollegor.

---

## 9. Support och källa

- **Kod:** https://github.com/MirkoMono/transport-coordinator  
- **API-dokumentation (lokal):** http://localhost:8000/docs  
- **Design:** [design.md](design.md)

*Senast uppdaterad: 2026-06-06*
