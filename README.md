# Lectio API

## Introduction

Lectio is a digital system used by the danish gymnasiums for everything from contacting the teachers (and management) to seeing your homework and school schedule for the next day. As this information is quite nice to have easily accessible on a day to day basis, it is quite a shame that there no longer exists a public accessible API nor a free and opensource app for Lectio, which is (partly) what this project is aiming at providing. A few years back there where a few API's written in PHP, but as Lectio stopped providing information without logging in, these have been non-functional the last years and while the [Lectio changelog](https://www.lectio.dk/lectio/3/versioninfoold.aspx) does mention an (presumably official) API for the first time the 30JAN2019, it is - as far as I and everyone potentially knowledgeable on this topic - not publicy accessible.

While I would argue that the codebase for this project is quite robust and tested, I unfortunately only have access to Lectio for a single danish gymnasium (Bagsværd Kostskole og Gymnasium) so if you're a danish student at some other gymnasium and you would like to help test the project, feel free to reach out either through Github, or by one of the contact methods listed on [my profile](https://github.com/bertmad3400)

## Andvendelse - Guide
Desværre har Lectio - som tidligere nævnt - over de sidste par år begrænset den information du kan få fra Lectio uden at være logget ind markant, hvilket betyder at alle API's der vil have et håb om stadig at fungere bliver nødt til at håndtere de cookies Lectio returnere når man logger ind. Det gør den her API også (det er faktisk en af de markante fordele ved denne API, den håndtere rigtig meget state-management selv, hvilket betyder at man bare skal logge ind, og modtager man på et tidspunkt en HTTP 401 respons skal man bare logge ind igen), og det håndtere rigtig meget af det information der kommer fra Lectio for dig, men du kommer desværre ikke helt udenom nogen form for authentication. Det betyder at denne API også returnere en cookie, hvilket naturligvis er bedre end de 8 der kommer fra Lectio's ASP.NET backend, men du skal stadig være i stand til at håndtere den ene cookie på en hensigtsmæssig måde, for at få denne API til at virke.

