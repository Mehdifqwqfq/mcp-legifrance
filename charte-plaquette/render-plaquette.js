/**
 * Plaquette A4 « Charte graphique EtikPharma » — 1 page recto, HTML -> Chromium -> PDF.
 *
 * PRINCIPE (repris du kit refetik `fiche-apothicaire`) : aucune couleur, aucune police et
 * aucun ratio de contraste n'est écrit en dur ici. Tout est lu à l'exécution dans le canon
 * `charte/etikpharma-maison.md` du dépôt refetik. Une valeur recopiée dans ce fichier
 * finirait par diverger du canon — c'est exactement la dette que la charte v1.5 mesure.
 *
 * Ce que ce script écrit en propre : la CONDENSATION éditoriale (quelles règles tiennent sur
 * une page, dans quel ordre). Chaque règle porte le nom de la section du canon dont elle sort,
 * pour rester traçable.
 */
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

// ---------------------------------------------------------------- canon refetik

const CANON_CANDIDATES = [
  process.env.REFETIK && path.join(process.env.REFETIK, 'charte'),
  path.join(__dirname, '..', '..', 'refetik', 'charte'),
  '/workspace/refetik/charte',
  path.join(process.env.HOME || '', 'Documents', 'refetik', 'charte'),
].filter(Boolean);

function canonDir() {
  for (const d of CANON_CANDIDATES) {
    if (fs.existsSync(path.join(d, 'etikpharma-maison.md'))) return d;
  }
  throw new Error(
    'Canon refetik introuvable. Clone https://github.com/Mehdifqwqfq/refetik puis relance avec\n' +
    '  REFETIK=/chemin/vers/refetik node render-plaquette.js\n' +
    'Chemins essayés :\n  - ' + CANON_CANDIDATES.join('\n  - ')
  );
}
const CANON = canonDir();
const MD = fs.readFileSync(path.join(CANON, 'etikpharma-maison.md'), 'utf8');

