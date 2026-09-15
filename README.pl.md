# LEGAION Verifier — dokumentacja serwera MCP

Zdalny serwer MCP, który sprawdza cytaty prawne w oficjalnych rejestrach, z których powinny pochodzić, i zapisuje, który rejestr był pytany, pod jakim adresem i o której godzinie.

- Adres serwera: `https://mcp.legaion.com` (Streamable HTTP, OAuth 2.1, dynamiczna rejestracja klienta)
- Wpis w rejestrze: `com.legaion/verifier` w [Oficjalnym Rejestrze MCP](https://registry.modelcontextprotocol.io/v0.1/servers?search=com.legaion)
- Strona produktu: https://www.legaion.com
- Wydawca: Aidvocates, Inc. (DBA LEGAION), Nowy Jork · centrum inżynieryjne UE: Katowice

To repozytorium zawiera **wyłącznie dokumentację**: schematy narzędzi, instrukcję podłączenia, opis wyników i listę rzeczy, których serwer nie robi. Kod serwera nie jest otwarty. Katalog [`sygnatury/`](sygnatury/) zawiera niezależny walidator formatu sygnatur polskich orzeczeń na licencji MIT.

## Co robi serwer

Prawnik cytuje przepisy i orzeczenia. Modele językowe produkują cytaty, które wyglądają poprawnie, a bywają zmyślone. LEGAION Verifier bierze dokument, wyodrębnia każde twierdzenie prawne (artykuł ustawy, sygnaturę, tezę) i sprawdza je w źródle, z którego powinno pochodzić: ISAP, SAOS, EUR-Lex oraz rejestry krajowe innych państw UE tam, gdzie istnieje zapytywalne źródło. Każdy werdykt niesie adres rejestru i znacznik czasu faktycznego pobrania — recenzent może powtórzyć sprawdzenie.

Zasada: **żaden cytat nie dostaje statusu „zweryfikowany", dopóki rejestr nie odpowiedział**. Niedostępny rejestr albo cytat nieznany rejestrowi daje `unverified` lub `unknown`, nigdy zielone światło.

## Narzędzia

Pięć narzędzi, wszystkie tylko do odczytu (`readOnlyHint: true`, `destructiveHint: false`). Serwer nie zapisuje w dokumentach użytkownika, nie wysyła poczty i niczego nie zmienia poza opisanym niżej opcjonalnym dopięciem wyniku do sprawy.

| Narzędzie | Do czego | Wymagane |
|---|---|---|
| `verifier_engine` | Weryfikacja cytatów i twierdzeń w dokumencie. Zwraca listę twierdzeń z werdyktami (`verified` / `unverified` / `fabricated` / `unknown`), źródłami (URL rejestru + `fetched_at`), werdykt ogólny i uzasadnienie. | `documentContent` |
| `deep_xray` | Audyt ryzyka umowy, regulaminu lub wzorca konsumenckiego. Ryzyka wg poziomu, statusy klauzul, rekomendacje, wynik liczbowy. Tryb `klauzule_abuzywne` dokłada dopasowania do rejestru UOKiK z numerem wpisu, URL i znacznikiem czasu. | `documentContent` |
| `list_cases` | Sprawy zalogowanego użytkownika, opcjonalnie wg statusu. | — |
| `list_clients` | Klienci zalogowanego użytkownika (firma, osoba, e-mail). | — |
| `whoami` | Id, e-mail i identyfikator klienta OAuth — do sprawdzenia połączenia. | — |

Pełne schematy JSON: [`tools/tools.json`](tools/tools.json). Format wyniku `verifier_engine`: [`docs/verifier-output.md`](docs/verifier-output.md).

`list_cases`, `list_clients` i opcjonalny parametr `caseId` wymagają konta z planem Platforma. `verifier_engine` i `deep_xray` działają na każdym koncie LEGAION, także w planie samego Verifiera.

## Podłączenie

Instrukcje dla Claude (web, desktop, Claude Code), ChatGPT, Cursora i dowolnego klienta obsługującego zdalne serwery MCP z OAuth: [`docs/connect.md`](docs/connect.md).

W skrócie: dodaj `https://mcp.legaion.com` jako zdalny serwer MCP, przejdź logowanie w oknie przeglądarki, wywołaj `whoami`.

## Dane

- Serwer działa w uprawnieniach zalogowanego użytkownika (row-level). Organizacje nie widzą nawzajem swoich spraw, klientów ani wyników.
- Treść dokumentu przekazana do `verifier_engine` lub `deep_xray` jest przetwarzana na potrzeby żądania i **nie jest zapisywana**. Przy podanym `caseId` do sprawy trafia wyłącznie wynik (twierdzenia, werdykty, źródła), nie tekst.
- Rejestry są pytane na żywo; `fetched_at` to czas tego zapytania.
- Szczegóły: https://www.legaion.com/privacy

## Czego nie robi

- Nie ocenia, czy cytat jest *trafny* dla Twojej argumentacji — tylko czy istnieje w rejestrze w cytowanej postaci i czy cytowana treść się zgadza.
- Poza Polską i prawem UE pokrycie zależy od tego, czy rejestr krajowy daje zapytywalne źródło. Gdy nie daje, werdykt to `unknown` z wyjaśnieniem, nie zgadywanie.
- Nie redaguje, nie streszcza, nie przepisuje dokumentów.
- Jest narzędziem dla osoby, która podpisuje pismo. Nie zastępuje jej kontroli.

## Kontakt

- Uwagi do dokumentacji: issue w tym repozytorium.
- Problemy z serwerem, konto: office@aidvocates.com

## Licencja

Dokumentacja: CC BY 4.0. Kod w `sygnatury/`: MIT. Sam serwer LEGAION Verifier jest własnościowy i nie podlega żadnej z tych licencji.
