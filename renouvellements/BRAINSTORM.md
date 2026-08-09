# Renouvellements — brainstorming fondateur

> **Statut** : brainstorming, rien n'est arbitré. Aucune ligne de code.
> **Date** : 2026-08-09 · **Portée** : architecture, spec, ergonomie, fonctionnalités.
> **Hors périmètre volontaire** : le choix d'infra OVHcloud est traité ici *seulement* là où
> il contraint la conception (périmètre HDS). Le cadrage OVH complet vient à la fin, comme prévu.

---

## 0. Résumé en une page

> **Le sujet, c'est la préparation à l'avance. Pas la livraison.** Ce qu'on transpose d'Amazon, c'est
> la *prédiction du réapprovisionnement* — savoir avant le client qu'il va manquer. Pas la logistique
> qui va avec, qui est de toute façon fermée en France (§1.1).

L'intuition « abonnement Amazon pour les médocs » est juste sur le **besoin** et fausse sur la
**mécanique commerciale**. Ce qui reste — et qui est en réalité *meilleur* que l'abonnement Amazon —
c'est le **rendez-vous mensuel de renouvellement** : l'officine sait, à la semaine près, quand chaque
patient chronique va tomber en panne de traitement ; elle prépare le sachet à l'avance, regroupe les
lignes, anticipe le stock, et le patient fait **un** passage par mois au lieu de trois.

Ce modèle a un nom et une littérature (*Appointment-Based Model* / *med sync*), avec des gains
d'observance mesurés — de l'ordre de 3 à 6× plus de chances d'être adhérent (PDC ≥ 80 %), et une
réduction nette du nombre de passages. Ce n'est donc pas un gadget de fidélisation déguisé : c'est
un acte pharmaceutique documenté, qui se trouve aussi être excellent commercialement.

**Trois décisions structurantes que je recommande :**

1. **Renommer le concept dès maintenant** : ce n'est pas un abonnement, c'est un *plan de
   renouvellement*. Le mot « abonnement » vous expose inutilement sur le terrain déontologique
   (sollicitation de clientèle, R.4235-22) pour zéro gain fonctionnel.
2. **Phase 0 en lecture seule, sans le patient.** Ingérer 12 mois d'historique, prédire les dates
   de fin de traitement, comparer aux retraits réels. Si le moteur ne prédit pas à ±3 jours, le
   reste du produit n'existe pas. C'est un go/no-go à 2–3 semaines, quasi sans risque juridique.
3. **Régler la question HDS *avant* d'écrire la V1 multi-officine.** Héberger les données de tes 3
   participations, c'est héberger pour le compte de tiers : ça peut obliger EtikPharma elle-même à
   se certifier HDS, pas seulement à louer de l'OVH certifié. Mono-officine d'abord.

---

## 1. Le droit décide du produit — avant l'architecture

Il faut prendre ça dans cet ordre, parce que trois interdits éliminent d'emblée la moitié des
fonctionnalités qu'on aurait spontanément dessinées.

### 1.1 Ce qui est fermé

| Interdit | Conséquence produit |
|---|---|
| **La vente en ligne de médicaments sur prescription est interdite.** Seuls les médicaments non soumis à prescription peuvent être vendus en ligne, depuis un site adossé à une officine physique et déclaré au DG de l'ARS. | Pas de panier, pas de paiement en ligne, pas de « renouvellement en 1 clic » sur des médicaments d'ordonnance. Le paiement et la délivrance restent au comptoir. |
| **La livraison à domicile n'est pas un service par défaut.** Encadrée (CSP, R.5125-45 à R.5125-52), réservée aux patients dans l'impossibilité de se déplacer — état de santé, âge, situation géographique. L'Ordre est en campagne active contre les offres qui s'affranchissent de ce cadre. | *Hors sujet ici de toute façon* — mais il faut le savoir, parce que c'est le premier réflexe de quiconque entend « abonnement ». Réponse définitive : **non**, et ce n'est même pas une phase ultérieure. |
| **Sollicitation de clientèle** : interdiction de solliciter la clientèle par des procédés contraires à la dignité de la profession (R.4235-22). La publicité en faveur de l'officine est désormais possible sur tout support, mais elle doit réserver une part prépondérante aux messages de santé publique, rester loyale, sans témoignages de tiers ni comparaison avec d'autres pharmacies. | Les notifications doivent être des **messages de suivi de traitement**, pas des relances commerciales. Pas de remise, pas d'avantage, pas de parrainage. L'inscription se fait au comptoir, en face à face, jamais par campagne de masse. |

> **À retenir** : tout ce qui fait le *commerce* d'Amazon — le clic, le paiement récurrent,
> l'expédition, la remise abonné — est précisément ce qui est fermé ici. Ce qui reste disponible,
> c'est le seul morceau qui avait de la valeur : **le moteur qui sait quand tu vas être à court.**
> Chez Amazon il déclenche un colis ; ici il déclenche une préparation.

### 1.2 Ce qui est ouvert — et qui fait le produit

