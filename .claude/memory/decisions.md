---
type: decisions
project: ecommerce-pricing-recommendation
---

# Décisions structurantes (BDR)

| ID | Date | Titre | Statut |
|---|---|---|---|
| BDR-001 | 2026-08-18 | ISM fait foi pour la technique, Gest Projet pour l'évaluation | actif |
| BDR-002 | 2026-08-18 | Trois sources data uniquement (UCI, RetailRocket, Dunnhumby), Olist écarté | actif |
| BDR-003 | 2026-08-18 | M5 non téléchargée, écartée volontairement | actif |
| BDR-004 | 2026-08-19 | Airflow isolé dans `requirements-airflow.txt`, installé séparément avec contraintes officielles | actif |

## BDR-001 — ISM fait foi pour la technique, Gest Projet pour l'évaluation

**Date** : 2026-08-18
**Décision** : le document "Projet Final ISM — Data-Driven Pricing & Recommandation" est la référence pour tous les choix d'architecture et la stack technique. Le document "Projet Final Gest Projet Data et E-Business" reste la référence pour la grille d'évaluation académique (gouvernance 15%, architecture 20%, modèles 25%, intégration 15%, business 15%, présentation 10%).
**Pourquoi** : les deux documents décrivent le même projet mais le premier est une version déjà tranchée (stack figée, jalons datés, ordre de priorité), le second est le brief générique d'origine avec plusieurs options laissées ouvertes.
**Alternatives considérées** : suivre uniquement le brief générique (rejeté — trop d'ambiguïté technique pour tenir 6 jours) ; fusionner les deux sans hiérarchie (rejeté — risque d'incohérence entre choix techniques).
**Statut** : actif.

## BDR-002 — Trois sources data uniquement, Olist écarté

**Date** : 2026-08-18
**Décision** : n'utiliser que UCI Online Retail II, RetailRocket et Dunnhumby Complete Journey. Le dataset Olist (téléchargé mais absent des deux briefs) n'est pas intégré au MVP.
**Pourquoi** : le brief interdit explicitement de mélanger des sources hétérogènes sans modèle de données cohérent (section 13 du brief ISM). Olist n'a pas d'identifiants ni de période compatibles avec les trois sources prescrites.
**Alternatives considérées** : utiliser Olist en remplacement d'une des trois sources prescrites (rejeté — non conforme au brief) ; l'intégrer comme quatrième source (rejeté — risque de confusion, hors périmètre noté).
**Statut** : actif — à révision seulement si le temps permet un enrichissement bonus après le Jalon 9.

## BDR-003 — M5 non téléchargée, écartée volontairement

**Date** : 2026-08-18
**Décision** : ne pas télécharger ni utiliser le dataset M5 (Walmart), présenté comme référence forecasting optionnelle dans le brief.
**Pourquoi** : gain de temps sur un délai de 6 jours, la source est explicitement facultative dans le brief.
**Alternatives considérées** : l'intégrer comme benchmark séparé (rejeté pour l'instant, faute de temps).
**Statut** : actif.

## BDR-004 — Airflow isolé de `requirements.txt`

**Date** : 2026-08-19
**Décision** : retirer `apache-airflow` de `requirements.txt` principal, le déplacer dans `requirements-airflow.txt` avec un exemple d'installation utilisant le fichier de contraintes officiel Airflow (`--constraint https://raw.githubusercontent.com/apache/airflow/constraints-X.Y.Z/constraints-3.11.txt`).
**Pourquoi** : un `pip install -r requirements.txt` incluant `apache-airflow>=2.9` non contraint est resté bloqué plusieurs heures (voir LRN-002) — le resolver pip tente de concilier l'immense arbre de dépendances d'Airflow avec fastapi/pydantic/prophet du reste du projet. Airflow est de toute façon explicitement sacrifiable en premier (AGENTS.md §9, roadmap "Rappel — en cas de retard").
**Alternatives considérées** : figer une version précise d'Airflow dans le même fichier (rejeté — le conflit vient de la combinaison avec les autres paquets, pas seulement de la version) ; abandonner Airflow entièrement (rejeté — encore possible si le temps le permet en fin de projet, Jalon 10).
**Statut** : actif.
