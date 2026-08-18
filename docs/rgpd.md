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