| Levier | Ce qu'il permet |
|---|---|
| **La e-réservation / préparation de commande.** Le patient transmet son ordonnance, l'officine prépare, le patient retire et paie au comptoir. C'est légal et déjà pratiqué. | C'est le cœur du parcours. On n'invente rien, on l'industrialise et on l'anticipe. |
| **La délivrance fractionnée d'un mois** (R.5123-2 : pas plus de 4 semaines ou 30 jours par délivrance selon conditionnement). | Le rythme réglementaire *est* le rythme du produit. La cadence mensuelle n'est pas un choix marketing, c'est la loi. Cadeau. |
| **La dispensation supplémentaire exceptionnelle** — décret n° 2024-1070 du 26 novembre 2024, applicable depuis le 29/11/2024. Ordonnance renouvelable expirée : le pharmacien dispense jusqu'à **3 mois, par délivrances successives d'un mois**, pour la poursuite d'un traitement chronique. Conditions : ordonnance initiale de 3 mois ou plus, première délivrance dans le mois suivant l'expiration. Exclus : les médicaments dont la durée de prescription est limitée à 12 semaines (hypnotiques, anxiolytiques, tramadol). | **C'est le moteur légal de la promesse « ton traitement ne s'arrête jamais ».** Et c'est un gisement d'alertes : fenêtre d'un mois à ne pas rater, compteur de 3 mois à tenir, exclusions à filtrer automatiquement. Un humain ne suit pas ça de tête sur 400 patients. Une machine, si. |
| **L'ordonnance numérique**, obligatoire en ville depuis le 31/12/2024–01/01/2025, en généralisation chez les prescripteurs et les officines en 2026. Pharmony One fait partie des dix logiciels ayant achevé la présérie et autorisés au déploiement national (avril 2026). | La source d'entrée propre, et elle est déjà là : prescriptions structurées plutôt que photo d'ordonnance. À ne pas construire en V1, mais le modèle de données doit l'accueillir dès le départ — et le moteur de prédiction en profite directement (§3.1). |

### 1.3 Reformulation

> **Ce n'est pas un abonnement produit. C'est un plan de renouvellement piloté par l'officine, avec
> un rendez-vous mensuel, une préparation anticipée, et un filet de sécurité réglementaire.**

Cette phrase est la spec. Tout ce qui suit en découle.

---

## 2. Le modèle cible : le rendez-vous mensuel

Le modèle de référence existe et est évalué : l'*Appointment-Based Model* (ABM), aussi appelé
*medication synchronization*. Principe : au lieu de subir des retraits dispersés, on aligne toutes
les lignes chroniques d'un patient sur une **date commune mensuelle**, l'officine appelle ou notifie
quelques jours avant, prépare tout, et le patient vient une fois.

Ce que la littérature en dit, en substance :

- adhésion (PDC ≥ 80 %) multipliée par **3,4 à 6,1** chez les patients inscrits vs non inscrits ;
- augmentation significative du PDC en continu, quelle que soit la classe pharmacologique ;
- réduction franche du nombre de dates de retrait (de ~6,8 à ~4,9 sur 6 mois dans une des études) ;
- ROI positif documenté pour l'officine ; l'impact sur les *résultats cliniques finaux* reste, lui,
  insuffisamment établi — ne pas survendre ce point.

**Pourquoi c'est le bon modèle pour toi, précisément :**

- il transforme une demande subie (le patient arrive quand il veut, souvent en rupture) en **charge
  planifiée** — donc lissable sur les heures creuses, donc compatible avec ton app Planning ;
- il rend le stock **prévisible à 4 semaines**, ce qui alimente directement la commande et le
  Copilote ACHAT ;
- il est défendable devant l'Ordre parce qu'il est clinique avant d'être commercial ;
- il ne dépend pas de l'adoption numérique des patients : même avec 0 % de patients connectés,
  l'officine gagne. Le canal patient est un accélérateur, pas une dépendance. **C'est le point
  d'ergonomie le plus important de tout ce document.**

---

## 3. Fonctionnalités

### 3.0 La préparation anticipée — l'acte central

C'est l'objet du produit, tout le reste le sert. Le cycle, pour un patient :

```
   J-30    le moteur pose une date de rendez-vous prévisionnelle
   J-10    la ligne entre au prévisionnel de commande → le stock est sécurisé
   J-5     l'officine prépare : picking, bac nominatif, contrôle pharmaceutique
           (+ notification patient si, et seulement si, il a un canal — P2)
   J-0     le patient passe, le bac l'attend, la délivrance prend 2 minutes
           au lieu de 10
   J+1     l'écart entre date prévue et retrait réel réalimente le moteur
```

Ce que « préparer à l'avance » change réellement, et qui n'est pas évident :

- **Le travail se déplace dans le temps.** La délivrance d'un chronique polymédiqué, c'est
  aujourd'hui 8 à 12 minutes en pleine affluence. Préparée la veille en heure creuse, elle coûte le
  même temps total mais plus au même moment. À volume constant, on décharge le pic.
- **La rupture se découvre 10 jours plus tôt.** Le manquant se constate au picking, pas devant le
  patient. On a le temps de commander, de substituer, ou de prévenir. C'est le gain le plus
  immédiatement monétisable.
- **Le contrôle pharmaceutique se fait au calme.** Analyser une ordonnance de 7 lignes avec un
  patient qui attend et trois personnes derrière lui, ce n'est pas de l'analyse. Anticipée, elle
  devient réelle — et c'est là que les alertes du §3.3 se déclenchent utilement.
- **Le patient n'attend plus.** C'est le seul bénéfice qu'il perçoit, et il suffit largement.

**Le préalable dur** : on ne peut préparer à l'avance que ce qu'on sait prévoir. D'où le §3.1, qui
est la condition d'existence de tout le reste.

### 3.1 Le moteur de prédiction — le cœur

Tout repose sur une seule question : *quand ce patient tombe-t-il en panne de cette ligne ?*

```
jours_couverts    = (nb_boîtes × unités_par_boîte) / doses_par_jour
date_fin_estimée  = date_délivrance + jours_couverts
date_rendez_vous  = date_fin_estimée − marge          (défaut : 7 jours)
```

Trivial sur le papier. Les difficultés réelles :

