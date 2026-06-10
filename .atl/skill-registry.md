# Skill Registry

**Delegator use only.** Any agent that launches sub-agents reads this registry to resolve compact rules, then injects them directly into sub-agent prompts. Sub-agents do NOT read this registry or individual SKILL.md files.

**Project**: activia-trace
**Generated**: 2026-06-09

---

## User Skills

| Trigger | Skill | Path |
|---------|-------|------|
| Creating CRUD page in Dashboard sub-project | dashboard-crud-page | `.agents/skills/dashboard-crud-page/SKILL.md` |
| Adding HelpButton or creating Dashboard page | help-system-content | `.agents/skills/help-system-content/SKILL.md` |
| Creating component libraries, design systems | tailwind-design-system | `.agents/skills/tailwind-design-system/SKILL.md` |
| Building knowledge base from scratch or docs | kb-creator | `.agents/skills/kb-creator/SKILL.md` |
| Implementing tasks from a change | openspec-apply-change | `.claude/skills/openspec-apply-change/SKILL.md` |
| Archiving a completed change | openspec-archive-change | `.claude/skills/openspec-archive-change/SKILL.md` |
| Exploring ideas, investigating problems | openspec-explore | `.claude/skills/openspec-explore/SKILL.md` |
| Proposing a new change with artifacts | openspec-propose | `.claude/skills/openspec-propose/SKILL.md` |
| Creating AGENTS.md / CLAUDE.md for project | agents-md-generator | `~/.config/opencode/skills/agent-instruction/SKILL.md` |
| Finding a skill for a task | find-skills | `~/.config/opencode/skills/find-skill/SKILL.md` |
| Writing Go tests, teatest usage | go-testing | `~/.config/opencode/skills/go-testing/SKILL.md` |
| Creating GitHub issues (bug/feature) | issue-creation | `~/.config/opencode/skills/issue-creation/SKILL.md` |
| Creating pull requests | branch-pr | `~/.config/opencode/skills/branch-pr/SKILL.md` |
| Running project foundation flow | jr-orchestrator | `~/.config/opencode/skills/jr-orchestrator/SKILL.md` |
| Running adversarial dual review | judgment-day | `~/.config/opencode/skills/judgment-day/SKILL.md` |
| Creating technical design documents | openspec-design | `~/.config/opencode/skills/openspec-design/SKILL.md` |
| Initializing OPSX in a project | openspec-init | `~/.config/opencode/skills/openspec-init/SKILL.md` |
| Guided OPSX walkthrough | openspec-onboard | `~/.config/opencode/skills/openspec-onboard/SKILL.md` |
| Writing change specifications | openspec-spec | `~/.config/opencode/skills/openspec-spec/SKILL.md` |
| Creating implementation task checklists | openspec-tasks | `~/.config/opencode/skills/openspec-tasks/SKILL.md` |
| Verifying implementation vs plan | openspec-verify | `~/.config/opencode/skills/openspec-verify/SKILL.md` |
| Generating CHANGES.md roadmap | roadmap-generator | `~/.config/opencode/skills/roadmap-generator/SKILL.md` |
| Creating or editing agent skills | skill-creator | `~/.config/opencode/skills/skill-creator/SKILL.md` |

---

## Compact Rules

Pre-digested rules per skill. Delegators copy matching blocks into sub-agent prompts as `## Project Standards (auto-resolved)`.

### dashboard-crud-page
- Hook Trio obligatorio: `useFormModal<FormData, Entity>` (no raw useState), `useConfirmDialog<Entity>`, `usePagination(sortedItems)`
- HelpButton MANDATORIO en toda page via `PageContainer helpContent={helpContent.xxx}` + `HelpButton size="sm"` como primer elemento del modal form
- Formularios: `useActionState` para submissions, NO `useState` + handler. Leer de FormData, validar, llamar store async, devolver `FormState<T>`. Cerrar modal chequeando `state.isSuccess` a nivel render
- Zustand: SIEMPRE selectors (nunca destructuring del store). `useShallow` para arrays filtrados, `useMemo` para datos derivados
- Columnas: `useMemo` con `deleteDialog` (objeto entero, no `deleteDialog.open`) en deps
- Branch-scoped: guardar con fallback card si no hay `selectedBranchId`
- Loading skeleton con `<TableSkeleton>` mientras `isLoading`
- Cascade delete: usar wrappers de `cascadeService` + `<CascadePreviewList>` en `<ConfirmDialog>`
- React Compiler: hooks incondicionales, evitar `setState` en `useEffect`

