# Protocole de comparaison

`benchmarks/scenarios.json` fige 15 briefs couvrant six pages Web, quatre apps iOS, quatre scénarios motion et une retouche. Cinq autres cas, dont deux négatifs, restent réservés à la validation. `benchmarks/prepare_trials.py` randomise l’ordre et enlève les étiquettes des variantes de la feuille de revue.

Les variantes sont A agent seul, B Cosmos 2.4.1, C Cosmos 2.5.0, D concurrent adapté au scénario. Le document d’architecture fourni utilise un autre ordre. Toujours stocker le nom de la variante avec sa lettre. Fixer le modèle, le budget et les références autorisées avant les essais. Ouvrir une session indépendante pour chaque essai et distribuer les mêmes ressources initiales. Ne pas substituer l’initialisation d’un outil à l’évaluation de ses productions.

La grille /100 du cahier texte utilise 15 direction, 15 identité, 10 composition, 10 typographie, 15 interactions ou motion, 10 UX, 10 technique, 10 responsive et accessibilité, 5 finition. Pour un cas sans motion, établir les critères d’interaction avant le test. Exiger un examen des captures et des contrôles fonctionnels. Enregistrer temps, appels, corrections, erreurs, coût et tokens quand le client les fournit. Les mesures indisponibles restent nulles. Les scénarios de reproduction utilisent uniquement des visuels autorisés à cette fin.

Portes annoncées avant comparaison commerciale : gain d’au moins 15 points contre A, score moyen d’au moins 85, au moins 80 % de préférences valides contre A, absence de défaut critique et vérification technique. L’activation et le gain contre B se mesurent séparément. Une enquête utilisateurs doit encore valider le besoin, la répétition d’usage et la volonté de payer.
