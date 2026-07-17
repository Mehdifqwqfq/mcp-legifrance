/** Un trait dessiné du tableau blanc. */
export type StrokePath = {
  /** Attribut `d` d'un <path> SVG (repère 900×480). */
  d: string;
  /** Épaisseur du trait (défaut 5). */
  w?: number;
  /**
   * Poids relatif du temps de tracé (défaut 1). Le temps de dessin de la
   * scène est réparti au prorata : donne p.ex. 3 à un long trait et 0.5 à
   * une petite coche pour une vitesse de plume homogène.
   */
  weight?: number;
};

/** Une scène = un plan de la vidéo : un titre, une narration, des traits. */
export type Scene = {
  id: string;
  title: string;
  /** Texte lu par la voix off ET affiché en sous-titre. */
  narration: string;
  /** Couleur d'encre du marqueur pour cette scène. */
  color: string;
  /** Durée de la scène en secondes (idéalement = durée de l'audio). */
  durationInSeconds: number;
  /** Traits dessinés séquentiellement pendant la scène. */
  paths: StrokePath[];
  /** Fichier audio dans public/ (ex. "audio/scene-1.mp3"). Optionnel. */
  audio?: string;
};