### help-system-content
- HelpButton MANDATORIO en TODAS las Dashboard pages — pasar `helpContent` a `PageContainer` sin excepción
- Contenido de ayuda en `Dashboard/src/utils/helpContent.tsx` — NUNCA inline en la page
- Form modals: `HelpButton size="sm"` inline como primer elemento del form
- Formato helpContent: title → intro → `<ul>` feature list → tip box (bg-zinc-800 + text-orange-400 para consejos; bg-red-900/50 + border-red-700 solo para data loss irreversible)
- Checklist: helpContent.tsx debe crearse si no existe, contenido en español sin tildes

### tailwind-design-system (v4)
- CSS-first config: NO `tailwind.config.ts` — usar `@theme` en CSS + `@import "tailwindcss"`
- OKLCH para colores (no hex/rgb en theme tokens)
- `@custom-variant dark (&:where(.dark, .dark *))` para dark mode (no `darkMode: "class"`)
- Componentes con `cva()` + `cn()` — patrones: Base → Variants → Sizes → States → Overrides
- React 19: `ref` es prop regular, NO `forwardRef`
- `--animate-*` tokens con `@keyframes` dentro de `@theme`
- `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2` en interactive elements

### kb-creator
- Auto-detecta modo: `docs/` con contenido → **ingest** (silencioso, fire-and-forget); sin docs → **interactive** (Q&A discovery)
- Output: `knowledge-base/` en raíz con 10+ archivos canónicos (01 a 11)
- No usar si `knowledge-base/` ya existe (sugerir editar archivos puntuales)
- discovery guarda en `.jr-orchestrator-state.json` `state.kb.discovery`

### openspec-apply-change
- `openspec status --change "<name>" --json` para entender schema y artifacts
- Leer `openspec instructions apply --change "<name>" --json` para contexto de implementación
- task tool con sub-agent para implementar, NO inline
- Strict TDD: test que falla → código mínimo → triangulación → refactor
- Marcar tasks completadas al terminar

### openspec-archive-change
- Solo cambios completados — verificar via `openspec status` que tasks estén [x]
- Sync specs delta antes de archivar: `openspec instructions specs --change "<name>" --json`
- Archivo mueve a `openspec/changes/archive/YYYY-MM-DD-<name>/`
- Después de archivar, marcar [x] en CHANGES.md

### openspec-explore
- NO implementar código — solo leer, investigar, pensar
- Exploración libre: curioso, visual (ASCII diagrams), adaptativo
- Puede crear artifacts OpenSpec (proposal, design, specs) — eso es capturar pensamiento, no implementar
- Si el usuario pide implementar, recordar salir de explore mode primero

### openspec-propose
- Crear change con `openspec new change "<name>"` y generar proposal + design + tasks + specs
- Leer KB y CHANGES.md ANTES de proponer — respetar dependencias y gates
- Leer `openspec instructions` para cada artifact antes de escribirlo
- Usar `openspec status --change "<name>" --json` para verificar estado post-creación

### agents-md-generator
- Pre-checks: `knowledge-base/` debe existir, `02_descripcion_general.md` y `CHANGES.md` deben existir
- Generar AGENTS.md + CLAUDE.md en raíz (copia exacta, no symlink)
- Leer `.atl/skill-registry.md` como source de truth de skills (NO re-escanear)
- Leer `~/.claude/CLAUDE.md` global para NO repetir lo que el stack ya instaló
- Skills agrupadas por rol de agente (Backend Core, Frontend, etc.)

### find-skills
- RECOMMEND ONLY — nunca instalar sin aprobación del usuario
- Buscar en https://skills.sh/ leaderboard primero, luego `npx skills find <query>`
- Recomendar con: skill name, repo/source, install count, one-line why-it-matches
- Devolver tabla completa al orchestrator para que el usuario decida

### go-testing
- Patrones específicos para testing de Go y Bubbletea TUIs
- Usar `teatest` para TUI testing
- Seguir patrones del proyecto (ver SKILL.md completo)

