# Prompt de démarrage — à coller dans Claude Code ET Codex

Ce prompt fonctionne pour les deux outils : Claude Code lit `CLAUDE.md` (qui importe `AGENTS.md`), Codex lit `AGENTS.md` directement. Même repo, même contexte, pas de duplication à maintenir.

---

Tu travailles sur le repo `ecommerce-pricing-recommendation`, une plateforme Data-Driven Pricing & Recommandation pour un projet final de Master 2 Big Data. Deadline : dimanche 23/08/2026.

Avant toute chose, lance `./memory.sh` (ou lis `.claude/memory/journal.md`) pour voir où en est le projet, puis lis intégralement `AGENTS.md` (instructions canoniques : stack imposée, règles data, règles ML, règles de code, arborescence, système de mémoire) et `docs/roadmap.md` (jalons datés avec checklist). Lis aussi `docs/data_sources.md` qui documente précisément les données réellement disponibles localement, et `.claude/memory/learnings.md` + `.claude/memory/blockers.md` pour ne pas répéter une erreur déjà rencontrée.

Les deux documents source du brief académique sont dans le dossier parent `Projet Ecommerce` : `Projet Final ISM — Data-Driven Pricing & Recommandation.docx` (spécification technique détaillée, fait foi pour l'architecture) et `Projet Final Gest Projet Data et E-Business.docx` (brief pédagogique d'origine, fait foi pour la grille d'évaluation). Consulte-les si un point du roadmap manque de détail.

Règles de fonctionnement pour cette session :

1. Identifie le jalon en cours dans `docs/roadmap.md` (celui dont la date correspond à aujourd'hui, ou le premier jalon non complété si on a du retard).
2. Avant de coder, reformule en une phrase ce que tu vas livrer pour ce jalon et son critère de validation, pour confirmation.
3. Implémente en respectant strictement les règles de `AGENTS.md` (pas de random split sur données temporelles, pas de mélange de sources, seed=42 pour tout ce qui est synthétique, jamais de credentials en dur).
4. Écris les tests Pytest correspondants quand le jalon en prévoit (data quality, API, pricing, recommendation, transformations).
5. Si tu bloques plus de 15 minutes sur un point non essentiel (ex. configuration Airflow/Kafka), applique l'ordre de priorité de `docs/roadmap.md` ("Rappel — en cas de retard") et signale-le plutôt que de t'enliser — les trois modèles et le dashboard ne doivent jamais être sacrifiés pour de l'infrastructure avancée.
6. Ne traite jamais les résultats du pricing ou du forecasting comme des vérités absolues dans les commentaires, la doc ou les messages de commit — toujours formuler "sous les hypothèses du modèle".
7. Une fois le jalon terminé et vérifié : coche les cases correspondantes dans `docs/roadmap.md`, applique le rituel de clôture de `AGENTS.md` section 7 (décidé / appris / bloqué / entrée journal.md), propose les entrées mémoire correspondantes pour validation, puis propose un message de commit.

Commence par me dire quel jalon tu identifies comme jalon du jour, et ce que tu comptes livrer avant de te lancer.

---

## Astuce d'usage à deux outils

Pour paralléliser Claude Code et Codex sans qu'ils se marchent dessus sur le même repo local, le plus simple en solo est de les faire travailler en séquence sur des jalons différents plutôt qu'en simultané sur les mêmes fichiers (ex. Claude Code sur Jalon 5 pendant que tu prépares en tête le Jalon 6, puis bascule sur Codex pour relire/tester ce que Claude Code vient de produire). Utiliser l'un en écriture et l'autre en revue de code fonctionne bien : demander à Codex "relis ce que Claude Code vient de produire pour le Jalon X, vérifie la conformité à AGENTS.md" est un bon réflexe avant chaque commit de jalon.