| Difficulté | Traitement proposé |
|---|---|
| `unités_par_boîte` | Résolu par le CIP13 via la BDPM — tu as déjà le tool `fiche_medicament` dans Domi. À réutiliser, pas à réécrire. |
| `doses_par_jour` : la posologie est du texte libre (« 1 cp matin et soir », « ½ le matin, 1 le soir », « 1 cp/j sauf le dimanche ») | Grammaire déterministe sur les ~50 motifs qui couvrent l'essentiel, **plus** un repli LLM sur la queue de distribution, avec un **score de confiance** stocké. Une ligne à faible confiance n'entre pas dans un plan automatique : elle part en file de validation humaine. **À vérifier avant de coder** : Pharmony One étant référencé Ségur et déployé sur l'ordonnance numérique, une part des prescriptions récentes est peut-être déjà structurée dans le LGO. Si c'est le cas, la difficulté s'effondre sur le flux récent — et ne subsiste que sur l'historique et les ordonnances d'origine papier. |
| Posologie non prédictible (« si besoin », « à la demande ») | Ne jamais planifier. Statut `cadence_indéterminée`. Mieux vaut un trou assumé qu'une fausse promesse. |
| Formes non unitaires : crèmes, collyres, sprays, inhalateurs, stylos d'insuline | Le comptage d'unités n'a pas de sens. Table d'heuristiques par forme galénique (durée d'usage typique), confiance basse par construction, recalibrée par l'observation des retraits réels. |
| Schémas séquentiels : contraception 21/28, décroissance de corticoïdes | Cas particuliers explicites, pas de généralisation hasardeuse. |
| Le patient n'observe pas : la date réelle dérive de la date prévue | **C'est une fonctionnalité, pas un bug.** L'écart prévu/réel *est* la mesure d'observance. On en tire le PDC par patient et par ligne. |

Deux détections qui tombent gratuitement du moteur et qui ont une vraie valeur pharmaceutique :

- **retard de retrait** au-delà d'un seuil → rupture d'observance, à rattraper ;
- **retraits trop rapprochés** → suspicion de mésusage ou de nomadisme. Un outil qui ne sait que
  vendre plus n'aurait jamais cette alerte. Celui-là l'a, et c'est ce qui le rend défendable.

### 3.2 La synchronisation — la fonctionnalité qui différencie

Un patient polymédiqué a 5 lignes qui finissent à 5 dates différentes, parce que les
conditionnements ne font pas tous 30 jours (28, 30, 90…). Le regroupement sur une date unique est
le vrai service rendu, et Amazon n'a pas d'équivalent.

L'algorithme d'alignement, en une règle :

> **On aligne en raccourcissant, jamais en allongeant.**

Concrètement : on choisit une date d'ancrage T (le prochain rendez-vous), et sur le premier cycle on
délivre volontairement « court » sur les lignes en avance, pour que toutes retombent ensemble à
T+30. Le reliquat demeure sur l'ordonnance. C'est de la délivrance fractionnée ordinaire.

Pourquoi la règle est stricte dans ce sens : allonger, ce serait délivrer plus que nécessaire, et se
heurter au plafond d'un mois par délivrance (R.5123-2). Raccourcir est toujours possible, jamais
sanctionnable, et sans coût pour le patient. La contrainte réglementaire tranche l'algorithme —
c'est confortable.

Sortie attendue : un `plan_renouvellement` par patient, avec une date de rendez-vous, la liste des
lignes, et pour chacune la quantité à préparer ce mois-ci.

### 3.3 Le moteur de vigilance — le catalogue d'alertes

C'est ici que l'outil cesse d'être un agenda et devient un copilote. Chaque alerte a un
déclencheur, une sévérité et une action proposée.

| # | Alerte | Action proposée |
|---|---|---|
| 1 | Ordonnance expire dans X jours | Prévenir le patient qu'il doit revoir son médecin, avant la panne |
| 2 | Ordonnance expirée, **éligible dispensation supplémentaire** (décret 2024-1070) | Proposer la dispensation, avec compteur des 3 mois et filtrage automatique des exclusions (12 semaines : hypnotiques, anxiolytiques, tramadol) |
| 3 | Retard de retrait > seuil | Relance de suivi, tracer la non-observance |
| 4 | Retraits trop rapprochés | Revue pharmaceutique, suspicion de mésusage |
| 5 | Rupture de stock prévue sur une ligne planifiée | Anticiper : commander tôt, préparer la substitution, prévenir |
| 6 | Ligne désynchronisée du plan | Proposer la resynchronisation au prochain passage |
| 7 | Patient ≥ 65 ans et ≥ 5 lignes chroniques | Éligible bilan partagé de médication — acte rémunéré, et lien direct vers BilanbyEtikPharma |
| 8 | Ligne apparue / disparue entre deux ordonnances | Changement de traitement à faire valider |
| 9 | Interaction ou redondance détectée | Brancher SafebyEtikPharma plutôt que réimplémenter |
| 10 | Suivi biologique attendu (INR, kaliémie sous IEC…) | **V2, prudemment** — c'est de l'analyse clinique, ça se conçoit avec un cadre, pas en passant |

L'alerte 2 mérite d'être soulignée : elle transforme un décret difficile à appliquer à la main en
avantage systématique. Sur 400 patients chroniques, personne ne suit de tête qui est dans sa fenêtre
d'un mois post-expiration et à combien de mois de compteur. La machine, oui.

### 3.4 Le couplage stock — le retour sur investissement le plus direct

Chaque renouvellement planifié réserve des CIP. Agrégé sur 4 semaines, ça donne un **prévisionnel de
besoin ferme** — pas une extrapolation statistique, une liste nominative de lignes déjà engagées.

Ce que ça débloque :

- détecter une rupture *avant* qu'elle ne frappe un patient identifié, et non le jour du comptoir ;
- commander sur du connu plutôt que sur de l'historique lissé ;
- alimenter les arbitrages génériques et les négociations labo — le Copilote Titulaire a déjà les
  tools, il lui manque la demande future.

C'est probablement le poste de ROI le plus facile à chiffrer, et il faut le chiffrer **sur tes
données** (Pharmanuage, `v_prix_achat_reel`, `v_ca_verite_unique`), pas sur des moyennes de presse
professionnelle. La règle R5 s'applique : Pharmanuage fait foi.

### 3.5 Ce qu'on ne construit pas — anti-scope explicite

À écrire noir sur blanc maintenant, sinon ça reviendra par la fenêtre à chaque réunion :

- pas de vente ni de paiement en ligne de médicaments d'ordonnance ;
- pas de livraison par défaut, pas de plateforme de livraison, pas d'intégration coursier ;
- pas de remise, avantage, points ou parrainage liés à l'inscription ;
- pas de conseil médical généré et envoyé au patient sans validation pharmacien ;
- pas de contact automatique du prescripteur sans validation humaine ;
- **aucune écriture dans le LGO.** L'outil lit, il n'écrit jamais. Cette règle n'a pas d'exception.

---

## 4. Ergonomie

### 4.1 Trois principes, dans l'ordre

1. **Le comptoir n'a pas 30 secondes.** Toute action qui coûte plus de ~5 secondes au comptoir ne
   sera pas faite, quelle que soit sa valeur. Le travail de fond se fait en back-office.
2. **L'outil doit fonctionner avec 0 % d'adoption patient.** Si la valeur dépend du fait que des
   patients de 78 ans cliquent sur un lien SMS, il n'y a pas de produit.
3. **Ne pas combattre le papier.** Une officine tourne en partie sur des feuilles imprimées. Il faut
   une fiche de préparation imprimable dès le premier jour.

### 4.2 Côté officine

**L'écran principal : le mur du jour**, pas un tableau de bord. Quatre colonnes, une carte par
patient : `À préparer` → `Prêt` → `Notifié` → `Retiré`. Une carte affiche le patient, le nombre de
lignes, des pastilles d'alerte, et un seul bouton d'action. Pas de graphique sur cet écran.

**La vue semaine** : la charge prévisionnelle sur 4 semaines, en nombre de préparations par jour.
C'est ce qui permet de lisser — décaler des rendez-vous vers les creux, et brancher ça sur le
Planning.

**La préparation** : un clic génère la liste de picking. Et comme le robot NEV existe déjà, la vraie
cible est d'envoyer directement la liste au robot pour qu'il sorte les boîtes dans un bac nominatif.
C'est le genre d'intégration que personne d'autre ne peut faire chez toi, parce que le RPA est déjà
maîtrisé.

**L'inscription d'un patient** doit coûter un clic. L'outil propose de lui-même : « ce patient a 6
lignes chroniques et 4 passages sur les 3 derniers mois — l'inscrire au plan ? [Oui] ». On ne
demande pas à l'équipe de repérer les candidats : c'est le travail de la machine.

**Au comptoir**, un seul signal : un badge « plan de renouvellement — bac prêt ». Rien d'autre.

### 4.3 Côté patient

Volontairement minimal. Pas d'application à installer — ça ne marchera pas sur cette population.

- **SMS à J-5** : « Bonjour, votre pharmacie prépare votre renouvellement pour le [date].
  Confirmer ou reporter : [lien] ». **Aucun nom de médicament dans le SMS** — un SMS s'affiche sur
  un écran verrouillé, potentiellement devant n'importe qui. C'est une contrainte de confidentialité
  autant que d'ergonomie.
- **La page web** : second facteur léger (date de naissance) avant d'afficher quoi que ce soit de
  médical. Puis trois boutons, gros : `Je confirme` · `Je reporte` (sélecteur de date) · `J'arrête`.
  Plus une quatrième action : `J'ai une nouvelle ordonnance` (photo).
- **Le repli, qui est le cas majoritaire** : le patient n'est pas joignable numériquement, ou ne
  répond pas. Il passe en *mode silencieux* : l'officine organise, prépare, et l'appelle. Aucune
  dégradation du service, juste un canal différent.

Accessibilité : gros corps de texte, contraste élevé, pas de jargon, pas de compte, pas de mot de
passe. Le patient qui n'y arrive pas doit pouvoir raccrocher sans conséquence.

### 4.4 Le point de friction à ne pas sous-estimer

Le vrai risque d'échec de ce produit n'est pas technique, il est humain : **si l'équipe ne préparait
pas déjà les renouvellements, l'outil crée du travail avant d'en économiser**. Il faut donc que la
Phase 1 démarre sur un sous-ensemble de patients volontaires (30–50), pas sur la file entière, et
que le gain de temps soit mesuré sur ce sous-ensemble avant l'extension.

---

## 5. Architecture

### 5.1 Vue d'ensemble

```
┌─ LGO PHARMONY ONE — cloud natif, référencé Ségur ──────────┐
│  Depuis le 2026-07-06 (bascule effective, coupure Smart RX)│
│  Connecteur — cloud→cloud, pas d'agent sur poste Windows   │
│  · extraction délivrances + ordonnances (nuit)             │
│  · LECTURE SEULE, jamais d'écriture dans le LGO            │
│  · file + reprise sur incident, côté enclave               │
└───────────────────────┬────────────────────────────────────┘
                        │  HTTPS, sortant uniquement
                        ▼
┌─ ENCLAVE HDS — OVHcloud, région France ────────────────────┐
│  API                 (Public Cloud instance, HDS)          │
│  PostgreSQL          (Cloud Databases, HDS)                │
│  Object Storage      (scans d'ordonnances, chiffrés)       │
│  Logs / audit        (Logs Data Platform, HDS)             │
│  Moteur : prédiction · synchronisation · vigilance         │
│  LLM posologie       (AI Endpoints / ML Serving, HDS)      │
│  Front officine + page patient servis depuis l'enclave     │
└───────────────────────┬────────────────────────────────────┘
                        │  agrégats anonymisés uniquement
                        ▼
┌─ HORS PÉRIMÈTRE SANTÉ (l'existant, inchangé) ──────────────┐
│  Supabase shuvawbdvfjxohuxvmhp — KPI agrégés               │
│  Copilote Titulaire · Netlify · Anthropic                  │
└────────────────────────────────────────────────────────────┘
```

Le point non négociable de ce schéma : **la frontière est étanche et elle ne se traverse que dans un
sens, avec des agrégats**. Aucune donnée nominative de santé ne descend vers Supabase, Netlify ou
l'API Anthropic. C'est la seule discipline qui rend l'ensemble auditable.

Servir aussi le front depuis l'enclave (plutôt que Netlify) coûte un nginx et évite toute discussion
sur l'origine, le CSP et les jetons. Sur ce projet précis, ça vaut la rupture d'habitude.

### 5.2 Le périmètre HDS — et le piège à connaître tout de suite

Le cadre : article L.1111-8 CSP — tout hébergement de données de santé à caractère personnel **pour
le compte d'un tiers** doit être réalisé par un hébergeur certifié.

Ce qui en découle, et qui n'est pas intuitif :

- **Une structure qui héberge ses propres données, sur ses propres serveurs, n'est pas soumise à
  l'obligation de certification.** Mais dès qu'on passe par un cloud, l'infrastructure sous-jacente
  doit être certifiée HDS. → OVHcloud coche cette case.
- **Le piège** : dès lors que l'éditeur administre l'application, assure l'infogérance ou gère les
  sauvegardes pour le compte du client, il doit **lui-même** détenir la certification HDS. Autrement
  dit : le jour où EtikPharma opère cet outil pour Rochechouart, Cardinet ou Saint-Georges, louer de
  l'OVH certifié ne suffit plus — c'est EtikPharma qui devient hébergeur.

Trois issues, à arbitrer plus tard mais à connaître maintenant :

1. **Mono-officine d'abord** (Pharmacie des Théâtres, tes propres données, ton propre responsable de
   traitement). Pas d'hébergement pour compte de tiers → pas de certification EtikPharma requise.
   C'est la voie de la Phase 1, et elle est propre.
