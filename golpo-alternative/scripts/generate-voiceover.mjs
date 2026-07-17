#!/usr/bin/env node
/**
 * Étape 2 — Générer les voix off (TTS) pour chaque scène.
 *
 * Lit un scenes.json (produit à l'étape 1, voir generate-script.md) et écrit
 * un MP3 par scène dans remotion/public/audio/scene-<n>.mp3.
 *
 * Fournisseurs supportés (au choix) :
 *   ELEVENLABS_API_KEY=...  node generate-voiceover.mjs scenes.json
 *   OPENAI_API_KEY=...      node generate-voiceover.mjs scenes.json --provider openai
 * (l'ordre fichier/options est libre ; --provider=openai marche aussi)
 *
 * Options :
 *   --provider elevenlabs|openai   (défaut : elevenlabs)
 *   --voice <id|nom>               (défaut : voix multilingue du fournisseur)
 *
 * Après génération : mesure la durée réelle de chaque MP3 —
 *   cd remotion && npx remotion ffprobe public/audio/scene-1.mp3
 * — reporte-la dans durationInSeconds de remotion/src/scenes.ts, puis
 * décommente les lignes `audio:` : la synchro image/son est alors exacte.
 */
import {readFile, writeFile, mkdir, readdir, unlink} from 'node:fs/promises';
import {dirname, join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT_DIR = resolve(HERE, '../remotion/public/audio');
const FETCH_TIMEOUT_MS = 120_000;

// ---- Parsing des arguments (fichier + flags, dans n'importe quel ordre) ----
const FLAGS_WITH_VALUE = new Set(['--provider', '--voice']);
let scenesPath = null;
let provider = 'elevenlabs';
let voiceArg = null;

const argv = process.argv.slice(2);
for (let i = 0; i < argv.length; i += 1) {
  const arg = argv[i];
  const eq = arg.indexOf('=');
  const name = arg.startsWith('--') ? (eq === -1 ? arg : arg.slice(0, eq)) : null;

  if (name && FLAGS_WITH_VALUE.has(name)) {
    const value = eq === -1 ? argv[++i] : arg.slice(eq + 1);
    if (value === undefined || value.startsWith('--')) {
      fail(`${name} attend une valeur (ex. ${name} openai)`);
    }
    if (name === '--provider') provider = value;
    else voiceArg = value;
  } else if (name) {
    fail(`Option inconnue : ${arg} (options valides : --provider, --voice)`);
  } else if (scenesPath === null) {
    scenesPath = arg;
  } else {
    fail(`Argument en trop : ${arg} (un seul fichier scenes.json attendu)`);
  }
}
scenesPath ??= join(HERE, 'scenes.example.json');

if (provider !== 'elevenlabs' && provider !== 'openai') {
  fail(`--provider "${provider}" inconnu — valeurs possibles : elevenlabs, openai`);
}

function fail(message) {
  process.stderr.write(`Erreur : ${message}\n`);
  process.exit(1);
}

// ---- Fournisseurs TTS ----
async function ttsElevenLabs(text, voice) {
  const key = process.env.ELEVENLABS_API_KEY;
  if (!key) throw new Error('ELEVENLABS_API_KEY manquant');
  // Voix par défaut : "George" (multilingue). Remplace par l'ID de ta voix préférée.
  const voiceId = voice ?? 'JBFqnCBsd6RMkjVDRZzb';
  const res = await fetch(
    `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}?output_format=mp3_44100_128`,
    {
      method: 'POST',
      headers: {'xi-api-key': key, 'content-type': 'application/json'},
      body: JSON.stringify({text, model_id: 'eleven_multilingual_v2'}),
      signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
    },
  );
  if (!res.ok) throw new Error(`ElevenLabs ${res.status}: ${await res.text()}`);
  return Buffer.from(await res.arrayBuffer());
}

async function ttsOpenAI(text, voice) {
  const key = process.env.OPENAI_API_KEY;
  if (!key) throw new Error('OPENAI_API_KEY manquant');
  const res = await fetch('https://api.openai.com/v1/audio/speech', {
    method: 'POST',
    headers: {authorization: `Bearer ${key}`, 'content-type': 'application/json'},
    body: JSON.stringify({
      model: 'gpt-4o-mini-tts',
      voice: voice ?? 'alloy',
      input: text,
      response_format: 'mp3',
    }),
    signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
  });
  if (!res.ok) throw new Error(`OpenAI ${res.status}: ${await res.text()}`);
  return Buffer.from(await res.arrayBuffer());
}

const tts = provider === 'openai' ? ttsOpenAI : ttsElevenLabs;

// ---- Validation des scènes ----
const scenes = JSON.parse(await readFile(scenesPath, 'utf8'));
if (!Array.isArray(scenes) || scenes.length === 0) {
  fail(`${scenesPath} doit contenir un tableau non vide de scènes`);
}
scenes.forEach((scene, idx) => {
  if (typeof scene?.narration !== 'string' || scene.narration.trim() === '') {
    fail(`Scène ${idx + 1} (${scene?.id ?? 'sans id'}) : champ "narration" vide ou manquant`);
  }
});

// ---- Génération (on purge d'abord les anciens scene-*.mp3 pour éviter
//      qu'un run partiel laisse traîner des audios d'un contenu précédent) ----
await mkdir(OUT_DIR, {recursive: true});
for (const old of await readdir(OUT_DIR)) {
  if (/^scene-\d+\.mp3$/.test(old)) await unlink(join(OUT_DIR, old));
}

let i = 0;
for (const scene of scenes) {
  i += 1;
  const out = join(OUT_DIR, `scene-${i}.mp3`);
  process.stdout.write(`[${i}/${scenes.length}] ${scene.id ?? 'scene'} → ${out}\n`);
  const audio = await tts(scene.narration, voiceArg);
  await writeFile(out, audio);
}

process.stdout.write(
  `\nOK — ${i} fichiers dans ${OUT_DIR}\n` +
    `Étape suivante : mesurer les durées réelles et les reporter dans scenes.ts ` +
    `(voir l'en-tête de ce script).\n`,
);
