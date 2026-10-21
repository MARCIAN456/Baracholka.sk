# Semestrálny projekt - Programovanie v Pythone

**Študent:** Markiian Liashkevych  
**Názov projektu:** Baracholka.sk – Inzertný portál a bazár (REST API)

Podrobné a aktuálne znenie zadania je na stránke predmetu:  
https://marek-horvath.github.io/python/projekt/

## Zadanie

Navrhnite a implementujte vlastný individuálny projekt v jazyku Python. Téma je voľná, projekt však musí riešiť konkrétny problém alebo poskytovať ucelenú funkcionalitu.

Projekt musí zmysluplne kombinovať minimálne **3 technologické oblasti**, napríklad:

- skriptovanie, súbory alebo automatizácia;
- GUI alebo webové používateľské rozhranie;
- HTTP a externé API;
- databáza;
- spracovanie alebo vizualizácia dát;
- web scraping alebo automatizácia prehliadača;
- web backend;
- iná primeraná Python technológia.

Samotný import knižnice sa nepočíta. Každá zvolená technológia musí riešiť reálnu časť projektu.

## Míľniky a hodnotenie

| Časť | Termín | Body |
| --- | --- | ---: |
| MVP - prvá funkčná verzia | 6. týždeň semestra | 30 |
| Finálna aplikácia | 11.-13. týždeň semestra | 40 |
| Technická dokumentácia PDF | finálne odovzdanie | 20 |
| Približne 5-minútové video | finálne odovzdanie | 10 |
| **Spolu** | | **100** |

MVP musí obsahovať reálny spustiteľný kód a základ hlavnej funkcionality. Nestačí prázdna štruktúra, mockup ani dokument s návrhom.

## Požadovaný obsah repozitára

- zdrojový kód rozdelený do zmysluplných modulov;
- tento `README.md` doplnený o informácie o projekte;
- `pyproject.toml` alebo `requirements.txt`;
- `.gitignore`;
- `.env.example`, ak projekt používa konfiguračné premenné;
- testy primerané typu projektu;
- potrebné assets alebo malé datasety;
- finálna technická dokumentácia v PDF, odporúčane v rozsahu približne 10-15 strán.

Video necommitujte ako veľký binárny súbor do Git repozitára. Spôsob jeho odovzdania bude oznámený samostatne.

## Pravidlá práce

- Commitujte priebežne. Jeden veľký commit na konci sa nepovažuje za priebežnú prácu.
- Projekt musí byť možné spustiť na inom počítači podľa návodu v README.
- Necommitujte heslá, API kľúče, tokeny, osobné dáta ani obsah súboru `.env`.
- Nepoužívajte hardcoded absolútne cesty závislé od vášho počítača.
- Ošetrite neplatné vstupy a bežné chybové situácie.
- Uprednostnite menší funkčný a kvalitný projekt pred veľkým nefunkčným riešením.

## Použitie AI

AI nástroje sú povolené. Za celý odovzdaný projekt však zodpovedáte vy. Musíte rozumieť použitému kódu, vedieť ho vysvetliť, upraviť a obhájiť svoje technické rozhodnutia.

Výraznejšie použitie AI, externých šablón, tutoriálov alebo prevzatého kódu uveďte v dokumentácii. Nepochopenie podstatnej časti riešenia môže viesť k bodovej penalizácii alebo k nesplneniu podmienok predmetu.

## Výskumné spracovanie

Odovzdaný projekt môže byť použitý na pedagogický alebo vedecký výskum. Pred spracovaním budú odstránené priame identifikátory študenta a výsledky budú prezentované iba v anonymizovanej alebo súhrnnej podobe.

---

## O projekte

### Krátky popis

**Baracholka.sk** je moderný inzertný portál (internetový bazár) pre nákup a predaj tovaru z druhej ruky, inšpirovaný platformami ako Bazoš alebo OLX. 
Projekt v aktuálnej fáze MVP poskytuje robustné, bezpečné a kontajnerizované REST API pre správu používateľských účtov, autentifikáciu a kompletnú inzerciu tovaru s autorizáciou na úrovni vlastníka.
### Čo projekt rieši

Aplikácia rieši bezpečný a štruktúrovaný predaj použitých vecí:
- Umožňuje používateľom jednoduchú registráciu a prihlásenie s bezpečným ukladaním hesiel.
- Zabezpečuje prehliadanie ponuky tovaru so stránkovaním (pagináciou), aby sa predišlo preťaženiu databázy pri veľkom počte záznamov.
- Rieši ochranu dát pred neoprávnenou úpravou (len vlastník inzerátu má právo meniť jeho údaje alebo ho vymazať).

### Aktuálna funkcionalita (MVP)
- **Autentifikácia a používatelia:**
    - Registrácia nového používateľa s validáciou emailu (`EmailStr`) a minimálnej dĺžky hesla.
    - Bezpečné prihlasovanie cez OAuth2 Password Flow s generovaním JWT prístupových tokenov.
    - Šifrovanie hesiel pomocou algoritmu `bcrypt` s automatickou soľou.
    - Získanie profilu prihláseného používateľa (`/api/v1/user/me`).
- **Inzercia tovaru (Items CRUD):**
    - Vytvorenie nového inzerátu s automatickým priradením k prihlásenému používateľovi.
    - Stránkovaný zoznam aktívnych inzerátov (`GET /api/v1/items/?page=1&size=10`) s metadátami o celkovom počte strán.
    - Detail inzerátu vrátane vnorených informácií o predajcovi.
    - Čiastočná úprava údajov inzerátu (`PATCH`), napr. zmena ceny alebo popisu.
    - Bezpečné zmazanie inzerátu (`DELETE`) iba autorom inzerátu.