2. **Certifier EtikPharma** le jour du réseau. Coûteux en temps et en argent, audit AFNOR, SMSI à
   monter. À ne pas découvrir six mois trop tard.
3. **S'abriter sous un opérateur déjà certifié.** Bunka.ai figure déjà dans ton HANDOFF comme
   partenaire pressenti pour la Queue Intelligente, précisément sur ce motif. **Les deux chantiers
   posent la même question HDS — autant la résoudre une fois pour les deux.**

Côté OVHcloud, ce qu'il faut retenir pour la conception : la certification couvre des produits
précis, pas le catalogue entier, et l'éligibilité suppose un niveau de support **Business ou
Enterprise** plus la signature de l'**avenant santé** (*OVHcloud Healthcare Addendum*). Ce n'est pas
un détail contractuel : c'est un coût récurrent à intégrer au budget dès maintenant.

> ⚠️ Les pages officielles OVHcloud et l'Ordre étaient inaccessibles depuis cet environnement
> (blocage proxy). La liste des produits couverts ci-dessus provient de résumés de recherche et
> **doit être revérifiée sur la documentation OVHcloud avant tout engagement**. Idem pour le détail
> de la fiche professionnelle CNOP sur la livraison à domicile.

### 5.3 L'accès aux données du LGO

**Le LGO est tranché : Pharmony One, en production depuis le 2026-07-06** (bascule effective,
coupure Smart RX / Offisanté). Ça change trois choses par rapport à l'hypothèse Smart RX.

