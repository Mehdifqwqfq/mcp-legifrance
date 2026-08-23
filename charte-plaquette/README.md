# Plaquette « Charte graphique EtikPharma » — 1 page A4

Génère un **recto A4 unique** condensant la charte maison EtikPharma : palette par grades,
typographie, contrastes mesurés, règles opposables, marque, icônes et mouvement.

```bash
npm install
REFETIK=/chemin/vers/refetik node render-plaquette.js --date=2026-08-23
# → out/plaquette-charte-etikpharma-2026-08-23.pdf
```

`--date` est facultatif (par défaut : aujourd'hui). Le passer **fige la date d'édition**, donc
rend le PDF reproductible : même canon + même date = même fichier.

## Le canon est ailleurs, et c'est voulu

Aucune couleur, aucune police, aucun ratio n'est écrit en dur dans ce dossier. Tout est lu à
l'exécution dans **refetik** (`Mehdifqwqfq/refetik`, servi sur `ref.etikpharma.com`) :

| Ce qui est lu | Où |
|---|---|
| version et date de la charte | en-tête de `charte/etikpharma-maison.md` |
| couleurs de marque, polices, mouvement, échelle | bloc ` ```json ` (§Palette) |
| matrice famille × grade, marqueurs ⚠ et ✎ | table de §Grades → *Les valeurs* |
| paires texte/fond et leurs verdicts | table de §Branche claire → *Ce qui a été mesuré* |
| marque sur les deux sols | table de §Grades → *Ce que la double famille ne coûte pas* |
| ratios du fond d'icône | prose de §Icônes |
| tracés de marque (5 déclinaisons) | `charte/marque/*.svg` |

Le script cherche le canon dans cet ordre : `$REFETIK/charte`, `../../refetik/charte`,
`/workspace/refetik/charte`, `~/Documents/refetik/charte`. Sans canon, il **échoue** — il ne
se rabat jamais sur des valeurs de secours, qui finiraient par diverger en silence.

**Ce que le script écrit en propre** : la condensation éditoriale — quelles règles tiennent
sur une page et dans quel ordre. Chaque règle porte le nom de la section dont elle sort.
En cas d'écart, le canon prime sur la plaquette ; c'est écrit dans le pied de page.

## Trois contrôles, et pourquoi ils existent

1. **Ratios rejoués.** Chaque paire annoncée par le canon est recalculée depuis les hex. Un
   écart > 0,06 sort en erreur : soit le parsing a cassé, soit le canon a dérivé. Sans ça, la
   plaquette imprimerait un chiffre faux avec l'autorité d'un document de référence.
2. **Collision avec le pied.** Le pied est opaque : un texte qui glisse dessous **disparaît**
   sans agrandir la page — `scrollHeight` ne bouge pas d'un pixel. Une première version de ce
   contrôle mesurait la hauteur et n'a rien vu pendant que la dernière ligne du §07 était
   avalée. On teste donc la géométrie, pas la hauteur.
3. **Lisibilité des libellés.** Les hex sont écrits sur le sol, jamais dans l'aplat : mesuré,
   aucune encre de la charte n'atteint 4,5:1 sur `#7A8690`, `#E5484D`, `#0284C7`, `#1A8C56`
   ni `#B07D20` — le meilleur des deux y plafonne vers 3,9. Sur crème, `ink` donne 13,21:1
   partout.

## La plaquette s'applique ses propres règles

- Les aplats que le canon marque ⚠ (sous 3:1 sur leur sol) portent le **filet de l'encre de
  leur famille**, opaque — la règle exacte de §Grades, pas le filet `teal-deep` universel de
  la v1.3 qui ne généralisait pas.
- Les pastilles trop claires pour se détacher du sol portent un contour fin. Sur cette planche
  la pastille **est** l'information, donc elle relève de WCAG 1.4.11 et non du régime
  « surface » (décor, aucun seuil).
- La baseline du bandeau est en crème (7,71:1) et non en corail : corail sur `teal-deep` donne
  3,35:1, que le canon réserve aux grands caractères. Le corail y revient comme **filet** —
  exactement le report de véhicule que prescrit §Branche claire.

## Polices

`Lora` / `Inter` / `Space Grotesk` sont embarquées en base64 depuis `@fontsource`, donc le PDF
ne dépend d'aucun réseau au rendu. Lora est plafonnée à **700** : 800 et 900 rendent HTTP 400
chez Google et casseraient la feuille entière.

## Où ça devrait vivre

Un générateur de modèle PDF est un **artefact refetik** (cf. `CONVENTIONS.md` §0.2 : la couche
design/templates a pour canon `refetik`, avec une entrée `registry.json`). Il est ici parce que
la branche de travail l'était ; le versement dans refetik reste à faire.
