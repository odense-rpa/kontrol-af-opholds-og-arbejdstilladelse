# Kontrol af opholds- og arbejdstilladelse

Robotten kontrollerer løbende, at medarbejdere fra lande uden for EU/EØS har en aktiv opholds- og arbejdssag i SBSYS med en gyldig erindring, og at erindringen er tildelt sagens sagsbehandler.

Robotten kører i to trin: først fyldes arbejdskøen med medarbejdere, derefter behandles hvert element i køen.

## Trin 1: Fyld arbejdskøen (`populate_queue`)

Køres med `--queue`.

1. Elementer med status *NEW* ryddes fra arbejdskøen.
2. Medarbejdere hentes fra tabellen `statsborgerskab` i DWH (`DWHService.hent_medarbejdere`). Kun medarbejdere, hvis `Land_statsborger` **ikke** er et EU/EØS-land, et nordisk land eller Ukraine, medtages.
3. `Tjenestenr` deles op: de første 2 cifre er institutionsnøglen, resten er tjenestenummeret.
4. For hver medarbejder lægges et `Medarbejder`-element i køen med CPR-nummeret som reference. Elementet indeholder CPR-nummer (valideres og normaliseres til `DDMMÅÅ-XXXX`), navn, tjenestenummer, institutionsnøgle og statsborgerskab.

## Trin 2: Behandl arbejdskøen (`process_workqueue`)

Hvert element i køen behandles sådan:

1. **Find opholdssagen.** I SBSYS søges efter en aktiv sag (status 6) med sagsskabelon **3127**, der matcher medarbejderens CPR-nummer, `EmploymentId` (tjenestenummer) og `InstitutionCode` (institutionsnøgle). Sagen tæller kun som fundet, hvis der er præcis én.
2. **Ingen opholdssag fundet.** Så søges efter en ansættelsessag (sagsskabelon **699**) med de samme kriterier:
   - Ansættelsessag fundet: elementet går til manuel behandling med årsagen *"Arbejds- og opholdssag kunne ikke findes på medarbejder for givet tjenestenr"*, og sagsbehandleren hentes fra ansættelsessagen.
   - Ingen ansættelsessag: elementet går til manuel behandling med årsagen *"'Arbejds- og opholdssag' og 'Ansættelsessag' ikke fundet på medarbejder"*.
3. **Opholdssag fundet.** Erindringerne på sagen kontrolleres (`SbsysService.kontroller_erindring_på_sag`). Kun erindringer med *"opholds- og arbejdstilladelse"* i navnet og en frist mere end 14 dage frem i tiden tæller med.
   - Ingen matchende erindring: manuel behandling med årsagen *"Ingen 'arbejds- og opholdserindring' fundet på sagen"*.
   - Mere end én matchende erindring: manuel behandling med årsagen *"Mere end én 'arbejds- og opholdserindring' erindring fundet på sagen"*.
   - Én matchende erindring, og den ansvarlige er sagens sagsbehandler: alt er i orden.
   - Én matchende erindring, men den ansvarlige er ikke sagens sagsbehandler: erindringen opdateres automatisk, så sagens sagsbehandler bliver ansvarlig. Fejler opdateringen, går elementet til manuel behandling med fejldetaljerne.
4. **Tracking.** Hvert behandlet element registreres i odk-tools under procesnavnet *"Kontrol af opholds- og arbejdstilladelse"*.
5. **Rapportering.** Elementer til manuel behandling rapporteres via odk-tools under nøglen `kontrol-af-opholds-og-arbejdstilladelse` med typen *Manuel* og felterne Cpr, Navn, Tjenstenr, Sagsbehandler og Årsag.
6. **Fejl.** Opstår en `WorkItemError`, bliver fejlen logget, og elementet markeres som fejlet.

## Forudsætninger

- Python ≥ 3.13
- [`uv`](https://docs.astral.sh/uv/) til pakkehåndtering
- Adgang til **SBSYS**
- Adgang til **Odense SQL Server** (DWH og tracking)

## Installation

```sh
uv sync
```

## Konfiguration

Robotten bruger to credentials:

| Credential | Bruges til |
|---|---|
| `P-sag - produktion` | SBSYS: `base_url`, `token_url`, `client_id`, `client_secret`, brugernavn og adgangskode |
| `Odense SQL Server` | DWH-opslag og tracking: `server`, `database`, brugernavn og adgangskode |

## Kørsel

```sh
uv run python main.py --queue   # Trin 1: Fyld arbejdskøen
uv run python main.py           # Trin 2: Behandl arbejdskøen
```

## Afhængigheder

| Pakke | Formål |
|---|---|
| `sbsys` | Klient til SBSYS: opslag af sager, erindringer og sagsbehandlere |
| `odk-tools` | Tracking af kørsler og rapportering af manuelle sager |
| `pymssql` | Forbindelse til DWH på SQL Server |

## GDPR og sikkerhed

Robotten behandler følsomme personoplysninger: CPR-numre, fulde navne, tjenestenumre og statsborgerskab. Oplysningerne hentes fra SBSYS og SQL Server under kørslen og gemmes ikke lokalt. Rapporter over manuelt markerede sager er tilgængelige via odk-tools for de medarbejdere, der har adgang til rapporteringsløsningen.
