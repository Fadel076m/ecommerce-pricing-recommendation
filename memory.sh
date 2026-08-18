#!/usr/bin/env bash
# Affiche les 10 derniers commits Git et la dernière entrée du journal de session.
# À lancer en début de session de travail (Claude Code / Codex / manuel).

echo "=== 10 derniers commits ==="
git log --oneline -10 2>/dev/null || echo "(pas encore de commit)"

echo
echo "=== Dernière entrée du journal (.claude/memory/journal.md) ==="
awk '/^## /{p=$0; buf=""; next} {buf=buf"\n"$0} END{print p; print buf}' .claude/memory/journal.md 2>/dev/null | tail -20
