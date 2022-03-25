# Opdracht 3 van SP
Dit is opdracht 3 van structered programming.

## Business rules voor Recommendation Engine 
Ophalen van data vanuit mongodb en omgezet naar tabellen in postgres, Er kunnen recommendaties worden aangevraagd op 
2 verschillende manieren
- collaborative filtering
- content filtering

### collaborative filtering
Als er naar 2 producten in dezelfde sessie worden bekeken dan kan het gerecommendeerd worden

### content filtering
Als de prijs binnen 20% van de prijs van het originele product ligt en de sub_sub_category hetzelfde is dan is het 
product een kandidaat voor een recommendatie

## producten aanvullen
Als er niet genoeg producten zijn die aan de criteria van 1 van de filterings manieren voldoen dan zal het worden
bijgevuld vanuit de andere manier van recommenderen

## Benodigde niet standaard python libraries
- psycopg2 (voor interactie met de postgres database)
- pymongo (voor interactie met de mongodb database)