**1. Il n'y a plus d'agent local à écrire.** Pharmony One est un LGO **nativement cloud** — le
premier référencé Ségur en cloud natif en France. Le pattern Robot NEV (PyAutoGUI sur client lourd
Windows) n'a plus d'objet ici : il n'y a pas de client lourd à piloter. On vise un connecteur
cloud→cloud, sans machine à maintenir dans l'officine, sans poste allumé la nuit, sans casse à
chaque mise à jour du LGO. C'est une simplification majeure de l'architecture — et une source
d'incidents en moins.

**2. Le mode d'accès se cherche autrement.** Options, de la meilleure à la moins bonne :

| Voie | Réaliste ? |
|---|---|
| **API éditeur** | La meilleure. Pharmony se positionne sur l'interopérabilité et le cloud — la question a des chances d'aboutir. **À poser à l'éditeur en premier**, avant toute ligne de code. |
| **Export planifié** (délivrances, format tabulaire) déposé sur un point de collecte | Le compromis pragmatique si l'API n'existe pas ou tarde. Robuste, peu couplé, négociable rapidement. |
| **Rétro-ingénierie de la session web** | LGO cloud = application web authentifiée. C'est exactement le terrain de ton skill `scraping-pharma-platforms`, et la règle R6 s'applique : capturer l'appel natif dans DevTools avant d'écrire quoi que ce soit. Le repli crédible — mais un repli, pas une cible : il n'a aucune garantie de stabilité et se négocie mal avec un éditeur. |
| Téléservice ordonnance numérique en direct | Hors de portée : réservé aux LGO référencés. On passe *par* Pharmony, pas à côté. |
| Dossier Pharmaceutique | Pas d'accès applicatif tiers. À écarter. |

**3. L'ordonnance numérique n'est plus un horizon lointain.** Pharmony One figure parmi les dix
logiciels ayant achevé la présérie et autorisés au déploiement national (avril 2026). Les
prescriptions récentes arrivent donc potentiellement **structurées** dans le LGO — ce qui attaque de
front la principale difficulté du moteur de prédiction (§3.1). À vérifier concrètement&nbsp;: ce que
l'ordonnance numérique porte de la posologie, et sous quelle forme.

