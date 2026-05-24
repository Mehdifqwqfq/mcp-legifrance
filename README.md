# mcp-legifrance

MCP server wrapping the **Légifrance API** (DILA via PISTE) for use in Etik
Pharma workflows — code consolidé (CSP, CSS, CT…), JORF, LODA, recherche
full-text réglementaire.

V1 ships 6 tools, async-safe OAuth2 token cache, structured Pydantic inputs,
and Markdown / JSON output for every endpoint.

## Pourquoi ce MCP

- **Source primaire** : on pioche le verbatim réglementaire directement dans
  Légifrance plutôt que de réingérer des PDF dérivés (CNOP / Cespharm /
  Meddispar) qui prennent du retard sur les modifications.
- **Standardisation** : remplace les bricolages curl/scrapers OAuth ad hoc.
- **Ingestion corpus** : alimente `tools/standards-pratique/scripts/ingest.py`
  avec un script de récupération section→texte structuré (cf. `tools/`
  ci-dessous).

## Prérequis

1. Une app PISTE **Confidentielle** souscrite à l'API Légifrance v2.4.2.
   Compte créé sur <https://piste.gouv.fr> → "Mes applications" → souscrire
   "Légifrance" (production).
2. Les deux credentials chargés dans l'environnement avant de lancer le MCP :

   ```bash
   export PISTE_CLIENT_ID=...      # UUID
   export PISTE_CLIENT_SECRET=...  # UUID (PISTE utilise vraiment ce format)
   ```

   Recommandé : ajouter ces lignes à `~/.etikpharma-secrets` puis
   `source ~/.etikpharma-secrets` avant le lancement (cf. doctrine secrets
   Etik Pharma).
3. Python ≥ 3.10.

## Install

```bash
cd /Users/medev/mcp-legifrance
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Enregistrement dans Claude Code

```bash
claude mcp add --scope user mcp-legifrance \
  /Users/medev/mcp-legifrance/.venv/bin/legifrance-mcp \
  -e PISTE_CLIENT_ID="$PISTE_CLIENT_ID" \
  -e PISTE_CLIENT_SECRET="$PISTE_CLIENT_SECRET"
```

> Note : MCPs "données publiques" doivent toujours être en `--scope user`
> (cf. doctrine `claude mcp add` Etik Pharma).

## Tools V1

Tous les tools acceptent `response_format` (`markdown` par défaut, ou `json`).

| Tool | Endpoint | Usage |
|------|----------|-------|
| `search_legifrance` | `POST /search` | Recherche full-text (fonds `code`/`code_etat`/`loda`/`jorf`/`juri`/`all`) |
| `get_code_toc` | `POST /consult/code/tableMatieres` | Table des matières d'un code consolidé |
| `get_section` | `POST /consult/getSectionByCid` | Section + sous-sections + articles à date donnée |
| `get_article` | `POST /consult/getArticle` | Verbatim d'un article par identifiant LEGIARTI |
| `get_jorf` | `POST /consult/jorf` | Texte JORF (décret/arrêté/loi) par CID JORFTEXT |
| `consult_loda` | `POST /consult/lawDecree` | Texte LODA consolidé (loi/décret/arrêté non codifié) |

### Exemples d'appel

**Article R.4235-1 (code de déontologie des pharmaciens, version 06/03/2026)**

```json
{ "article_id": "LEGIARTI000006913651" }
```

**Section R.4235 (Chapitre V CSP, à date du 24/05/2026)**

```json
{
  "cid": "LEGISCTA000006178625",
  "text_id": "LEGITEXT000006072665",
  "date": "2026-05-24"
}
```

**Décret 2026-156 du 3 mars 2026**

```json
{ "text_cid": "JORFTEXT000053618939" }
```

**Recherche LODA biosimilaire**

```json
{ "query": "biosimilaire substitution", "fond": "loda", "page_size": 5 }
```

**Recherche scopée au Code de la santé publique**

```json
{
  "query": "pharmacien officine",
  "fond": "code",
  "code_name": "Code de la santé publique",
  "date": "2026-05-24"
}
```

**Table des matières du Code de la santé publique**

```json
{ "text_id": "LEGITEXT000006072665", "date": "2026-05-24", "max_depth": 3 }
```

**Texte LODA consolidé (Arrêté biosimilaires 20/02/2025)**

```json
{ "text_id": "LEGITEXT000053002992", "date": "2026-05-24" }
```

## Tests

```bash
# unitaires (sans réseau)
.venv/bin/pytest tests/test_unit.py -v

# E2E (live PISTE — nécessite PISTE_CLIENT_ID + SECRET dans l'env)
source ~/.etikpharma-secrets
LEGIFRANCE_E2E=1 .venv/bin/pytest tests/test_e2e.py -v
```

V1 : 13 unitaires + 5 E2E, tous verts au 24/05/2026.

## Bonus — pipeline d'ingestion corpus

Le script `tools/ingest_legifrance_section.py` (dans le repo EtikPharma) prend
un `(cid, text_id)` Légifrance, récupère la section + ses articles via le MCP,
et la passe à `tools/standards-pratique/scripts/ingest.py` au format texte
structuré attendu par le corpus `standards`.

## Limitations connues

- L'endpoint `/consult/lawDecree` exige un **LEGITEXT** (pas un JORFTEXT) +
  une `date`. Pour aller du décret JORF au texte LODA consolidé, faire d'abord
  un `search_legifrance` ou `get_jorf` pour récupérer le LEGITEXT associé.
- L'API renvoie ses dates en **timestamps Unix milliseconds**. Le helper
  `ms_to_iso` collapse la sentinelle `9223372036854775807` (= Long.MAX_VALUE,
  "pas de fin") sur `None` pour garder le Markdown propre.
- Quota PISTE : pas de rate limit explicite documenté, mais on cache le token
  1h et on bat-volée à la demande — pas de pré-polling.
- V1 expose 6 tools sur les 61 endpoints documentés dans l'OpenAPI Légifrance.
  Discipline V1 : on n'ajoute pas d'autre tool tant qu'un cas d'usage Etik
  n'en a pas besoin.

## Doctrine et liens

- `project_mcp_legifrance.md` (memory Etik Pharma)
- Référence OpenAPI : `mcp__datagouv__get_dataservice_openapi_spec(672cf648a474f2d73502b5cd)`
- Précédents MCP du même pattern : `mcp-ameli`, `mcp-ansm`, `mcp-has-sante`,
  `mcp-cnop-search`, `mcp-cnam-opendata`.
