# Comparaison des outils

| Outil | Vérification effectuée | Force observée ou documentée | Choix pour Cosmos |
|---|---|---|---|
| shadcn MCP | Paquet 4.23.0, initialisation et 7 outils exposés | La registry décrit une intégration et ses dépendances | Garder l’adaptateur et préserver le thème du projet |
| Playwright MCP | Paquet 0.0.86, initialisation et 25 outils exposés | Arbre accessible pour piloter des états et captures | Associer un rendu à des assertions et à une décision |
| HeroUI | Projet 3.2.8 local compilé et rejoué. MCP officiel étudié | Composants réels et styles par version | Tester les imports et les contrôles rendus |
| Figma MCP | Documentation officielle | Contexte de layout, composants et variables | Annoter les régions et indiquer quand les mesures sont estimées |
| 21st | Documentation officielle | Recherche de pièces installables et contexte d’intégration | Décrire les composants par rôle et dépendances |
| Mobbin | Documentation officielle, accès MCP payé non utilisé | Corpus d’écrans et de parcours réels | Privilégier les captures qui expliquent un produit ou un geste |
| Magic UI | Documentation officielle | Registry et composants d’animation React | Préférer des primitives vérifiables et ne rien installer par défaut |

Aucune génération esthétique concurrente contrôlée n’a été exécutée. Les résultats de deux serveurs MCP sont dans `benchmarks/results/mcp-comparison.json`. Aucun compte tiers ni accès payant utilisé. Les chiffres publics de taille de catalogue sont des chiffres déclarés par les éditeurs.

Pour la motion, ScrollTrigger décrit les plages et la synchronisation au scroll. Motion expose une stratégie reduced motion. Lottie lit des animations exportées. Les APIs Three.js couvrent la scène et le rendu 3D. Les HIG Apple privilégient les transitions motivées et une alternative à la motion. Le premier exemple Cosmos utilise WAAPI, sans dépendance supplémentaire, pour une séquence DOM mesurable. Rive, WebGL et les transitions iOS restent à qualifier en exécution.

Sources : [21st](https://21st.dev/mcp), [Figma](https://developers.figma.com/docs/figma-mcp-server/), [shadcn](https://ui.shadcn.com/docs/mcp), [Playwright](https://github.com/microsoft/playwright-mcp), [HeroUI](https://heroui.com/en/docs/react/getting-started/mcp-server), [Mobbin](https://mobbin.com/mcp), [Magic UI](https://magicui.design/docs/mcp), [Motion](https://motion.dev/docs/react-accessibility), [GSAP](https://gsap.com/docs/v3/Plugins/ScrollTrigger/), [Lottie](https://github.com/airbnb/lottie/blob/master/web.md), [Three.js](https://threejs.org/docs/), [Apple](https://developer.apple.com/design/human-interface-guidelines/motion), [OpenAI](https://developers.openai.com/plugins/guides/optimize-metadata).