Hvordan man gør er forskelligt fra person til person, og variere meget alt efter hvilke sprog du benytter, men jeg kan give dig nogle forslag. Da det er en API - og den derfor er designet til at blive interageret med fra andre programmer - ville det oplagte være at benytte et session objekt som de blandt andet findes i [Pythons Requests bibliotek](https://2.python-requests.org/en/master/user/advanced/). Dette er faktisk også hvad der bliver benyttet i backenden og gør det utroligt simpelt at have med session data at gøre.

Da du kun modtager en cookie som er statisk (indtil du efterspørger en nye) er muligheden der også for manuelt at notere værdien af cookien (den hedder "LectioAPI-ID"), gemme den lokalt og manuelt vedhæfte den ved fremtidige efterspørgsler. Dette er ikke lige så simpelt som den tidligere beskrevet metode, men det er stadig relativt lige ud af landevejen og burde ikke være problematisk.

### Disclaimer - Advarsel
Dette projekt er fuldt self-contained, og består både af en backend og en frontend. Selve backenden kan du godt benytte alene uden frontend (det kan give dig noget mere kontrol), men jeg ville andbefale at benytte frontenden i kombination med den, da den også består af noget state-management, nogler wrappers, og generelt andre ting der gør dit liv som udvikler (eller bare normal person) markant nemmere.

Hvordan du så skal anvende den API er det der kan være kritisk. Du kan anvende den ved lokalt at køre selve flask-frontenden på din egen maskine (jeg håber det køre på Windows, har kun testet det på Linux so far), eller du kan benytte den version af API'en jeg hoster på [https://bertmad.dk/api/lectio/](https://bertmad.dk/api/lectio/). Sidstenævnte er hvad resten af denne guide kommer til at tage udgangspunkt i (da det er en simplere tilgang), men du skal være opmærksom på at det desværre heller ikke er risikofrit. Selvom din forbindelse til min API burde være sikker (HTTPS med HSTS headers), er der altid en række risiko når først dine credentials. Selvom at den nuværende kode i dette repo gemmer ikke password og brugernavne i cleartext form på disken, men kun i memory, så er der desværre ikke nogen måde for dig at verificere at det faktisk er den version af softwaren jeg køre, og selvom at jeg selvfølgelig ikke har nogen intentioner om at snage i dine sager, er sandheden at du nok ikke skal stole på en fremmede på internettet.

Ydermere er der også den ene ting at den nuværende version af denne API **gemmer et SHA256 hash af en streng der er en kombination af dit brugernavn og password på disken** (i en SQLite3 database). Selvfølgelig har jeg sørget for at tage de rigtige forholdsregler mod SQL injection samt at sikre file permissions på DB filen, men skulle der være et breach (hvilket dog er usandsynligt) er der ikke en stor, men bestemt tilstedeværende risiko for at dit password ville blive lækket. Som nævnt tidligere skal du være velkommen til at benytte min hostede version af API'en, men du skal bare også være opmærksom på den dertilhørende risiko. Med det ude af vejen kan vi fortsætte til den egentlige guide:

### Gymnasium-nummer
Det første du skal finde er dit gymnasium-nummer. Alle gymnasier på Lectio har internt et nummer fra 1-20200992 (ikke at der er så mange gymnasier på Lectio, tror bare udvikleren har haft svært ved at tælle) forbundet med deres navn, og du kan finde dit ved at navigere til [/gymnasieList/](https://bertmad.dk/api/lectio/gymnasieListe/) i din browser og søge efter navnet på dit gymnasium. Dette er det første og sidste sted i denne guide hvor det giver mening at benytte din browser.

### Login
Det næste på programmet er at få dig logget ind. Dette gøres ved sende en POST request til [/login/](https://bertmad.dk/api/lectio) med følgende oplysninger:

```
{
	"gymnasiumNumber" : [gymnasium-nummer],
	"username" : [brugernavn],
	"password : [password]
}
```

Dette kan gøres med følgende python kode:

```
import requests, json
data = {
	"gymnasiumNumber" : [gymnasium-nummer],
	"username" : [brugernavn],
	"password : [password]
}
with requests.session() as sess:
	sess.post("https://bertmad.dk/api/lectio/login/", data=json.dumps(data))
```

Dette vil så give dig et session objekt du kan bruge til resten af indholdet af denne API (hvor det er krævet at du er logget ind), eller du kan benytte ```sess.cookies.get_dict()``` til at finde det ID som API'en har tildelt dig og manuelt vedhæfte det til fremtidige forgspørgsler.

### Hente information
Nu hvor du er logget ind, er der ingen grænser for hvad du kan benytte denne API til (eller næsten i hvert fald, jeg har som udvikler også et begrænset antal timer jeg kan dedikere til et sideprojekt). De følgende routes er URI'er på API som du kan benytte til at forespørge information:

#### [/opgaveListe/[årstal]](https://bertmad.dk/api/lectio/opgaveList/)
På denne route kan du få listet alle de afleveringer du har og har haft i et givent år. For alle routes hvor der specificeres et årstal gælder det at hvis der gives et årstal hvor du ikke er registreret i Lectio, vil Lectio (og derigennem API'en) bare returnere resultater for det årstal som er tættest på hvor du er registreret.

#### [/lektieListe/](https://bertmad.dk/api/lectio/lektieListe/)
På denne route vil du få listet de lektier du har for i den nære fremtid. Da Lectio (og derfor også den API) kun lister lektier kort ud i fremtiden, er der ikke nogen grund til at specificere et tidsrum.

#### [/beskedListe/[beskedClass]/[årstal]/](https://bertmad.dk/api/lectio/beskedListe/)
På denne route kan du få listet en oversigt over beskeder fra forskellige kategorier og forskellige årstal. Hvis der er så mange beskeder i en kategori at der er mere end en side, listes de alle samme. De forskellige kategorier er som følger:

```
beskedClasses = {
		"nyeste"
		"ulæste"
		"flag"
		"slettede"
		"egne"
		"sendte"
		"hold"
		"indbyggedegrupper"
		"egnegrupper"
	}
```

Udover bare besked-titlerne og andre detaljer, returneres der også et ID for hver besked. Dette kan bruges i næste route.

#### [/beskedIndhold/[beskedID]/](https://bertmad.dk/api/lectio/beskedIndhold/)
På denne route kan indholdet af individuelle beskeder returneres som en nestet JSON struktur der repræsentere hvem der svarede hvem vist visuelt på Lectio. beskedID er det ID som du fandt i den tidligere route.

#### [/skema/[year]/[week]/](https://bertmad.dk/api/lectio/skema/)
På denne route kan indholdet af dit skema for en given uge i et givent år. Hvis du indtaster en uge som ikke findes i systemet vil den retunere en 400 respons som lyder "Error scraping the page, please check your request"

#### Fremtidige routes
Udover disse routes er der også planer om at implementere routes for følgende funktioner (engang i fremtiden):

- Fravær
- Dokumenter
- Karakterer