- **Automatizácia a infraštruktúra:**
    - Automatická správa a verzovanie databázovej schémy pomocou **Alembic** migrácií.
    - Skript pre generovanie realistických počiatočných dát (`seed.py`).
    - Kompletná kontajnerizácia v **Docker & Docker Compose** (izolovaná databáza PostgreSQL + FastAPI s healthcheckom).
### Plánovaná funkcionalita (do finálnej verzie)

- Vyhľadávanie inzerátov podľa kľúčových slov v názve a popise.
- Filtrovanie podľa cenového rozpätia (od - do) a kategórií tovaru (elektronika, nábytok, oblečenie atď.).
- Možnosť nahrávania a správy fotografií k inzerátom.
- Implementácia integračných testov (pytest) pre overenie API
- **Integrácia platobného servisu (Platobná brána):**
    - Napojenie na externú platobnú bránu (napr. Stripe / GoPay API) pre bezpečné online platby kartou.
    - Spracovanie webhooks pre overenie úspešnosti platby a zmenu stavu objednávky.
- **Integrácia doručovacieho servisu (Packeta API):**
    - Prepojenie s externým logistickým API služby Packeta (Zásielkovňa) pomocou HTTP klienta `httpx`.
    - Možnosť výberu doručenia do výdajného miesta alebo samoobslužného Z-BOXu.
    - Automatické generovanie údajov k zásielke a výpočet ceny dopravy.
- **Manažment objednávok (Order Management):**
    - Prepojenie platby, dopravy a inzerátu do uceleného nákupného procesu (`Order` model so stavmi: `CREATED` -> `PAID` -> `SHIPPED` -> `DELIVERED`).
- **Rozšírené vyhľadávanie a kategórie:**
    - Vyhľadávanie inzerátov podľa kľúčových slov a filtrovanie podľa kategórií tovaru.

### Použité technologické oblasti

1. **Web backend (FastAPI, Pydantic v2):**
    - Využitie moderného asynchrónneho frameworku FastAPI pre tvorbu prehľadného REST API s automatickou interaktívnou dokumentáciou (Swagger / OpenAPI).
    - Dôsledná validácia a serializácia vstupných aj výstupných údajov prostredníctvom Pydantic schém.
2. **Databázy (PostgreSQL, SQLAlchemy 2.0, Alembic):**
    - Relačný návrh databázy s viacerými entitami (`User` a `Item`), väzbou 1:N (jeden používateľ má viacero inzerátov) a kaskádovým mazaním (`CASCADE`).
    - Použitie pokročilého ORM SQLAlchemy 2.0 na ochranu pred SQL Injection a automatické verzovanie schémy cez migračný nástroj Alembic.
3. **Skriptovanie a automatizácia (Docker Compose, Seed skript):**
    - Orchestrácia infraštruktúry cez Docker Compose s definovaným poradím spúšťania a `healthcheck` mechanizmom pre PostgreSQL.
    - Automatizovaný skript `seed.py` na naplnenie databázy 25+ reálnymi inzerátmi pre okamžité testovanie.
4. **HTTP, bezpečnosť a autentifikácia (PyJWT, Passlib/Bcrypt):**
    - Implementácia bezstavovej autentifikácie pomocou štandardu JSON Web Tokens (JWT) s časovou expiráciou a kontrolou oprávnení na úrovni endpointov.

## Inštalácia a spustenie


Projekt má pripravenú kompletnú orchestráciu, takže na spustenie stačí mať nainštalovaný Docker:
1. Skopírujte šablónu premenných prostredia:
   ```bash
   cp .env.example .env
   ```
2. Zostavte a spustite celú aplikáciu (databázu aj API s automatickými migráciami):
    ```bash
   docker compose up --build
    ```
3. Aplikácia bude dostupná na http://localhost:8000.

## Základné použitie

### Typický používateľský scenár:

1. **Registrácia:** Otvorte endpoint `POST /api/v1/auth/register`, zadajte meno, email a heslo a odošlite požiadavku na vytvorenie účtu.
2. **Prihlásenie cez ikonu zámku (Authorize):**
    * V pravom hornom rohu (alebo priamo pri ktoromkoľvek chránenom endpointe) kliknite na **ikonu zámku 🔓 (Authorize)**.
    * Do poľa `username` zadajte svoj zaregistrovaný email a do poľa `password` svoje heslo.
    * Kliknite na tlačidlo **Authorize**. Swagger UI na pozadí automaticky odošle požiadavku na `/api/v1/auth/login`, prevezme JWT token a zapamätá si ho pre všetky vaše ďalšie volania API.
3. **Overenie profilu:** Vykonajte požiadavku na `GET /api/v1/user/me` — endpoint vám okamžite vráti údaje o vašom prihlásenom profile.
4. **Vytvorenie inzerátu:** Pošlite `POST` na `/api/v1/items/create-item` (názov, popis a cena) — systém automaticky priradí inzerát k vášmu prihlásenému účtu.
5. **Prehliadanie inzerátov:** Odošlite `GET` na `/api/v1/items/?page=1&size=10` pre zobrazenie verejnej ponuky tovarov so stránkovaním.
6. **Úprava a mazanie:** Vyskúšajte `PATCH` na `/api/v1/items/update-item/{id}` alebo `DELETE /api/v1/items/{id}` — systém automaticky overí, že ste skutočným autorom daného inzerátu.

## Zdroje a použité nástroje

1. FastAPI Documentation: https://fastapi.tiangolo.com/
2. SQLAlchemy 2.0 Documentation: https://docs.sqlalchemy.org/
3. Alembic Documentation: https://alembic.sqlalchemy.org/
4. Docker & Docker Compose Guides: https://docs.docker.com/
5. AI asistent (Antigravity): Použitý na konzultáciu architektúry, ladenie chybových stavov pri serializácii Pydantic schém
