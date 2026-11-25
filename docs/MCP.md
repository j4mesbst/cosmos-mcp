# Outils MCP 2.5.0

| Outil | Rôle |
|---|---|
| plan_design | Démarre un contrat et propose des références |
| search_patterns | Recherche par plateforme, section, composant ou contexte, avec filtre et pagination |
| read_pattern | Renvoie des octets d’image, page entière ou extrait |
| open_reference_flow | Ouvre les états ordonnés des scénarios Grok Bot |
| read_design_skill | Renvoie le guide applicable et trace son empreinte |
| search_brand_logos | Recherche les marques dans le lot local |
| read_brand_logo | Ouvre un logo déclaré dans le workflow |
| choose_design_direction | Vérifie les références ouvertes et les applications proposées |
| get_design_assets | Renvoie les tokens et le mapping des composants retenus |
| record_design_implementation | Inscrit et contrôle les fichiers réellement produits |
| run_design_audit | Lance le navigateur sur le serveur local autorisé |
| open_design_render | Ouvre les captures et associe comparaisons et décisions |
| record_design_review | Vérifie la fraîcheur des preuves et conserve les vérifications en attente |
| get_design_workflow | Guide pour design, implémentation, audit ou motion avec un exemple Web |
| review_evidence | Convertit les observations mesurées en corrections ciblées |

Exemple de catalogue : `search_patterns` avec `query: "landing page", fullPageOnly: true, limit: 5`. Répéter avec `offset: nextOffset`. Appeler `read_pattern` avec `id: "landing-mintlify"`, puis avec chaque `sectionId` si la page est retenue. Associer chaque section à `productFeature` et `renderTarget` dans la décision. Avec la mémoire activée côté processus, `reuseProjectStyle` lit le style et `saveProjectStyle` peut l’enregistrer à la fin d’une revue complète.
