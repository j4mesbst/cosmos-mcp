# Recherche produit pour Cosmos 2.0.0

Sources consultées le 22 novembre 2026. Les pages éditeurs décrivent les fonctions annoncées. Les avis publics sont des retours individuels et les outils payants n'ont pas été évalués ici en instrumentant des comptes réels.

| Outil | Mécanisme observé | Décision pour Cosmos |
|---|---|---|
| [Mobbin MCP](https://mobbin.com/mcp) | Recherche de références dans des produits existants et transmission du contexte à un agent. | Conserver la provenance et les images, exposer des séquences d'interaction et permettre l'adaptation explicite entre iOS et le web. |
| [Refero MCP](https://refero.design/mcp), [référence des outils](https://github.com/referodesign/refero_skill/blob/master/skills/refero-design/references/mcp-tools.md) | Sépare recherche par style, écrans et parcours. La documentation expose des identifiants et des descriptions. | Ouvrir des écrans par ID, fournir un parcours ordonné, puis documenter le lien entre état observé et décision de produit. Le catalogue Cosmos actuel couvre Grok Bot. |
| [Figma MCP](https://developers.figma.com/docs/figma-mcp-server/tools-and-prompts/) | Fournit le contexte de design et des captures. Code Connect peut orienter l'agent vers les composants réellement installés. | Renvoyer des données structurées et les pixels. Inspecter la source du composant et son utilisation JSX. |
| [shadcn/ui MCP](https://ui.shadcn.com/docs/mcp) | Recherche, lecture et installation d'éléments de registre dans le projet. | Fournir le vrai Button de la source new-york-v4, avec provenance, code et dépendances. Vérifier l'import et l'usage ou réutiliser le composant shadcn du projet. |
| [Paper MCP](https://paper.design/docs/mcp) | La surface de travail s'appuie sur une représentation HTML/CSS modifiable par l'agent. | Donner des fichiers et des tokens concrets à l'agent, puis vérifier sur le résultat implémenté. |
| [Playwright](https://github.com/microsoft/playwright.dev/blob/main/mcp/tools/screenshots.mdx) | Captures du navigateur et vérifications d'interface. | Charger de vrais PNG pour la critique. Produire un rapport avec navigation clavier, contrôle axe, parcours testable et empreintes de captures. |
| [UI/UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | Génère des recommandations et des valeurs à l'aide de scripts et données locaux. | Exécuter sa CLI embarquée pour générer les couleurs du projet. Vérifier que le fichier produit est effectivement importé. |
| [OpenAI, évaluation des skills](https://developers.openai.com/blog/eval-skills) et [création des skills](https://developers.openai.com/plugins/build/skills) | Le titre et la description aident le modèle à décider quand lire un skill. Le serveur expose les actions contrôlées. | Utiliser un skill d'entrée, puis exiger des traces que le MCP peut observer pendant le parcours. Tester une invocation automatique depuis un vrai client séparément. |

## Retours publics

- Sur r/UXDesign, un utilisateur de Mobbin dit que l'outil l'aide à comprendre les parcours et insiste sur la possibilité d'adapter les composants. Un autre fait état de rendus génériques en l'absence de composants de design system. Cet échantillon ne mesure pas un effet moyen. [Discussion](https://www.reddit.com/r/UXDesign/comments/1vz1zpq/mobbin_screendesign_refero_how_to_get_the_best/)
- Les avis Refero sur Product Hunt apprécient les motifs issus de produits réels et la rapidité de recherche. Ils demandent aussi de meilleurs regroupements et des mises à jour plus fréquentes. [Avis](https://www.producthunt.com/products/refero/reviews)
- Dans un essai indépendant de Refero, l'auteur rapporte que la recherche a renvoyé des exemples de vrais produits. Il associe Refero à Impeccable pour la phase de correction et signale une session ultérieure avec erreur d'autorisation. [Essai](https://soymarketingultra.com/en/refero-review-design-claude-code-codex/)

## Conséquences et limites

Cosmos exige désormais des références ou un résultat de recherche vide justifié, la récupération des fichiers de design, la présence de ces fichiers dans le code du projet, les captures réelles et une revue. Les mises en œuvre shadcn doivent inclure une importation JSX d'un Button reconnu. Le contrôle de provenance exactement identique s'applique à la version embarquée. Un composant existant peut passer le contrôle de structure, ce qui ne certifie pas à lui seul son origine.

La preuve technique borne ce que le serveur peut réellement vérifier. Il établit l'exécution du générateur, les références rendues au client, la présence et certains usages des fichiers, les octets des captures et la cohérence du rapport browser. L'appréciation du rendu demeure une revue visuelle. Une application sans le plugin ou une réponse générée en dehors du parcours Cosmos reste sous le contrôle du client. Pour une comparaison visuelle fiable, il faut des sessions distinctes, le même modèle et des résultats cachés au moment de la notation.