> **Ce qu'il reste à lever, et c'est la seule inconnue bloquante** : ce que Pharmony expose, et à
> quelles conditions. Une question à l'éditeur, pas un problème d'ingénierie. Tant qu'elle n'est pas
> répondue, la P0 se fait sur un export manuel — voir §7.

*Note de gouvernance* : le conseil de gérance du 05/08 listait la bascule comme « passée, non
soldée », avec zéro commit Pharmony depuis le 06/07. C'était une observation sur la **visibilité
dans le dépôt**, pas sur la réalité opérationnelle — la bascule a bien eu lieu. L'écart entre les
deux est précisément ce que ce conseil signale semaine après semaine.

### 5.4 Modèle de données — les entités qui comptent

```
officine(finess, raison_sociale)                          ← tenant
patient(id, nom, prénom, ddn, lgo_patient_id, contact,
        consentement, canal_préféré, statut)
prescripteur(rpps, nom)
ordonnance(id, patient, prescripteur, date_prescription,
           durée_prescrite, renouvellements,
           date_expiration_calculée, source, statut)
ligne_ordonnance(ordonnance, cip13, ucd, posologie_texte,
                 posologie_structurée, confiance_parsing,
                 ald, substituable)
délivrance(date, ligne, nb_boîtes, unités_par_boîte,
           jours_couverts_calculés)
plan_renouvellement(patient, lignes[], date_rendez_vous,
                    cadence, statut, mode_retrait)         ← le cœur
événement_renouvellement(plan, occurrence, statut,
                         horodatages, opérateur)
alerte(type, sévérité, cible, statut, date_échéance)
consentement(patient, finalité, canal, date, preuve)
journal_audit(...)                                         ← immuable
```

Deux choix à acter tôt :

- **Multi-tenant dès le schéma**, même si la Phase 1 est mono-officine. Tenant = officine (FINESS),
  isolation par RLS. Tu as déjà ce réflexe sur ProCS ; rétrofitter du multi-tenant coûte dix fois
  plus cher que le prévoir.
- **L'INS** (Identité Nationale de Santé) n'est pas nécessaire tant que rien n'est échangé avec
  d'autres acteurs de santé. Prévoir le champ, ne pas le remplir en V1.

### 5.5 L'IA dans le périmètre — la rupture d'habitude

Ton réflexe écosystème, c'est l'API Anthropic derrière un proxy Netlify. **Ici, non.** Envoyer
posologie + médicament + patient à un service non-HDS hors UE, c'est un transfert de données de
santé hors périmètre.

Deux sorties propres, cumulables :

1. **Détacher la donnée.** Le parsing de posologie n'a besoin ni du nom, ni de l'INS, ni de l'ID
   patient : il a besoin de la chaîne `"1 cp matin et soir"` et de la forme galénique. Un appel
   strictement dépersonnalisé, sans identifiant ni possibilité de rattachement, sort du champ.
   Discipline stricte à imposer dans le code, pas dans la doctrine.
2. **Rester dans l'enclave.** OVHcloud AI Endpoints / ML Serving figure dans le périmètre HDS : un
   modèle ouvert hébergé là traite la donnée sans jamais sortir. Plus lourd, mais sans débat.

Recommandation : parser déterministe pour l'essentiel, option 2 pour la queue, option 1 seulement si
l'option 2 s'avère trop lente ou trop chère — et jamais pour autre chose que la posologie.

### 5.6 Notifications

SMS et e-mail sont des sous-traitants au sens RGPD : contrat, DPA, hébergement UE. OVHcloud propose
une API SMS, ce qui permet de rester sur un seul contrat et un seul périmètre — c'est un argument de
simplification juridique plus que technique.

Règle de contenu, sans exception : **aucun nom de médicament, aucune pathologie, aucune posologie
dans un SMS ou un e-mail.** Le message dit qu'un renouvellement est prêt, et rien de plus.

---

## 6. Conformité — la check-list à ouvrir dès la Phase 1

- **Base légale** : article 9.2.h RGPD (prise en charge sanitaire, sous secret professionnel) pour
  le traitement de soin lui-même ; **consentement explicite distinct** pour le canal de notification.
  Les deux, pas l'un ou l'autre.
- **AIPD obligatoire** — traitement de données de santé à grande échelle. À faire *avant* la mise en
  production, pas après.
- **Registre des traitements** à mettre à jour.
- **Consentement patient** recueilli au comptoir, tracé (date, canal, support), révocable en un clic.
  Le mode silencieux doit rester possible sans consentement au canal numérique.
- **Durée de conservation** : à fixer explicitement (proposition : purge ou anonymisation 3 ans après
  la dernière délivrance), avec un job planifié qui l'exécute réellement. Le précédent
  `retro.demands` est parlant : une anonymisation « manuelle au-delà de 30 jours » n'est pas une
  anonymisation, c'est une intention.
- **Journal d'audit immuable** : qui a consulté quel dossier patient, quand. Non négociable en santé,
  et c'est ce que les Logs Data Platform HDS servent à porter.
- **Volet ordinal** : formuler le service comme un suivi de traitement. Pas de remise, pas de
  comparaison avec d'autres officines, pas de témoignages patients, part prépondérante de santé
  publique dans toute communication publique. Si un jour tu communiques dessus, c'est cette grille
  qu'il faut passer avant publication.

---

## 7. Trajectoire

