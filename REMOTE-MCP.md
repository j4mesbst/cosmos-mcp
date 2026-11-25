# Cosmos 2.4.1 et le transport MCP distant

Le moteur Python et les ressources du plugin sont conservés. Le Worker sert de passerelle Streamable HTTP sur /mcp. Il transmet les demandes au même moteur Python via remote/bridge.py, qui maintient un processus et un état distincts par session. Les vérifications du projet, la génération des fichiers et Chromium s’exécutent sur la machine qui héberge ce moteur.

## Configuration

Le moteur se lie à 127.0.0.1:8765. Faire pointer une origine HTTPS contrôlée vers ce port. Le Worker doit recevoir COSMOS_UPSTREAM avec l’URL complète de l’origine MCP, ainsi que deux secrets différents COSMOS_CLIENT_TOKEN et COSMOS_ORIGIN_TOKEN. Configurer ces secrets via Wrangler et les transmettre à la machine d’origine par son environnement. Exécuter python3 remote/bridge.py sur l’origine. Pour auditer un projet, fixer COSMOS_PROJECT_ROOT à un répertoire de projet dédié et installé. Les traces d’audit peuvent lire les fichiers de ce répertoire. Réserver cet accès aux utilisateurs autorisés. Le moteur doit rester en ligne.

Le Worker refuse les appels sans jeton. Pour un client qui exige une URL seule et un flux d’autorisation standard, ajouter un fournisseur OAuth avant de publier le connecteur. Ne pas mettre de jeton dans une URL ou dans un fichier suivi. Le connecteur Claude n’a pas été testé avec cette passerelle.

Aucun ZIP monolithique ni ressource privée n’est servi comme asset Cloudflare. Les ressources utiles restent dans le dépôt. Connecter le dépôt GitHub et faire un push sans forcer après inspection de sa branche existante. Pour déployer, s’authentifier avec Wrangler dans le compte autorisé, vérifier l’offre Workers Free et configurer une origine fonctionnelle avant de publier.
