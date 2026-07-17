import {Config} from '@remotion/cli/config';

// Rendu MP4 : image intermédiaire en JPEG (plus rapide), écrasement autorisé.
Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);

// Dans un conteneur qui fournit déjà un Chromium complet (pas sur ton poste !),
// décommente ces deux lignes au lieu de passer les flags CLI à chaque commande :
// Config.setBrowserExecutable('/opt/pw-browsers/chromium');
// Config.setChromeMode('chrome-for-testing');