| Phase | Contenu | Durée indicative | Critère de passage |
|---|---|---|---|
| **P0 — Le radar** | Lecture seule. Ingestion de 12 mois d'historique, moteur de prédiction, comparaison prévu/réel. Zéro patient, zéro notification, zéro écriture. | 2–3 semaines | **Go/no-go** : erreur médiane sur la date de fin ≤ 3 jours, et ≥ 80 % des lignes parsées en confiance haute. Sinon, on s'arrête et on répare le moteur. |
| **P1 — Le plan** | Mur du jour, préparation, statuts, alertes 1–5, prévisionnel de stock. Mono-officine, 30–50 patients volontaires. Toujours aucun canal patient. | 4–6 semaines | Temps de préparation mesuré en baisse, et l'équipe ouvre l'outil sans qu'on le lui demande. |
| **P2 — Le rendez-vous** | Consentement, SMS, page patient, synchronisation des lignes, alertes 6–9. | 4–6 semaines | Taux de retrait à date, PDC en hausse sur la cohorte, zéro réclamation. |
| **P3 — Le réseau** | Multi-officine, intégration Copilote. | — | **Bloqué par la question HDS** (§5.2). Ne pas démarrer avant arbitrage. |

Il n'y a pas de phase livraison, ni maintenant ni plus tard. Le produit s'arrête au bac préparé qui
attend le patient au comptoir.

La forme de cette trajectoire n'est pas neutre : **les deux premières phases ne touchent pas au
patient**, donc elles ne consomment ni consentement, ni exposition ordinale, ni capital de confiance,
tant que le moteur n'a pas prouvé qu'il prédit juste.

---

## 8. Ce qu'on mesure

**Moteur** — erreur médiane en jours sur la date de fin ; part des lignes en confiance haute ; part
des lignes en `cadence_indéterminée`.

**Produit** — taux de retrait à la date prévue ; PDC moyen de la cohorte vs témoins ; nombre de
passages évités par patient et par trimestre.

**Officine** — ruptures anticipées vs subies ; heures de préparation déplacées hors des pics ; marge
captée sur les lignes chroniques (chiffrée sur Pharmanuage, règle R5).

**Garde-fous** — taux de désinscription ; nombre de réclamations patients ; **zéro signalement
ordinal**. Si le taux de désinscription grimpe, c'est que le produit est perçu comme du marketing :
c'est le signal d'alarme le plus important du tableau.

---

## 9. Décisions qui te reviennent

Rien dans ce document ne bloque le démarrage de la P0. Ces cinq points bloquent la suite :

1. **Ce que Pharmony expose** — le LGO est tranché (Pharmony One depuis le 06/07), la question qui
   reste est l'accès : API éditeur, export planifié, ou rien. C'est un appel à passer, pas un
   problème d'ingénierie, et c'est la seule inconnue qui borne l'architecture d'ingestion. À poser
   dans la foulée : ce que l'ordonnance numérique porte de la posologie structurée.
2. **Périmètre initial** — Théâtres seule (recommandé) ou d'emblée les 4 officines ? La réponse
   change le régime HDS, pas seulement l'échelle.
3. **HDS réseau** — certification EtikPharma, abri Bunka.ai, ou contrats OVH séparés par officine ?
   À instruire en même temps que la Queue Intelligente, qui pose la même question.
4. **Nom** — « abonnement » est à écarter pour les raisons du §1.1. Dans ta convention `xxxbyEtikPharma` :
   **Cadence** (le rythme, pas le commerce) a ma préférence ; *Fil* et *Relève* sont les alternatives
   que je garderais. Décision sans urgence.
5. **Ambition** — outil interne pour tes officines, ou produit destiné à être vendu à d'autres
   pharmacies ? La deuxième réponse déclenche la certification HDS, un tout autre budget, et devrait
   être décidée maintenant plutôt que découverte en P3.

---

## 10. Prochaine étape proposée

**Une seule** : la P0, sur données réelles.

Concrètement — extraire 12 mois de délivrances des Théâtres, écrire le parseur de posologie et le
calcul de date de fin, et produire un unique tableau : *date prédite vs date réelle de retour*, ligne
par ligne. Rien d'autre. Pas d'interface, pas de base hébergée, pas de patient. Un notebook et un CSV.

**La P0 n'attend pas la réponse de Pharmony** : un export manuel depuis l'interface suffit
largement pour 12 mois d'historique sur une officine. C'est même préférable — on valide le moteur
avant d'investir dans le tuyau, et on saura exactement quels champs demander à l'éditeur.

Si l'erreur médiane tient sous 3 jours, tout le reste de ce document devient constructible. Si elle
ne tient pas, on aura dépensé deux semaines au lieu de six mois.

---

## Annexe — verbatim réglementaire à constituer

Ce document cite le droit de seconde main : résumés de presse professionnelle et de sites
spécialisés, parce que Légifrance et le site de l'Ordre étaient bloqués depuis cet environnement.
C'est acceptable pour un brainstorming, **pas pour une décision d'investissement**.

Or ce dépôt contient exactement l'outil qu'il faut. Une fois `PISTE_CLIENT_ID` / `PISTE_CLIENT_SECRET`
en environnement, `mcp-legifrance` permet de récupérer le verbatim consolidé de :

| Texte | Objet | Tool |
|---|---|---|
| R.5123-2 CSP | Quantité maximale par délivrance | `get_article` / `get_section` |
| R.5132-21, R.5132-22 CSP | Durée maximale de prescription, délai de présentation | `get_section` |
| R.5125-45 à R.5125-52 CSP | Livraison et dispensation à domicile | `get_section` |
| R.4235-22 CSP + sous-section information et publicité | Sollicitation de clientèle, communication | `get_section` |
| Décret n° 2024-1070 du 26/11/2024 | Dispensation supplémentaire exceptionnelle | `get_jorf` puis `consult_loda` |

Attention au piège documenté dans le README : `/consult/lawDecree` exige un LEGITEXT, pas un
JORFTEXT — passer par `search_legifrance` ou `get_jorf` pour récupérer le LEGITEXT du décret.

Les numéros d'articles ci-dessus sont donnés de mémoire et par recoupement de sources secondaires :
**ils font partie de ce qui est à confirmer au verbatim**, pas de ce qui est établi.

---

## Sources

