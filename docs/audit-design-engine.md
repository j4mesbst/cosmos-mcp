# Audit de Cosmos 2.4.1

Baseline reproductible `d8336e0`. Le worktree de départ contient deux changements utilisateur sur le Worker et sa documentation. La branche de refonte est isolée et les laisse en place. Aucun déploiement ni secret modifié.

| Gravité | Constat | Preuve de départ | Risque et correction |
|---|---|---|---|
| Élevée | Une référence toute hauteur est traitée comme un écran quelconque. | `patterns.py` indexe deux catalogues, renvoie cinq lignes et aucun repère de section. `open_design_render` compare uniquement des ratios équivalents. | Préserver les IDs existants. Ajouter un corpus de pages, des sections et des comparaisons ciblées. |
| Élevée | Une décision de référence générique suffit souvent à approuver une landing. | `choose_design_direction` n’exige ni couverture des usages du produit ni liaison à un extrait de page. | Restreindre la nouvelle condition aux créations web qui sélectionnent les pages ajoutées. |
| Élevée | Les audits Web et les vérifications d’assets dépendent du projet local. | `design_assets.project_file` exige `COSMOS_PROJECT_ROOT`. Le gateway délègue au moteur. | Préserver le modèle de confiance. Les clients distants restent à qualifier. |
| Moyenne | Le choix de HeroUI par défaut peut contredire un projet existant. | `plan_design` choisit HeroUI pour le web et `verify_heroui_source` exige la version exacte 3.2.8. | Détecter les déclarations existantes et refuser de prétendre avoir installé une version inconnue. |
| Moyenne | Les guides ne prouvent ni l’activation ni leur effet. | Le serveur conserve les empreintes des guides lus et vérifie les extraits soumis. | Distinguer consultation, vérification d’implémentation et qualité comparative. |
| Élevée | Aucun résultat qui prouve la qualité iOS native ou motion à lui seul. | Il existe un profil chat, un audit Chromium et un mode motion textuel. Linux ne fournit pas Xcode. | Conserver le profil chat, ajouter un exemple motion vérifiable et inscrire les limites natives. |
| Élevée | Le dépôt contient une bibliothèque tierce sans autorisation générale établie. | Le catalogue et les captures portent la provenance. | Gérer les nouvelles captures en lot privé. Autorisation de republication à établir. |

`python3 -B skills/get-started/tests/test_references.py` a réussi avant la refonte. La découverte unittest a échoué car les fichiers historiques sont des scripts à lancer avec leurs arguments. Les notes visuelles /100, le coût, le rappel d’activation par client et les performances iOS natives restent non mesurés à la baseline. La présence d’un outil ne justifie aucun score.