/** Version + date du canon, lues dans son en-tête (jamais supposées). */
function canonVersion() {
  const v = MD.match(/^#\s*Charte maison EtikPharma\s*—\s*v([\d.]+)/m);
  const d = MD.match(/^>\s*\*\*v[\d.]+\s*\((\d{4}-\d{2}-\d{2})\)\*\*/m);
  if (!v || !d) throw new Error('En-tête du canon illisible : version ou date absente.');
  return { version: v[1], date: d[1] };
}

/** Bloc ```json` de la charte — déclaré par elle « source unique des valeurs ». */
function tokens() {
  const block = MD.match(/```json\s*([\s\S]*?)```/);
  if (!block) throw new Error('Canon illisible : aucun bloc ```json` (tokens).');
  const { tokens } = JSON.parse(block[1]);
  for (const k of ['brand', 'ink', 'state', 'fonts', 'motion', 'type-scale']) {
    if (!tokens[k]) throw new Error(`Canon incomplet : tokens.${k} manquant.`);
  }
  return tokens;
}

/** Extrait le corps d'une table markdown située sous un titre donné. */
function tableUnder(heading) {
  const i = MD.indexOf(heading);
  if (i < 0) throw new Error(`Section « ${heading} » absente du canon.`);
  const rows = [];
  for (const line of MD.slice(i).split('\n').slice(1)) {
    const t = line.trim();
    if (!t.startsWith('|')) { if (rows.length) break; else continue; }
    if (/^\|[\s:|-]+\|$/.test(t)) continue;
    rows.push(t.slice(1, -1).split('|').map(c => c.trim()));
  }
  if (!rows.length) throw new Error(`Aucune table sous « ${heading} ».`);
  return rows;
}

const stripMd = s => s.replace(/\*\*/g, '').replace(/`/g, '').replace(/\*(.*?)\*/g, '$1').trim();

/** §Grades → Les valeurs : la matrice famille x grade, avec ses marqueurs ⚠️ (sous 3:1) et ✎ (calculée). */
function grades() {
  const rows = tableUnder('### Les valeurs — arbitrées et mesurées le 2026-08-18');
  const head = rows[0].slice(1).map(stripMd);
  return {
    grades: head,
    families: rows.slice(1).map(r => ({
      key: stripMd(r[0]).replace(/\s*\(.*\)$/, '').trim(),
      scope: (r[0].match(/\((.*?)\)/) || [, ''])[1],
      cells: r.slice(1).map(c => {
        const hex = (c.match(/#[0-9A-Fa-f]{6}/) || [null])[0];
        return hex && { hex, low: c.includes('⚠'), computed: c.includes('✎') };
      }),
    })),
  };
}

/** §Branche claire → Ce qui a été mesuré : les paires texte/fond et leur verdict. */
function contrasts() {
  return tableUnder('### Ce qui a été mesuré (WCAG, 2026-07-21)').slice(1).map(r => ({
    bg: stripMd(r[0]), fg: stripMd(r[1]),
    ratio: parseFloat(stripMd(r[2]).replace(',', '.')),
    use: stripMd(r[3]),
    ko: /❌/.test(r[3]),
  }));
}

/** §Grades → Ce que la double famille NE coûte pas : marque mesuree sur les deux sols. */
function bothSoils() {
  const rows = tableUnder('#### Ce que la double famille NE coûte pas');
  const sols = rows[0].slice(1).map(h => (h.match(/#[0-9A-Fa-f]{6}/) || [''])[0]);
  return {
    sols,
    rows: rows.slice(1).map(r => ({ name: stripMd(r[0]), vals: r.slice(1).map(stripMd) })),
  };
}

/** §Icônes : les deux ratios qui fondent le fond `teal-deep`, lus dans la prose. */
function iconRatios() {
  const m = MD.match(/l'accent corail donne \*\*([\d,]+):1\*\*, sur\s*`teal` il tombe à \*\*([\d,]+):1\*\*/s);
  if (!m) throw new Error('§Icônes : ratios du fond introuvables dans le canon.');
  return { deep: m[1], base: m[2] };
}

const T = tokens(), G = grades(), C = contrasts(), ICON = iconRatios(), V = canonVersion();
const BOTH = bothSoils();

// ---------------------------------------------------------------- contrôle WCAG

const srgb = c => (c /= 255) <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
const lum = hex => {
  const n = parseInt(hex.slice(1), 16);
  return 0.2126 * srgb(n >> 16 & 255) + 0.7152 * srgb(n >> 8 & 255) + 0.0722 * srgb(n & 255);
};
const ratio = (a, b) => {
  const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
};
/**
 * Les hex de la palette sont écrits sur le SOL, pas dans l'aplat : mesuré, aucune encre de la
 * charte n'atteint 4,5:1 sur `#7A8690`, `#E5484D`, `#0284C7`, `#1A8C56` ni `#B07D20` — le
 * meilleur des deux y plafonne vers 3,9. Sur crème, `ink` donne 13,21:1 pour tous.
 */
const LABEL_ON_SOL = ratio(T.ink.ink, T.ink.creme);
if (LABEL_ON_SOL < 4.5) throw new Error(`Libellés de palette illisibles : ${LABEL_ON_SOL.toFixed(2)}:1.`);

/**
 * Garde-fou : la plaquette ne doit jamais imprimer un ratio que le canon annonce mais que
 * les hex ne produisent pas. Un écart signale soit un parsing cassé, soit une dérive du canon.
 */
const NAMED = { ...T.brand, ...T.ink, ...T.state };
const drift = [];
for (const c of C) {
  const bg = NAMED[c.bg.replace(/^aplat /, '')], fg = NAMED[c.fg];
  if (!bg || !fg) continue;
  const got = ratio(bg, fg);
  if (Math.abs(got - c.ratio) > 0.06) drift.push(`${c.bg}/${c.fg} : canon ${c.ratio} vs mesuré ${got.toFixed(2)}`);
}
if (drift.length) {
  console.error('⚠️  Ratios du canon non reproduits :\n   - ' + drift.join('\n   - '));
  process.exitCode = 1;
}

// ---------------------------------------------------------------- polices & marque

function fontFaces() {
  const b64 = p => {
    try { return fs.readFileSync(path.join(__dirname, 'node_modules/@fontsource', p)).toString('base64'); }
    catch (e) { throw new Error(`Police manquante (${p}). Lance : npm install`); }
  };
  const F = (fam, w, file) =>
    `@font-face{font-family:'${fam}';font-style:normal;font-weight:${w};font-display:block;` +
    `src:url(data:font/woff2;base64,${b64(file)}) format('woff2');}`;
  // Lora plafonne à 700 : 800/900 rendent HTTP 400 chez Google (canon, §Ce que Lora coûte).
  return [
    F(T.fonts.display, 400, 'lora/files/lora-latin-400-normal.woff2'),
    F(T.fonts.display, 600, 'lora/files/lora-latin-600-normal.woff2'),
    F(T.fonts.display, 700, 'lora/files/lora-latin-700-normal.woff2'),
    F(T.fonts.text, 400, 'inter/files/inter-latin-400-normal.woff2'),
    F(T.fonts.text, 500, 'inter/files/inter-latin-500-normal.woff2'),
    F(T.fonts.text, 600, 'inter/files/inter-latin-600-normal.woff2'),
    F(T.fonts.text, 700, 'inter/files/inter-latin-700-normal.woff2'),
    F(T.fonts.tech, 500, 'space-grotesk/files/space-grotesk-latin-500-normal.woff2'),
    F(T.fonts.tech, 700, 'space-grotesk/files/space-grotesk-latin-700-normal.woff2'),
  ].join('');
}

/** Les tracés de marque ne sont jamais redessinés : ils sont lus dans refetik. */
function marque(name, px) {
  const p = path.join(CANON, 'marque', name + '.svg');
  if (!fs.existsSync(p)) throw new Error(`Tracé de marque absent : ${p}`);
  return fs.readFileSync(p, 'utf8')
    .replace(/\swidth="\d+"/, ` width="${px}"`)
    .replace(/\sheight="\d+"/, ` height="${px}"`);
}

// ---------------------------------------------------------------- contenu éditorial
// Condensation : chaque entrée cite la section du canon dont elle sort.

const RULES = [
  ['Le teal porte le fond, le corail porte l’accent.', 'dérivé', 'Un fond corail ne contraste avec rien : 2,90 sur crème, 1,62 sur teal.'],
  ['Un seul élément corail par plan.', 'verrouillé 20/07/26', 'Règle de rareté : le corail tire sa force de sa parcimonie, pas de sa surface.'],
  ['Sur fond clair, le corail ne porte pas de texte — à aucune taille.', 'dérivé', 'Il change de véhicule : sol, aplat ou filet. Il y gagne 6,04 contre 3,35.'],
  ['Un aplat sous 3:1 se borde du filet de sa propre encre.', 'dérivé', 'Opaque. err, info et teal passent seuls le seuil : leur en poser un serait un ornement.'],
  ['Une couleur qui porte du sens est interdite dans le décor.', 'dérivé', 'Vécu : une barre corail sur sol corail disparaît à l’instant de sa bascule.'],
  ['La parité se joue entre les plans, la rareté du corail dans un plan.', 'dérivé', 'Les deux phrases du canon ne parlent pas du même objet.'],
  ['La famille de neutres découle du public.', 'verrouillé 18/08/26', 'Elle ne se choisit pas : Comptoir (interne) → froids, Public (patients) → chauds.'],
  ['Tout nombre qui varie porte tabular-nums.', 'dérivé', 'Sans lui le bloc « respire » à chaque incrément. Invisible sur maquette figée.'],
];

const GRADE_ROLES = [
  ['sol', 'fond de page', '—'],
  ['surface', 'fond de carte, de pastille', 'aucune'],
  ['filet', 'bordure, séparateur', '3:1 s’il délimite seul'],
  ['plein', 'aplat qui porte du sens', '3:1 — WCAG 1.4.11'],
  ['encre', 'le texte de cette famille', '4,5:1'],
];

const MOTION = [
  ['ease-enter', `cubic-bezier(${T.motion['ease-enter'].join(', ')})`],
  ['ease-exit', `cubic-bezier(${T.motion['ease-exit'].join(', ')})`],
  ['ease-emphasis', `cubic-bezier(${T.motion['ease-emphasis'].join(', ')})`],
  ['durées', `${T.motion['dur-micro-frames']} / ${T.motion['dur-base-frames']} / ${T.motion['dur-ample-frames']} f ⚠`],
  ['décalage · amplitude', `${T.motion['stagger-frames']} f · ${T.motion['amplitude-px']} px`],
  ['échelle · référence', `${T['type-scale'].display} / ${T['type-scale'].body} / ${T['type-scale'].label} px @ ${T['type-scale']['ref-width']}`],
];

const esc = s => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];
const longDate = iso => { const [y, m, d] = iso.split('-').map(Number); return `${d} ${MOIS[m - 1]} ${y}`; };

// Date d'édition : figée par --date=YYYY-MM-DD pour que le PDF soit reproductible.
const argDate = (process.argv.find(a => a.startsWith('--date=')) || '').slice(7);
if (argDate && !/^\d{4}-\d{2}-\d{2}$/.test(argDate)) throw new Error('--date attend YYYY-MM-DD');
const EDITION = argDate || new Date().toISOString().slice(0, 10);

// ---------------------------------------------------------------- rendu

const pill = (txt, kind) => `<span class="pill ${kind}">${esc(txt)}</span>`;

// Filet de délimitation : l'encre de la famille quand le canon a marqué l'aplat (⚠), sinon un
// trait fin pris dans la charte — `plein` de la famille froide, seul neutre mesuré au-dessus de 3:1.
const HAIRLINE = (() => {
  const f = G.families.find(f => f.key === 'froid');
  const hex = f && (f.cells[G.grades.indexOf('plein')] || {}).hex;
  if (!hex) throw new Error('Filet de délimitation introuvable : froid/plein absent du canon.');
  if (ratio(hex, T.ink.creme) < 3) throw new Error(`Filet sous 3:1 sur le sol de la plaquette.`);
  return hex;
})();

function swatchCell(cell, family) {
  if (!cell) return '<td class="empty"><span></span></td>';
  // Le canon l'impose : un aplat sous 3:1 sur son sol se borde de l'encre de sa famille.
  const filet = cell.low && family.encre
    ? `box-shadow:inset 0 0 0 1.1pt ${family.encre};`
    : (ratio(cell.hex, T.ink.creme) < 3 ? `box-shadow:inset 0 0 0 .5pt ${HAIRLINE};` : '');
  const mk = (cell.computed ? '✎' : '') + (cell.low ? '⚠' : '');
  return `<td><span class="sw"><i class="ch" style="background:${cell.hex};${filet}"></i>` +
    `<b>${cell.hex.toUpperCase()}</b><u>${mk}</u></span></td>`;
}

const paletteRows = G.families.map(f => {
  const encre = (f.cells[G.grades.indexOf('encre')] || {}).hex;
  return `<tr><th><b>${esc(f.key)}</b>${f.scope ? `<em>${esc(f.scope)}</em>` : ''}</th>` +
    f.cells.map(c => swatchCell(c, { encre })).join('') + '</tr>';
}).join('');

const html = `<!doctype html><html lang="fr"><head><meta charset="utf-8">
<title>Charte graphique EtikPharma — plaquette</title>
<style>
${fontFaces()}
:root{
  --corail:${T.brand.corail}; --corail-deep:${T.brand['corail-deep']};
  --teal:${T.brand.teal}; --teal-deep:${T.brand['teal-deep']}; --teal-soft:${T.brand['teal-soft']};
  --ink:${T.ink.ink}; --muted:${T.ink.muted}; --line:${T.ink.line}; --creme:${T.ink.creme};
  --surface:#F6F3EA; --corail-encre:#D12D00; --warn-encre:#7A5600; --warn-soft:#FEF3C7;
}
@page{size:A4;margin:0}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:210mm;height:297mm}
body{background:var(--creme);color:var(--ink);
  font-family:'${T.fonts.text}',system-ui,sans-serif;font-size:7.4pt;line-height:1.34;
  -webkit-font-smoothing:antialiased;font-kerning:normal}
.page{width:210mm;height:297mm;display:flex;flex-direction:column;overflow:hidden}

/* ---- bandeau : branche sombre du canon (crème sur teal-deep, 7,71:1) ---- */
.hd{background:var(--teal-deep);color:var(--creme);padding:5mm 11mm 4.8mm;
  display:flex;align-items:flex-start;gap:6mm}
.hd .mark{flex:0 0 auto;line-height:0}
.hd .mark svg{display:block;border-radius:2.6mm}
.hd .id{flex:1 1 auto;padding-top:.6mm}
.hd h1{font-family:'${T.fonts.display}',serif;font-weight:700;font-size:21pt;letter-spacing:-.012em;line-height:1}
.hd .sub{font-family:'${T.fonts.display}',serif;font-size:9.4pt;font-weight:400;color:var(--teal-soft);margin-top:1.4mm}
.hd .base{font-size:6.4pt;font-weight:600;letter-spacing:.19em;color:var(--creme);margin-top:2.1mm}
.hd .base::before{content:"";display:inline-block;width:5.4mm;height:1.2pt;background:var(--corail);
  vertical-align:.62mm;margin-right:2.1mm}
.hd .meta{flex:0 0 46mm;text-align:right;border-left:.5pt solid rgba(251,250,245,.28);padding-left:5mm;align-self:stretch}
.hd .meta .lb{font-size:5.6pt;font-weight:600;letter-spacing:.17em;color:var(--teal-soft);opacity:.85}
.hd .meta .dt{font-family:'${T.fonts.tech}',sans-serif;font-weight:700;font-size:10.6pt;
  font-variant-numeric:tabular-nums;margin:.6mm 0 1.9mm;line-height:1.1}
.hd .meta p{font-size:6.5pt;color:var(--teal-soft);line-height:1.45}
.hd .meta p b{color:var(--creme);font-weight:600}

/* ---- corps ---- */
.body{flex:1 1 auto;padding:3.3mm 11mm 0;display:flex;flex-direction:column;gap:1.7mm;
  justify-content:space-between;min-height:0}
.body>*{flex:0 0 auto}
h2{font-family:'${T.fonts.display}',serif;font-weight:600;font-size:9pt;color:var(--teal-deep);
  letter-spacing:-.005em;display:flex;align-items:baseline;gap:2.2mm;margin-bottom:1.05mm}
h2::after{content:"";flex:1 1 auto;height:1.1pt;background:var(--corail);opacity:.9;transform:translateY(-.9pt)}
h2 .n{font-family:'${T.fonts.tech}',sans-serif;font-size:6.6pt;font-weight:700;color:var(--corail-encre);
  font-variant-numeric:tabular-nums}
.hint{font-size:6.2pt;color:var(--muted);font-weight:400;letter-spacing:0}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:2.6mm 6mm}
.cols3{display:grid;grid-template-columns:1fr 1fr;gap:3.4mm 6mm}

/* ---- palette : la matrice EST la table des grades ---- */
table.pal{width:100%;border-collapse:collapse;table-layout:fixed}
table.pal thead th{font-size:5.8pt;font-weight:600;letter-spacing:.13em;color:var(--muted);
  text-align:center;padding-bottom:.8mm;text-transform:uppercase}
table.pal thead th:first-child{text-align:left}
table.pal th:first-child{width:20mm;text-align:left;vertical-align:middle;padding-right:2mm}
table.pal tbody th b{font-size:7.2pt;font-weight:700;color:var(--teal-deep);display:block;line-height:1.15}
table.pal tbody th em{font-size:5.6pt;font-style:normal;color:var(--muted);letter-spacing:.02em}
table.pal td{padding:.34mm .5mm}
.sw{display:flex;align-items:center;gap:1.2mm}
.sw .ch{flex:1 1 auto;min-width:4mm;height:4.9mm;border-radius:1.1mm;display:block}
.sw b{flex:0 0 11.2mm;font-family:'${T.fonts.tech}',sans-serif;font-size:5.9pt;font-weight:500;
  letter-spacing:.005em;font-variant-numeric:tabular-nums;color:var(--ink);text-align:left}
.sw u{flex:0 0 2.2mm;text-decoration:none;font-size:5pt;color:var(--muted);margin-left:-.8mm}
td.empty span{display:block;height:4.9mm;border-radius:1.1mm;
  background:repeating-linear-gradient(135deg,transparent 0 1.4mm,var(--line) 1.4mm 1.55mm)}
.legend{display:flex;gap:5mm;margin-top:.8mm;font-size:5.9pt;color:var(--muted)}
.legend b{color:var(--ink);font-weight:600}

/* ---- blocs ---- */
.card{border:.6pt solid var(--line);border-radius:1.4mm;padding:1.8mm 2.4mm;background:var(--surface)}
.spec{display:flex;align-items:baseline;gap:2.6mm;padding:.9mm 0;border-bottom:.5pt solid var(--line)}
.spec:last-child{border-bottom:0;padding-bottom:0}
.spec .aa{flex:0 0 12mm;font-size:13.5pt;line-height:1;color:var(--teal-deep)}
.spec .nm{flex:0 0 24mm;font-weight:600;font-size:7.3pt;color:var(--ink)}
.spec .ds{flex:1 1 auto;font-size:6.4pt;color:var(--muted);line-height:1.35}
.spec .ds b{color:var(--teal-deep);font-weight:600}

table.k{width:100%;border-collapse:collapse}
table.k th{font-size:5.6pt;font-weight:600;letter-spacing:.13em;color:var(--muted);text-transform:uppercase;
  text-align:left;padding-bottom:.7mm;border-bottom:.6pt solid var(--line)}
table.k td{padding:.46mm 0;border-bottom:.4pt solid var(--line);font-size:6.7pt;vertical-align:baseline}
table.k tr:last-child td{border-bottom:0}
table.k td.g{font-family:'${T.fonts.tech}',sans-serif;font-weight:700;color:var(--teal-deep);font-size:6.7pt;width:15mm}
table.k td.r{text-align:right;font-family:'${T.fonts.tech}',sans-serif;font-variant-numeric:tabular-nums;
  font-weight:500;white-space:nowrap;width:17mm}
table.k td.pair{white-space:nowrap}
table.k td.pair i{font-style:normal;color:var(--muted)}
.ko{color:var(--corail-encre);font-weight:700}
.okv{color:#0F6B3D;font-weight:700}

ol.rules{list-style:none;counter-reset:r}
ol.rules li{counter-increment:r;padding:.85mm 0 .85mm 5.4mm;position:relative;
  border-bottom:.4pt solid var(--line)}
ol.rules li:last-child{border-bottom:0}
ol.rules li::before{content:counter(r);position:absolute;left:0;top:1.05mm;
  font-family:'${T.fonts.tech}',sans-serif;font-size:5.9pt;font-weight:700;color:var(--creme);
  background:var(--teal-deep);width:3.9mm;height:3.9mm;line-height:3.9mm;text-align:center;border-radius:.9mm}
ol.rules b{font-weight:600;font-size:6.9pt;color:var(--ink)}
ol.rules em{display:block;font-style:normal;font-size:6.05pt;color:var(--muted);margin-top:.2mm}
.pill{display:inline-block;font-size:5.3pt;font-weight:600;letter-spacing:.06em;padding:.25mm 1.1mm;
  border-radius:.7mm;vertical-align:.4mm;margin-left:1.2mm;white-space:nowrap}
.pill.d{background:var(--teal-soft);color:var(--teal-deep)}
.pill.v{background:var(--warn-soft);color:var(--warn-encre)}

.sh{font-size:6.1pt;font-weight:600;letter-spacing:.055em;color:var(--teal-deep);
  text-transform:uppercase;margin-bottom:1mm}
.sh .hint{text-transform:none;letter-spacing:0;font-weight:400}
.statut{margin-top:1.3mm;border-top:.6pt solid var(--line);padding-top:1mm;
  font-size:6.2pt;color:var(--muted);line-height:1.4}
.statut b{color:var(--teal-deep);font-weight:600}
.statut .pill{margin:0 .3mm 0 .9mm}
table.k.soils td{padding:.36mm 0}
table.k.soils th{text-align:right;font-size:5.2pt;padding-bottom:.5mm}
table.k.soils th:first-child{text-align:left}
table.k.soils td.r{width:20mm}
.marks{display:flex;gap:2.6mm;align-items:flex-end;margin-bottom:1.9mm}
.marks figure{text-align:center;flex:0 0 auto}
.marks svg{display:block;border-radius:1.9mm}
.marks .onlight{background:var(--creme);border:.5pt solid var(--line);border-radius:1.9mm;padding:.9mm}
.marks figcaption{font-size:5.4pt;color:var(--muted);margin-top:.7mm;letter-spacing:.02em}
.note{font-size:6.25pt;color:var(--muted);line-height:1.36}
.note b{color:var(--teal-deep);font-weight:600}
.note+.note{margin-top:.9mm}
.ico{display:flex;gap:2mm;align-items:center;margin-bottom:1.4mm}
.ico .tile{width:9mm;height:9mm;border-radius:2.4mm;background:var(--teal-deep);position:relative;flex:0 0 auto}
.ico .tile .p{position:absolute;left:2.1mm;top:2.1mm;width:5.6mm;height:5.6mm;border-radius:.8mm;background:var(--creme)}
.ico .tile .a{position:absolute;right:1.7mm;bottom:1.7mm;width:3.1mm;height:3.1mm;border-radius:.7mm;background:var(--corail)}
.ico .txt{font-size:6.3pt;color:var(--muted);line-height:1.4}
.ico .txt b{color:var(--teal-deep);font-weight:600}

/* ---- pied ---- */
.ft{flex:0 0 auto;background:var(--teal-deep);color:var(--teal-soft);
  padding:1.9mm 11mm;display:flex;justify-content:space-between;align-items:center;gap:6mm;font-size:5.9pt}
.ft b{color:var(--creme);font-weight:600}
.ft .sig{font-family:'${T.fonts.display}',serif;font-size:7pt;color:var(--creme);letter-spacing:.13em;white-space:nowrap}
</style></head><body><div class="page">

<header class="hd">
  <div class="mark">${marque('marque', 64)}</div>
  <div class="id">
    <h1>EtikPharma</h1>
    <div class="sub">Charte graphique — plaquette de référence</div>
    <div class="base">PAR NOUS, POUR VOUS</div>
  </div>
  <div class="meta">
    <div class="lb">ÉDITION</div>
    <div class="dt">${esc(longDate(EDITION))}</div>
    <p>Condensé de la <b>charte maison v${esc(V.version)}</b><br>du ${esc(longDate(V.date))}</p>
    <p style="margin-top:1.4mm">Canon : <b>refetik</b><br>ref.etikpharma.com</p>
  </div>
</header>

<main class="body">

  <section>
    <h2><span class="n">01</span>Palette <span class="hint">— deux primaires à égalité ; le grade nomme un rôle, pas une clarté</span></h2>
    <table class="pal">
      <thead><tr><th>Famille</th>${G.grades.map(g => `<th>${esc(g)}</th>`).join('')}</tr></thead>
      <tbody>${paletteRows}</tbody>
    </table>
    <div class="legend">
      <span><b>⚠</b> aplat sous 3:1 sur son sol — bordé de l’encre de sa famille, comme l’impose le canon</span>
      <span><b>✎</b> valeur calculée, à juger à l’œil</span>
      <span><b>contour fin</b> — pastille trop claire pour se détacher du sol</span>
    </div>
  </section>

  <div class="cols">
    <section>
      <h2><span class="n">02</span>Typographie</h2>
      <div class="card">
        <div class="spec">
          <div class="aa" style="font-family:'${T.fonts.display}',serif;font-weight:700">Aa</div>
          <div class="nm">${esc(T.fonts.display)}</div>
          <div class="ds"><b>Titraille et affichage.</b> 400 → 700 seulement : 800 et 900 n’existent pas, les demander casse la feuille entière.</div>
        </div>
        <div class="spec">
          <div class="aa" style="font-family:'${T.fonts.text}',sans-serif;font-weight:600">Aa</div>
          <div class="nm">${esc(T.fonts.text)}</div>
          <div class="ds"><b>Texte et interface.</b> Repli <code>system-ui</code>.</div>
        </div>
        <div class="spec">
          <div class="aa" style="font-family:'${T.fonts.tech}',sans-serif;font-weight:700">123</div>
          <div class="nm">${esc(T.fonts.tech)}</div>
          <div class="ds"><b>Technique et chiffres</b> — jeton <code>tech</code>, jamais <code>mono</code> : c’est une sans-serif proportionnelle. Chiffres tabulaires embarqués.</div>
        </div>
      </div>
      <div class="note" style="margin-top:1.7mm">La règle opposable n’est pas « ${esc(T.fonts.display)} » mais le <b>critère</b> : la serif retenue ne fait pas descendre son <b>f</b> sous la ligne de base. Le choix entre les recevables est arbitraire, et se verrouille par date.${pill('verrouillé 15/08/26', 'v')}</div>
    </section>

    <section>
      <h2><span class="n">03</span>Grades <span class="hint">— le seuil suit l’usage</span></h2>
      <table class="k">
        <thead><tr><th>Grade</th><th>Rôle unique</th><th style="text-align:right">Contraste</th></tr></thead>
        <tbody>${GRADE_ROLES.map(([g, r, o]) =>
          `<tr><td class="g">${esc(g)}</td><td>${esc(r)}</td><td class="r">${esc(o)}</td></tr>`).join('')}</tbody>
      </table>
      <div class="note" style="margin-top:1.4mm">Un fond de carte à 1,12:1 est un <b>bon</b> fond de carte : 1.4.11 vise le sens, pas le décor. Neutres <b>froids</b> pour Comptoir, <b>chauds</b> pour Public — la famille chaude n’a pas encore d’encre, toute encre y reste <code>ink</code>.</div>
      <div class="statut"><b>Statut des standards</b> — ${pill('dérivé', 'd')} la règle a une réponse juste, <b>qui se mesure</b> : on ne l’ouvre pas à l’avis, on remesure. ${pill('verrouillé', 'v')} plusieurs réponses marchaient ; celle-ci porte une <b>date</b> et un <b>coût de sortie</b>, et la rouvrir sans le payer n’a aucune condition d’arrêt.</div>
    </section>
  </div>

  <div class="cols">
    <section>
      <h2><span class="n">04</span>Contrastes mesurés <span class="hint">— jamais inférés</span></h2>
      <table class="k">
        <tbody>${C.map(c =>
          `<tr><td class="pair">${esc(c.bg)} <i>+</i> ${esc(c.fg)}</td>` +
          `<td class="r ${c.ko ? 'ko' : 'okv'}">${esc(c.ratio.toFixed(2).replace('.', ','))}:1</td>` +
          `<td style="padding-left:2.4mm;color:var(--muted);font-size:6.2pt">${esc(c.use)}</td></tr>`).join('')}
        <tr><td class="pair">icône : corail <i>sur</i> teal-deep</td><td class="r okv">${esc(ICON.deep)}:1</td>
            <td style="padding-left:2.4mm;color:var(--muted);font-size:6.2pt">le fond d’icône, et c’est dérivé</td></tr>
        <tr><td class="pair">icône : corail <i>sur</i> teal</td><td class="r ko">${esc(ICON.base)}:1</td>
            <td style="padding-left:2.4mm;color:var(--muted);font-size:6.2pt">❌ sous le seuil 1.4.11</td></tr>
        </tbody>
      </table>
      <div class="sh" style="margin-top:1.5mm">La marque sur les deux sols <span class="hint">— la double famille ne coûte pas de remesure</span></div>
      <table class="k soils">
        <thead><tr><th></th>${BOTH.sols.map(h => `<th>sol ${esc(h)}</th>`).join('')}</tr></thead>
        <tbody>${BOTH.rows.map(r =>
          `<tr><td class="pair">${esc(r.name)}</td>${r.vals.map(v =>
            `<td class="r ${parseFloat(v.replace(',', '.')) >= 3 ? 'okv' : 'ko'}">${esc(v)}:1</td>`).join('')}</tr>`).join('')}
        </tbody>
      </table>
    </section>

    <section>
      <h2><span class="n">05</span>Règles opposables</h2>
      <ol class="rules">${RULES.map(([r, st, why]) =>
        `<li><b>${esc(r)}</b>${pill(st, st === 'dérivé' ? 'd' : 'v')}<em>${esc(why)}</em></li>`).join('')}</ol>
    </section>
  </div>

  <div class="cols">
    <section>
      <h2><span class="n">06</span>Marque <span class="hint">— arbitraire pur, verrouillé</span></h2>
      <div class="marks">
        <figure>${marque('marque', 36)}<figcaption>marque</figcaption></figure>
        <figure>${marque('marque-reduite', 28)}<figcaption>réduite ≤ 32 px</figcaption></figure>
        <figure>${marque('marque-sur-creme', 28)}<figcaption>sur crème</figcaption></figure>
        <figure><div class="onlight">${marque('marque-detouree', 22)}</div><figcaption>détourée ⚠</figcaption></figure>
        <figure>${marque('marque-mono', 28)}<figcaption>mono</figcaption></figure>
      </div>
      <div class="note"><b>Quatre blocs inégaux, crème sur teal-deep, un seul en corail.</b> Ni une lettre, ni une croix pleine. Retenue parmi treize motifs comparés à taille réelle.${pill('verrouillé 18/08/26', 'v')}</div>
      <div class="note">La <b>réduite</b> n’est pas un second logo : mêmes blocs, même position du corail, seuls les vides sont doublés — à 16 px la version serrée soude ses blocs. La <b>détourée</b> exige un sol clair. La baseline <b>PAR NOUS, POUR VOUS</b> survit hors du logo : signature de communication, jamais élément du lockup.</div>
    </section>

    <section>
      <h2><span class="n">07</span>Icônes &amp; mouvement</h2>
      <div class="ico">
        <div class="tile"><span class="p"></span><span class="a"></span></div>
        <div class="txt"><b>Fond teal-deep, pictogramme crème, accent corail.</b> Plat par défaut : le relief n’existe plus sous 32 px et rend <b>moins net</b> à 56 px — autorisé au-delà de ~120 px. Une icône montre un <b>état</b>, jamais une transition. Contrôle sur planche 16 → 180 px, rognage circulaire appliqué.</div>
      </div>
      <table class="k">
        <tbody>${MOTION.map(([k, v]) =>
          `<tr><td class="g" style="width:26mm">${esc(k)}</td><td class="r" style="width:auto;text-align:right">${esc(v)}</td></tr>`).join('')}</tbody>
      </table>
      <div class="note" style="margin-top:1.4mm">30 fps. ⚠ <code>dur-ample</code> encore dérivé : aucune séquence ne l’a employé. Une capsule se compose en <b>1:1</b> — le format suit la forme du contenu, jamais la destination.</div>
    </section>
  </div>

</main>

<footer class="ft">
  <div>Plaquette éditée le <b>${esc(longDate(EDITION))}</b> · condensé de la charte maison EtikPharma <b>v${esc(V.version)}</b> (${esc(longDate(V.date))}) · source unique des valeurs : <b>refetik</b> — ref.etikpharma.com · <b>en cas d’écart, le canon prime sur cette plaquette.</b></div>
  <div class="sig">EtikPharma</div>
</footer>

</div></body></html>`;

// ---------------------------------------------------------------- sortie

const OUT = path.join(__dirname, 'out');
fs.mkdirSync(OUT, { recursive: true });
const base = `plaquette-charte-etikpharma-${EDITION}`;
const htmlPath = path.join(OUT, base + '.html');
const pdfPath = path.join(OUT, base + '.pdf');
fs.writeFileSync(htmlPath, html);

function chromiumPath() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const root = process.env.PLAYWRIGHT_BROWSERS_PATH;
  if (root) {
    for (const p of [path.join(root, 'chromium'), path.join(root, 'chrome')]) {
      if (fs.existsSync(p) && fs.statSync(p).isFile()) return p;
    }
    const dir = fs.existsSync(root) && fs.readdirSync(root).find(d => /^chromium-\d+$/.test(d));
    if (dir) {
      for (const rel of ['chrome-linux/chrome', 'chrome-mac/Chromium.app/Contents/MacOS/Chromium']) {
        const p = path.join(root, dir, rel);
        if (fs.existsSync(p)) return p;
      }
    }
  }
  for (const p of ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                   '/usr/bin/google-chrome', '/usr/bin/chromium']) {
    if (fs.existsSync(p)) return p;
  }
  return undefined; // Playwright ira chercher son propre Chromium.
}

