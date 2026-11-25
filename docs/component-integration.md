# Intégrer les composants

Commencer par le résultat `designContract.target.projectUI` de `plan_design`. Il liste les dépendances déclarées, le gestionnaire, les lockfiles et l’éventuelle version HeroUI installée. N’ajouter des dépendances qu’après lecture du projet.

- HeroUI React 3.2.8. `get_design_assets` fournit le mapping Button, Link, Modal, Switch et Card. Enregistrer le package.json, les composants importés et la feuille Tailwind avant les styles HeroUI. Le vérificateur contrôle l’AST, la version installée et les contrôles visibles.
- shadcn. Conserver le chemin et le thème du projet. Le Button fourni correspond à la registry existante. Vérifier les dépendances et l’état de focus.
- theSVG. Les marques déclarées sont renvoyées avec provenance et empreinte. La présence dans la collection ne confère pas de droits sur les marques.
- SwiftUI. Préférer les primitives natives, NavigationStack, Button, Dynamic Type et Reduce Motion. Le rendu Chromium ne vérifie pas SwiftUI.

Les pages de référence montrent des compositions, pas des composants installables. Les intégrer comme visuels produit nécessite des droits indépendants.
