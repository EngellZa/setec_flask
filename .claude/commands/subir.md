---
description: Commit + push al fork (Lguribe) y abrir PR hacia el repo original (EngellZa)
argument-hint: "[mensaje del commit opcional]"
allowed-tools: Bash(git:*), Bash(gh:*)
---

Sube los cambios actuales de este repo al fork y abre un Pull Request hacia el original.

Remotos esperados:
- `origin`   → https://github.com/Lguribe/setec_flask.git (fork, aquí se hace push)
- `upstream` → https://github.com/EngellZa/setec_flask.git (original, destino del PR)

Mensaje sugerido por el usuario: $ARGUMENTS

Pasos:

1. Ejecuta `git remote -v`, `git status -sb` y `git diff --stat`. Si los remotos no coinciden con los de arriba, detente y avísame. Si no hay cambios ni commits pendientes de subir, dilo y termina.
2. Ignora las diferencias que sean solo de fin de línea (CRLF por OneDrive/Windows): verifica con `git diff --ignore-cr-at-eol --stat`. No hagas commit de esos archivos. Nunca hagas commit de `.env`, `env/`, `.venv_mac/` ni `.DS_Store`.
3. `git fetch upstream`. Si estás en `main`, crea una rama nueva con un nombre corto y descriptivo en español (p. ej. `articulo-4-biblioteca-vapor`) basada en el estado actual. Si `upstream/main` avanzó, haz rebase de la rama sobre `upstream/main` (si hay conflictos, detente y muéstramelos).
4. Agrega solo los archivos relevantes por nombre (no `git add -A`) y haz commit. Usa el mensaje de $ARGUMENTS si lo hay; si no, redacta uno breve en español que describa el cambio.
5. `git push -u origin <rama>`. Si falla por credenciales, explícame cómo autenticarme (token personal de GitHub o `gh auth login`) y detente.
6. Abre el PR hacia el original:
   - Si `gh` está disponible: `gh pr create --repo EngellZa/setec_flask --base main --head Lguribe:<rama>` con título y descripción en español (qué cambió y cómo probarlo).
   - Si no: dame el enlace `https://github.com/EngellZa/setec_flask/compare/main...Lguribe:setec_flask:<rama>?expand=1` para abrirlo en el navegador, junto con el título y la descripción sugeridos.
7. Al final, resume: rama, commit, enlace del push y enlace del PR. Nunca hagas merge del PR.
