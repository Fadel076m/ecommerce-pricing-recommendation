---
type: blockers
project: ecommerce-pricing-recommendation
---

# Frictions & blocages (BLK)

| ID | Date | Résumé | Statut |
|---|---|---|---|
| BLK-001 | 2026-08-18 | Page Notion de setup initialement inaccessible (connecteur non autorisé) | résolu |

## BLK-001 — Page Notion de setup initialement inaccessible

**Date** : 2026-08-18
**Friction** : la page Notion "Setup projet dev web/mobile/Data/IA avec Claude Code" était inaccessible en début de session (connecteur Notion sans les droits sur ce workspace).
**Cause réelle** : accès non encore accordé côté utilisateur au moment du premier essai.
**Solution** : l'utilisateur a accordé l'accès en cours de session ; les pages Fondations transverses, Setup Data et Setup Multi-Domaine ont ensuite été lues et intégrées (système de mémoire `.claude/memory/`, conventions d'environnement, recommandations MCP/sécurité).
**Statut** : résolu.
