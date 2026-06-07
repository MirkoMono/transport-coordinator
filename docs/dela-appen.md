# Dela Transport Coordinator med andra

Kort guide för dig som redan har appen och vill att kollegor ska kunna köra **demon på sin egen Mac**.

---

## Vad du delar

| Vad | Var |
|-----|-----|
| **Källkod** | https://github.com/MirkoMono/transport-coordinator |
| **Demomanual (svenska)** | [demo-manual-sv.md](demo-manual-sv.md) |
| **Licens** | Apache 2.0 — fritt att använda och modifiera |

Skicka kollegan **GitHub-länken** och länken till manualen (eller denna fil + manualen som PDF/export från GitHub).

---

## Tre sätt att dela

### 1. GitHub (bäst för utvecklare)

```bash
git clone https://github.com/MirkoMono/transport-coordinator.git
cd transport-coordinator
make setup-local
./scripts/start.sh
```

### 2. ZIP (utan Git)

1. GitHub → **Code → Download ZIP**  
2. Packa upp  
3. Öppna Terminal i mappen  
4. `make setup-local` → `./scripts/start.sh`

### 3. Skrivbordsgenväg (Mac, efter setup)

```bash
./scripts/install-desktop-shortcut.sh
```

Kollegan dubbelklickar **Start Transport Coordinator** på skrivbordet — ingen Terminal-kunskap krävs efter första installationen.

---

## Krav du bör nämna

- **Mac** med macOS (Windows/Linux: samma skript fungerar ofta, men manualen är skriven för Mac)
- **Python 3.12+** och **Node.js 22+**
- **Internet** vid geokodning (adresser → karta)
- **Ingen Docker** behövs för demon

---

## Mobiltest i teamet

Om någon ska testa **förarvy på telefon** under ett möte:

1. Värddatorn kör `./scripts/start.sh --mobile`
2. Alla på samma Wi‑Fi öppnar den URL som skrivs ut (t.ex. `http://192.168.x.x:5173/driver`)
3. Värden kör optimize i coordinator först så förardata finns

---

## Produktion / on-prem (senare)

För permanent installation med databas och Docker, se [on-prem-install.md](on-prem-install.md).

---

## Checklista — skicka till ny användare

- [ ] Länk: https://github.com/MirkoMono/transport-coordinator  
- [ ] Manual: `docs/demo-manual-sv.md`  
- [ ] Krav: Python 3.12, Node 22, `brew` om de saknar verktyg  
- [ ] Kommandon: `make setup-local` → `./scripts/start.sh`  
- [ ] Valfritt: `make desktop` för skrivbordsgenvägar  