### issue-creation
- Issue-first enforcement: crear issue ANTES de implementar
- Template para bug reports y feature requests
- Incluir labels, milestones, assignee según proyecto

### branch-pr
- PR creation con issue-first enforcement
- Verificar que existe issue vinculado antes de crear PR
- Template de PR con checklist de verificación

### jr-orchestrator
- NO reimplementar lógica de phases — routear a sub-skills
- Own shared state `.jr-orchestrator-state.json` — solo `version`, `step`, `owner`
- Resume flow si state existe con `step != "done"`
- Inter-phase checkpoint: preguntar "Continuar | Ajustar | Parar" después de cada fase
- NEVER auto-install skills — `find-skill` solo recomienda, el usuario elige

### judgment-day
- Lanzar DOS sub-agentes ciegos en paralelo (nunca secuencial)
- Cada judge recibe el MISMO target pero trabaja independiente
- Synthesize findings → apply fixes → re-judge hasta que ambos pasen o 2 iteraciones
- NO hacer review como orchestrator — solo coordinación
- Skill Resolver Protocol antes de lanzar judges

### openspec-design
- `openspec instructions design --change "<name>" --json` para template y contexto
- Leer proposal + specs + existing code antes de diseñar
- Diseño = HOW: architecture decisions, data models, API contracts, component structure

### openspec-init
- `openspec status --json` para verificar si ya está inicializado
- Solo ejecutar `openspec init` si no hay `openspec/` directory
- Verificar que CLI esté instalado: `openspec --version`

### openspec-onboard
- Guided walkthrough de ciclo OPSX completo: Check → Explore → Propose → Apply → Archive
- Usar codebase real del proyecto, no ejemplos genéricos
- Enseñar haciendo: crear un change real

### openspec-spec
- `openspec instructions specs --change "<name>" --json` para template y contexto
- Specs = WHAT: acceptance criteria para implementación
- Leer proposal como dependencia

### openspec-tasks
- `openspec instructions tasks --change "<name>" --json` para template y contexto
- Tasks = HOW: breakdown en unidades completables en una sesión
- Leer proposal + specs + design como dependencias

### openspec-verify
- Verificar completitud (tasks hechos), corrección (code matches specs), coherencia (design seguido)
- `openspec status --change "<name>" --json` para estado actual
- NO corregir automáticamente — reportar findings

### roadmap-generator
- Pre-checks: `knowledge-base/` con 10 canónicos + `openspec/` debe existir
- Output: `CHANGES.md` en raíz (único archivo)
- Leer `state.kb.discovery` + `state.kb.files` si orquestado; si no, globbear `knowledge-base/`
- Fire-and-forget: NO preguntar, generar y devolver
- Incluir: dependency tree, parallelism gates, critical path, multi-agent plan

### skill-creator
- Proceso iterativo: draft → test prompts → evaluate (qual + quant) → rewrite → repeat
- Evaluaciones cuantitativas con scripts de benchmark y variance analysis
- Descubrimiento: skill description improver para optimizar triggering
- Adaptar comunicación al nivel técnico del usuario

---

## Project Conventions

| File | Path | Notes |
|------|------|-------|
| AGENTS.md (index) | `AGENTS.md` | Canonical project instructions — stack, KB reference, skills per agent, roadmap, hard rules |
| CLAUDE.md (copy) | `CLAUDE.md` | Exact copy of AGENTS.md |
| Architecture doc | `docs/ARQUITECTURA.md` | Stack, Clean Architecture patterns, directory structure, security |
| Product requirements | `docs/PRD.md` | RNFs and product requirements |
| Change roadmap | `CHANGES.md` | 24 changes (C-01…C-24), dependency tree, critical path, parallelism gates |
| Knowledge base | `knowledge-base/*.md` | 11 canonical KB files (01…11) covering vision, domain model, actors, rules, flows, architecture, decisions |
| OpenSpec state | `openspec/` | OPSX workflow directory with changes/ and specs/ |
| Orchestrator state | `.jr-orchestrator-state.json` | Foundation flow state tracker |
| Hard rules | `AGENTS.md` §Reglas Duras | 17 non-negotiable rules (no build auto, snake_case, TDD, multi-tenancy, RBAC, etc.) |
