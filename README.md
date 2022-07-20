IPP - Principy programovacích jazyků 2019/2020
---

##Ciele
Hlavnym cielom bolo vytvorenie programu na interpretáciu XML kódu, ktorý sme dostali ako výstup z parse.php upravou zdrojoveho kodu IPPcode20.
Správne fungovanie implementácie parse.php a interpret.py sa skúša pomocou testovacieho skriptu test.php.
K zadaniu je potrebne vytvorit programovu dokumentaciu s blizsimi specifikaciami implementacie. 


##interpret.py
Interpret ako druhá časť projektu, pracuje s výstupným kódom získaným programom parse.php upravený vo formáte XML.
Pri spustení programu sa vykoná kontrola zadaných argumentov a ich správne priradenie vstupného suboru alebo standardneho vstupu potrebného pre program. 
V programe sa využíva ElementTree na skontrolovanie a upravenie vstupneho xml kodu do vhodnej podoby.

Zo zadanej reprezentácie kódu sa vytvorí slovník, ktorý prejde kontrolou a výsledok uloží do pola, s ktorým sa následne pracuje.
Program ďalej skontroluje pomocou regexov správnosť formátov zadaných príkazov. 
Na základe poradia zadaného užívatelom pomocou order sa výsledný kod interpretuje. 

Hlavné vykonávanie funkcii programu sa rieši vo funkcii codeInterpret pomocou vytvoreného automatu.
Zložitejšie implementovatelné funkcie programu su riešené v samostatných funkciách. Pri práci s premennými bolo treba implementovať zásobník, ktorý pracoval s 3 možnými rámcami: 
#####•globálny rámec
#####•lokálny rámec
#####•dočasný rámec
Každý rámec združuje dokopy premenné a ich hodnoty. Globálny rámec slúži na ukladanie globálnych premien a ich vytváranie, na začiatku je však prázdny. 
Lokálny rámec slúži na ukladanie lokálnych premien. Dočasný rámec sa využíva pri práci s rámcami. Slúži na ich vytváranie a aj rušenie. Dočasný rámec sa dokáže stať lokálnym rámcom.

Povolenie je tiež zadanie argumentu --help, ktorý vypíše dodatočné informácie programu.
Na správne vykonávanie aritmetických operácii programu som vytvoril funkciu na aktualizovanie uloženej hodnoty premennej. 
Program vykoná celkovo 4 hlavné úpravy kódu, v ktorých prebehne lexikálna aj syntaktická kontrola kodu.


#####Implementácia
Implementácia programu bola postupná. Program som prisposoboval formatom testov, ktore mi pomohli pri ošetrovani hraničných prípradoch, ktoré bolo ošetriť pre správnu funkčnosť programu interpret.py. 

Na testovanie som použil provizórny testovací skript test.php, ktorý sa mi pre časové obmedzenie nepodarilo dokončiť do dostatočnej podoby. Pri testovaní som bol tiež čiastočne obmedzený neúplným ošetrením programu parse.php.