(async () => {
  const { chromium } = require('playwright-core');
  const browser = await chromium.launch({ executablePath: chromiumPath() });
  const page = await browser.newPage();
  await page.goto('file://' + htmlPath, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);

  // Contrôle dur : la plaquette est un RECTO, et son pied est opaque. Un texte qui glisse
  // dessous ne fait pas déborder la page — il DISPARAÎT, sans qu'aucun compteur ne bouge.
  // C'est donc la collision qu'on mesure, pas la hauteur.
  const over = await page.evaluate(() => {
    const ft = document.querySelector('.ft').getBoundingClientRect();
    const pg = document.querySelector('.page');
    let worst = null;
    for (const el of document.querySelectorAll('.body *')) {
      if (el.childElementCount || !el.textContent.trim()) continue;
      const b = el.getBoundingClientRect();
      if (b.bottom > ft.top + 0.5 && (!worst || b.bottom > worst.bottom)) {
        worst = { bottom: b.bottom, txt: el.textContent.trim().slice(0, 60) };
      }
    }
    return { over: pg.scrollHeight - pg.clientHeight, ftTop: ft.top, worst };
  });
  await page.pdf({ path: pdfPath, width: '210mm', height: '297mm', printBackground: true,
                   margin: { top: 0, right: 0, bottom: 0, left: 0 }, pageRanges: '1' });
  await browser.close();

  if (over.worst) {
    console.error(`⚠️  Texte masqué par le pied (${Math.round(over.worst.bottom - over.ftTop)}px) : « ${over.worst.txt}… »`);
    process.exitCode = 1;
  }
  if (over.over > 1) {
    console.error(`⚠️  Débordement de page : ${over.over}px.`);
    process.exitCode = 1;
  }
  console.log(`✓ ${path.relative(process.cwd(), pdfPath)}`);
  console.log(`  charte v${V.version} (${V.date}) · édition ${EDITION} · ${G.families.length} familles · ${C.length} paires mesurées`);
})();
