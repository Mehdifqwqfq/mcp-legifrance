# Renouvellements — organisation des renouvellements patients

Chantier Etik Pharma : anticiper et **préparer à l'avance** les renouvellements de traitements
chroniques. L'intuition de départ était « un abonnement Amazon pour les médocs » ; ce qu'on en garde,
c'est le moteur de prédiction du réapprovisionnement — pas la logistique, fermée en France pour les
médicaments d'ordonnance.

**Statut** : brainstorming. Aucun code, aucune décision arrêtée.

## Contenu

| Fichier | Objet |
|---|---|
| [`BRAINSTORM.md`](BRAINSTORM.md) | Le document fondateur : cadre légal, modèle produit, fonctionnalités, ergonomie, architecture, conformité, trajectoire |

## En deux lignes

Le produit n'est pas un abonnement mais un **plan de renouvellement** : l'officine sait à la semaine
près quand chaque patient chronique va tomber en panne, prépare le bac à l'avance, synchronise les
lignes sur un rendez-vous mensuel unique, et sécurise le stock en amont.

## Prochaine étape

La **P0**, en lecture seule et sans patient : 12 mois d'historique de délivrances, un parseur de
posologie, et un seul tableau — date de fin prédite vs date de retour réelle. Go/no-go sur une erreur
médiane ≤ 3 jours. Détail au §7 du brainstorming.

## Pourquoi dans ce dépôt

Le cadre réglementaire est ici la contrainte de conception principale, et `mcp-legifrance` est
l'outil qui permet d'en récupérer le verbatim consolidé (CSP, JORF, LODA). L'annexe du brainstorming
liste les textes à sourcer et les tools correspondants.