Réglementaire et professionnel :

- [Décret n° 2024-1070 du 26 novembre 2024 — dispensation supplémentaire exceptionnelle (Légifrance)](https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000050668009)
- [Renouvellement des traitements chroniques pour 3 mois (USPO)](https://uspo.fr/renouvellement-des-traitements-chroniques-pour-3-mois-la-mesure-enfin-applicable/)
- [Délivrance après expiration de l'ordonnance : de 1 à 3 mois (Vidal)](https://www.vidal.fr/actualites/31079-delivrance-des-medicaments-apres-expiration-de-l-ordonnance-la-duree-passe-de-1-a-3-mois.html)
- [CSP — Délivrance, livraison, dispensation à domicile, R.5125-45 à R.5125-52 (Légifrance)](https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006072665/LEGISCTA000006190692/2020-04-23)
- [Dispensation et livraison à domicile — fiche professionnelle (CNOP)](https://www.ordre.pharmacien.fr/je-suis/pharmacien/pharmacien/mon-exercice-professionnel/les-fiches-professionnelles/dispensation-et-livraison-a-domicile-de-medicaments-produits-ou-objets-mentionnes-a-l-article-l4211-1-du-code-de-la-sante-publique)
- [L'Ordre s'en prend aux offres de livraison (Le Moniteur des pharmacies)](https://www.lemoniteurdespharmacies.fr/legislation/dispensation/medicaments-a-domicile-lordre-des-pharmaciens-sen-prend-aux-offres-de-livraison)
- [CSP — Interdictions de certains procédés de recherche de clientèle, R.4235-21 à R.4235-30 (Légifrance)](https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006072665/LEGISCTA000006196447/)
- [CSP — Information et publicité, R.4235-38 à R.4235-53 (Légifrance)](https://www.legifrance.gouv.fr/codes/id/LEGISCTA000053624084/2026-03-06)
- [144 — Sollicitation de clientèle, jurisprudence ordinale (CNOP)](https://www.ordre.pharmacien.fr/jurisprudence/144-sollicitation-de-clientele)
- [Nouvelles règles de communication et de publicité des pharmaciens (J. Dubois, avocat)](https://www.jdubois-avocat.fr/pharmaciens)
- [L'activité de vente en ligne de médicaments à usage humain (CNOP)](https://www.ordre.pharmacien.fr/je-suis/pharmacien/pharmacien/mon-exercice-professionnel/les-fiches-professionnelles/l-activite-de-vente-en-ligne-de-medicaments-a-usage-humain)
- [Médicaments et dispositifs médicaux vendus sur internet (DGCCRF)](https://www.economie.gouv.fr/dgccrf/les-fiches-pratiques/medicaments-et-dispositifs-medicaux-vendus-sur-internet)
- [Click & collect en officine : bonnes pratiques (Le Quotidien du Pharmacien)](https://www.lequotidiendupharmacien.fr/gestion-de-lofficine/e-sante/tout-sur-les-bonnes-pratiques-du-click-collect)
- [Ordonnance numérique — doctrine du numérique en santé (ANS)](https://esante.gouv.fr/doctrine/ordonnance-numerique)
- [Prescription électronique : où en est l'ordonnance numérique ? (CNOP)](https://www.ordre.pharmacien.fr/les-communications/focus-sur/les-actualites/prescription-electronique-ou-en-est-l-ordonnance-numerique)
- [Le Ségur du numérique en santé pour l'officine (ANS)](https://esante.gouv.fr/segur/officine)

LGO Pharmony :

- [PHARMONY ONE — gestion d'officine (Pharmony France)](https://pharmony.fr/pharmony-one-gestion-officine/)
- [Le LGO cloud PHARMONY obtient le référencement Ségur (Pharmony France)](https://pharmony.fr/1er-lgo-en-mode-cloud-pharmony-obtient-le-referencement-segur/)
- [Logiciels référencés « Ségur » : mise à jour (CNOP)](https://www.ordre.pharmacien.fr/les-communications/focus-sur/les-actualites/logiciels-references-segur-mise-a-jour-d-ici-septembre)

Modèle du rendez-vous mensuel :

- [Impact of Appointment-Based Medication Synchronization on Proportion of Days Covered (PMC)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6025216/)
- [The impact of appointment-based medication synchronization — systematic review (J Clin Pharm Ther)](https://onlinelibrary.wiley.com/doi/10.1111/jcpt.12554)
- [Implementation of the appointment-based model in community pharmacies (PubMed)](https://pubmed.ncbi.nlm.nih.gov/37286385/)
- [Pharmacy Medication Synchronization Service Works to Improve Medication Adherence (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6124979/)
- [Cost-Benefit of Appointment-Based Medication Synchronization (AJMC)](https://www.ajmc.com/view/cost-benefit-of-appointment-based-medication-synchronization-in-community-pharmacies)

Hébergement et conformité :

- [Certification HDS — hébergement de données de santé (OVHcloud)](https://www.ovhcloud.com/en/compliance/hds/)
- [Produits OVHcloud couverts par la certification HDS (documentation OVHcloud)](https://docs.ovhcloud.com/en/guides/account-and-service-management/account-information/hds-certification)
- [Certification HDS — hébergeurs de données de santé (AFNOR)](https://certification.afnor.org/en/digital/hds-certification)
- [Obligations HDS pour les éditeurs SaaS de santé (SDV)](https://www.sdv.fr/actualites/donnees-de-sante-tout-ce-quil-faut-savoir-sur-les-obligations-hds/)
- [RGPD et logiciels de santé en 2026 — guide éditeurs (Vidal France)](https://editeurs.vidalfrance.com/ressources/articles/rgpd-et-logiciels-de-sante-en-2026-guide-de-conformite-pour-les-editeurs-de-sante-nouvelles-obligations-et-bonnes-pratiques)
