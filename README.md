# Kontrol af opholds- og arbejdstilladelse

Robotten kontrollerer løbende at medarbejdere med opholds- og arbejdstilladelse i SBSYS har en gyldig erindring på sagen, og at erindringen er tildelt den rette sagsbehandler.

## Hvad gør robotten?

1. For hvert arbejdselement (medarbejder) slås den tilhørende opholdssag op i SBSYS via medarbejderens tjenestenummer og CPR-nummer (sagsskabelon 3127, kun aktive sager).
2. Hvis ingen sag findes, markeres medarbejderen til manuel behandling med årsagen *"Arbejds- og opholdssag kunne ikke findes på medarbejder for givet tjenestenr"*.
3. Erindringer på sagen gennemgås — kun erindringer med *"opholds- og arbejdstilladelse"* i navnet og en frist mere end 14 dage frem i tiden medtages.
4. Hvis ingen matchende erindring findes, markeres sagen til manuel behandling: *"Ingen arbejds- og opholdserindring fundet på sagen"*.
5. Hvis mere end én matchende erindring findes, markeres sagen til manuel behandling: *"Mere end én arbejds- og opholdserindring erindring fundet på sagen"*.
6. Hvis erindringsansvarlig ikke stemmer overens med sagsbehandleren på sagen, opdateres erindringen automatisk med den korrekte sagsbehandler.
7. Hvis opdateringen fejler, markeres sagen til manuel behandling med fejldetaljerne.
8. Alle manuelt markerede sager rapporteres via odk-tools under nøglen `kontrol-af-opholds-og-arbejdstilladelse` med CPR-nummer, navn, tjenestenummer og årsag.

## Forudsætninger

- Python ≥ 3.13
- [`uv`](https://docs.astral.sh/uv/) til pakkehåndtering
- Adgang til **Automation Server** (arbejdskø)
- Adgang til **SBSYS**
- Adgang til **Odense SQL Server**

## Installation

```sh
uv sync
```

## Konfiguration

Credentials registreres i Automation Server:
- `P-sag - produktion`
- `Odense SQL Server`

| Miljøvariabel | Beskrivelse |
|---|---|
| `ATS_URL` | URL til Automation Server API |
| `ATS_TOKEN` | Bearer token til Automation Server |
| `ATS_WORKQUEUE_OVERRIDE` | Tilsidesæt arbejdskø-ID (valgfri) |

## Kørsel

```sh
uv run python main.py --queue   # Fyld arbejdskøen
uv run python main.py           # Behandl arbejdskøen
```

## Afhængigheder

| Pakke | Formål |
|---|---|
| `automation-server-client` | Klient til Automation Server — styrer arbejdskøer og arbejdselementer |
| `odk-tools` | Sporing og rapportering af manuelle sager og kørselsstatistik |
| `sbsys` | Klient til SBSYS — opslag af sager, erindringer og sagsbehandlere |

## GDPR og sikkerhed

Robotten behandler følsomme personoplysninger: CPR-numre, fulde navne, tjenestenumre og statsborgerskab. Oplysningerne hentes fra SBSYS og SQL Server under kørslen og gemmes ikke lokalt. Rapporter over manuelt markerede sager er tilgængelige via odk-tools for de medarbejdere, der har adgang til rapporteringsløsningen.
