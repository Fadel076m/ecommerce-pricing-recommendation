# RGPD et protection des données

Principes à respecter (brief section 28) :

- Minimisation des données
- Pseudonymisation des identifiants clients (customer_id ne doit jamais être un identifiant réel identifiant)
- Contrôle d'accès (credentials R2/Postgres uniquement en `.env`, jamais commités)
- Limitation de conservation
- Sécurité (voir `.gitignore`, `.env.example`)
- Documentation des sources (voir `docs/data_sources.md`)
- Absence de données personnelles directement identifiantes dans le prototype

Les customer_id d'UCI Online Retail II sont déjà anonymisés (identifiants numériques). Les visitorid de RetailRocket et household_key de Dunnhumby sont également des identifiants anonymisés par les fournisseurs de données — à documenter comme tel.

## Limitation de conservation — politique retenue

- Aucune donnée personnelle directement identifiante n'est collectée par le projet (pas de nom, email, adresse) : les trois sources publiques ne fournissent que des identifiants déjà anonymisés par leur éditeur.
- Portée du projet : prototype académique (Master 2), pas de mise en production ni de traitement de données réelles de personnes vivantes identifiées. Durée de conservation = durée du projet (jusqu'au 23/08/2026) puis dépôt académique ; pas de politique de purge automatisée nécessaire à ce stade.
- Si le projet devait être opérationnalisé au-delà du cadre académique, une durée de conservation explicite (ex. 24 mois glissants pour l'historique transactionnel) devrait être définie et documentée avant toute mise en production — hors périmètre du MVP.
