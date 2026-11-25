# Critique visuelle

Relais est une fixture de documentation fictive écrite pour montrer une transposition de Mintlify. L’aperçu d’éditeur est construit pour Relais avec ses propres textes et données. Le hero associe une promesse courte à un aperçu centré sur la publication. La grille montre trois fonctions distinctes. La clôture donne accès à un éditeur testable sur place.

La première inspection a montré des retours de ligne irréguliers du titre et une flèche convertie en emoji dans Chromium. Le titre emploie désormais un retour naturel équilibré et la flèche est typographique. L’inspection a été relancée à 1440, 768 et 390 px, avec un changement de titre vérifié, un premier focus clavier et l’activation du CTA. Aucun débordement ni erreur console sur cette fixture. L’aperçu est volontairement simplifié. Il ne publie aucune documentation.

- Avant après correction : `benchmarks/results/relay/avant-correction.png` et `benchmarks/results/relay/relay-contact.png`.
- Solo desktop, tablette et mobile : `benchmarks/results/relay/relay-{1440,768,390}.png`.
- Motion : `motion-timeline.mp4` visualise une timeline échantillonnée. Les offsets effectivement observés par le navigateur sont 0, 1000 et 2000 ms, à 0,5×. La séquence rend aussi son état final en mouvement réduit. La vidéo n’établit ni un FPS mesuré ni une continuité de boucle.
- Grok : `benchmarks/results/grok/active.png` et rapport Chromium. Le scénario est un prototype Web de chat iOS. Aucun binaire iOS n’a été construit.
- HeroUI : trace du projet Trait d’Union, dépendances React et styles 3.2.8, imports et contrôles rendus plus trois logos theSVG aux empreintes vérifiées. Les captures du replay testent le même projet et les deux versions du moteur.

Les images Relais sont un avant/après de correction sur une seule implémentation. Les artefacts du replay HeroUI prouvent une non-régression de ce projet. Les deux séries sont indépendantes de l’évaluation à l’aveugle d’un LLM.
