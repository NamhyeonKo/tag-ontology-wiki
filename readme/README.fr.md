# TOW — Tag Ontology for Wiki

Un plugin de compétences pour agents qui relie un coffre Obsidian à un projet de développement : recherche par concept dans les deux, étiquette les documents du projet au moyen des métadonnées `.tow/` et envoie le contenu sélectionné dans le coffre sous forme de nouvelle note. Il ne modifie pas les documents du projet et préserve le contenu lors de la maintenance du coffre. Il fonctionne dans Claude Code, Codex et Google Antigravity.

[English](../README.md) · [한국어](README.ko.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [Español](README.es.md) · [Français](README.fr.md)

> **Version :** 0.5.1.

## Présentation

La maintenance courante préserve le texte, le contenu des formules et du code, ainsi que les valeurs des tableaux ; seuls les éléments de frontmatter et de mise en forme sélectionnés changent. La curation ultérieure facultative suit vos propres modèles et les opérations que vous choisissez explicitement. TOW fonctionne avec les structures de coffre existantes, y compris les notes sans frontmatter. Sa méthode facultative de LLM Wiki centrée sur les tags comporte trois couches sélectionnables indépendamment :

- **Dossiers PARA** : Projects, Areas, Resources, Archives.
- **Champs de classification** dans le frontmatter : `category`, `type`, `status`, `kind`.
- **Une ontologie de tags conceptuels** : un dictionnaire de tags avec des alias et des relations entre concepts plus généraux et plus spécifiques.

Choisissez PARA lors de la configuration ou conservez vos propres dossiers. La recherche courante et le travail sur le corps des notes ne nécessitent ni dictionnaires ni nettoyage des métadonnées. Les requêtes utilisent d'abord Obsidian CLI, puis une recherche de fichiers à périmètre limité si nécessaire, avant de vérifier le contenu ; les propriétés disponibles améliorent la précision. Les conventions complètes figurent dans [docs/methodology.md](../docs/methodology.md).

TOW installe douze workflows dans l'environnement local de votre agent. Les workflows réservés au coffre gèrent les notes Obsidian ; depuis un projet, `tow-query` recherche à la fois dans le coffre connecté et dans le projet actuel, et `tow-send-vault` crée une nouvelle note dans le coffre avec le contenu sélectionné après votre approbation. Les tags et empreintes du projet sont stockés dans les métadonnées `.tow/` du projet ; les documents du projet ne sont pas modifiés.

Le paquet contient des compétences, des conventions partagées et l'utilitaire Python [`scripts/tow.py`](../scripts/tow.py). Cet utilitaire vérifie les règles de classification et appelle la CLI npm [`tag-ontology`](https://github.com/NamhyeonKo/obsidian-tag-ontology) pour analyser les notes, interroger les tags et valider ou modifier le dictionnaire. L'environnement de votre agent fournit le modèle et les outils de gestion de fichiers.

TOW utilise la CLI Tag Ontology pour interroger les tags et valider ou gérer les dictionnaires. Installez le [plugin Tag Ontology pour Obsidian](https://github.com/NamhyeonKo/obsidian-tag-ontology) ([page du plugin communautaire](https://community.obsidian.md/plugins/tag-ontology)) avec TOW pour explorer visuellement, dans un graphe, la hiérarchie des tags et les relations que vous gérez.

```text
tag-ontology@0.2.0        vérifications du dictionnaire, requêtes, modifications, analyse des notes
      ▲  npx tag-ontology … --json
tow (ce plugin)           vérifications des conventions du coffre, compétences
      ▲  Claude Code / Codex / Antigravity
votre coffre Obsidian
```

## Compétences

| Compétence | Quand l'utiliser | Changements |
| --- | --- | --- |
| `tow-setup` | Configurer un coffre, le connecter pour un projet ou enregistrer les métadonnées du projet | Inspecte d'abord les noms ; écrit uniquement les métadonnées `.tow/` approuvées ou la connexion personnelle |
| `tow-send-vault` | Envoyer le contenu sélectionné du projet vers le coffre connecté | Crée une nouvelle note après approbation ; préserve le corps sélectionné sauf transformation demandée |
| `tow-query` | Trouver des documents à partir de conditions en langage naturel, de propriétés personnalisées, de tags ou de texte | Lecture seule ; CLI en premier, recherche de fichiers à périmètre limité en repli ; correspondances vérifiées et candidats déduits présentés séparément |
| `tow-check` | Vérifier le frontmatter, Markdown, les formules, le code, les tableaux et les références | Produit d'abord un rapport ; les corrections de syntaxe sélectionnées préservent le texte, le contenu et les valeurs |
| `tow-tag-suggest` | Recommander des tags conceptuels pour les notes sélectionnées | Applique uniquement les ajouts ou suppressions que vous sélectionnez |
| `tow-tag-sync` | Enregistrer de nouveaux tags, résoudre les alias ou réconcilier le dictionnaire | Propose d'abord ; applique les modifications approuvées du dictionnaire et des tags |
| `tow-classify` | Enregistrer des catégories, reclasser des notes, convertir d'anciens champs | Soumet les entrées et conversions à approbation ; les modifications rétroactives font l'objet d'un choix distinct |
| `tow-link` | Lier les mentions existantes de titres ou d'alias | Uniquement les premières mentions approuvées ; préserve les mots affichés |
| `tow-edit` | Effectuer explicitement des retouches du corps selon votre modèle ou vos règles | Uniquement le contenu nouveau ou vide sélectionné, ou les transformations sélectionnées ; pose une question si les règles manquent |
| `tow-merge` | Consolider explicitement selon les destinations et règles choisies | Transfert à l'identique par défaut ; choix au cas par cas et confirmation distincte avant tout abandon de contenu |
| `tow-review` | Examiner les notes selon vos règles et proposer des retouches | Lecture seule tant qu'une opération de suivi concrète n'est pas sélectionnée |
| `tow-ingest` | Classer ou retravailler explicitement les sources selon les règles choisies | Classement à l'identique par défaut ; aucune métadonnée, dérivation ni réécriture implicite |

Les trois environnements partagent ces compétences, les conventions et la CLI. Dans Claude Code, invoquez `/tow:tow-query` ; dans Codex, sélectionnez `tow-query` avec `$` ou `/skills` ; dans Antigravity, invoquez `/tow-query`.

## Préservation et retouches facultatives

Les changements limités aux métadonnées utilisent des instantanés indépendants et `tow verify-body` pour vérifier les octets exacts du corps. La mise en forme comprend la syntaxe Markdown, les délimiteurs mathématiques, les délimiteurs de blocs de code, la mise en forme adaptée au langage et les tableaux, mais ne modifie jamais leur contenu. Les corrections ambiguës ou invérifiables restent de simples rapports. Il s'agit d'instructions pour les compétences, complétées par une comparaison limitée des octets, et non d'un vérificateur sémantique universel ou d'un mécanisme de sécurité imposé par l'environnement.

`tow-edit`, `tow-merge`, `tow-ingest` et `tow-review` conservent leurs noms et constituent des workflows facultatifs de curation ultérieure. Ils réutilisent les modèles et règles que vous avez fournis ou établis ; une demande générale de nettoyage ou un modèle seul n'autorise pas la réécriture de texte déjà rédigé, la génération d'une note centrale ni la division de notes. Voir [préservation](../docs/preservation.md) et [curation ultérieure](../docs/post-curation.md).

## Prérequis

- Claude Code, Codex ou Google Antigravity avec prise en charge des plugins
- Git, pour l'installation depuis GitHub
- Node.js 22.18 ou version ultérieure, avec npm/npx dans `PATH`, pour utiliser les fonctions facultatives d'analyse ou d'ontologie de `tag-ontology`
- Obsidian CLI est facultative ; la recherche native exige son activation et l'accès au coffre cible dans l'application en cours d'exécution. La recherche de fichiers reste disponible sans elle
- Python 3.10 ou version ultérieure (bibliothèque standard uniquement)

Les compétences lisent les fichiers du coffre compris dans le périmètre que vous définissez et n'appliquent que les changements que vous approuvez. L'environnement de votre agent traite le contenu des notes ouvertes selon ses propres paramètres de modèle et de confidentialité. TOW n'a pas de backend hébergé ; npm télécharge la CLI à la version fixée et l'environnement contrôle l'accès aux fichiers.

## Installer depuis GitHub

Installez directement depuis ce dépôt public. L'inscription dans l'annuaire officiel est facultative. Les commandes ci-dessous utilisent `main` ; après l'installation, démarrez une nouvelle session de votre environnement. Consultez le [guide d'installation et de dépannage](../docs/installation.md) pour la vérification, les paramètres du coffre et les mises à jour.

### Claude Code

```text
/plugin install tow --marketplace NamhyeonKo/tag-ontology-wiki
```

Sur les versions de Claude Code antérieures à 2.1.275 :

```text
/plugin marketplace add NamhyeonKo/tag-ontology-wiki
/plugin install tow@tag-ontology-wiki
```

### Codex

Exécutez dans votre terminal :

```bash
codex plugin marketplace add NamhyeonKo/tag-ontology-wiki --ref main
codex plugin add tow@tag-ontology-wiki
```

### Antigravity

Exécutez dans votre terminal, puis démarrez une nouvelle session Antigravity :

```bash
agy plugin install https://github.com/NamhyeonKo/tag-ontology-wiki
```

## Mettre à jour

Exécutez les commandes correspondant à votre environnement dans votre terminal, puis démarrez une nouvelle session.

**Claude Code :**

```bash
claude plugin update tow@tag-ontology-wiki
```

**Codex :**

```bash
codex plugin marketplace upgrade tag-ontology-wiki
codex plugin add tow@tag-ontology-wiki
```

**Antigravity :** réinstallez depuis la même source.

```bash
agy plugin install https://github.com/NamhyeonKo/tag-ontology-wiki
```

Confirmez la version installée avec la commande de liste ou de détails des plugins de votre environnement. Voir [mises à jour et dépannage](../docs/installation.md#update) pour le comportement et les vérifications propres à chaque environnement.

## Première utilisation

Pour la maintenance du coffre uniquement, ouvrez-le comme espace de travail de votre environnement. Pour utiliser TOW depuis un projet, ouvrez le projet et sélectionnez `tow-setup` afin de connecter le coffre et d'enregistrer les métadonnées `.tow/` du projet. Dans une nouvelle session du projet, sélectionnez `tow-query` et envoyez :

```text
Mon coffre se trouve dans /absolute/path/to/vault. Trouve les notes de projet sur RAG par catégorie
ou concept, en excluant les documents remplacés. Recherche à la fois dans ce projet et dans le
coffre connecté, lis les notes correspondantes avant de les résumer, et indique la source, les
chemins, les raisons des correspondances et le nombre de résultats. Ne modifie aucun fichier.
```

La recherche est possible sans enregistrer le projet ni disposer de dictionnaires ; l'étiquetage du projet nécessite des métadonnées `.tow/`. La connexion personnelle est enregistrée dans `$TOW_VAULT` ou `~/.tow/config.json`, jamais dans les fichiers du projet. Si le répertoire courant se trouve dans un coffre, celui-ci est prioritaire sur la connexion personnelle ; utilisez `--root` pour choisir explicitement. Depuis un coffre, les requêtes ne recherchent que dans ce coffre. Pour organiser le coffre, sélectionnez `tow-setup` ; il vous demandera si vous souhaitez PARA et préservera la structure et le schéma existants. La nouvelle configuration du coffre se trouve dans `.tow/config.json` ; les coffres 0.4.x avec un `tow.json` à la racine restent lisibles avant migration. Consultez le [guide de configuration](../docs/installation.md#configure-the-vault) et les [instructions de connexion d'un projet](../docs/installation.md#connect-a-vault-to-a-project).

## CLI et vérifications de configuration

L'utilitaire utilise `npx --yes tag-ontology@0.2.0` ; npm récupère cette version exacte lorsque c'est nécessaire. Les commandes manuelles de l'utilitaire utilisent le chemin du fichier `scripts/tow.py` installé. Dans les conventions, le nom `tow` est une abréviation de ce chemin.

Ni TOW 0.5.1 ni `tag-ontology` 0.2.0 ne possèdent de commande `doctor`. Commencez par :

```bash
python3 --version
node --version
npx --yes tag-ontology@0.2.0 --version
```

Exécutez `lint` de TOW uniquement pour les métadonnées TOW adoptées ; les vérifications du dictionnaire s'appliquent uniquement aux fonctions d'ontologie initialisées. L'absence de métadonnées ou de dictionnaires facultatifs n'est pas un échec d'installation. Suivez ensuite les [vérifications de configuration](../docs/installation.md#check-the-setup) pour vérifier le plugin installé, la configuration, les dictionnaires et les tags des notes. `lint` couvre les champs de classification et le nombre de tags ; la compétence de vérification ajoute l'examen de la mise en forme et des références, note par note. Un résultat lint sans erreur ne couvre pas à lui seul toutes les vérifications des compétences.

## Documentation

- [Installation, paramètres du coffre et dépannage](../docs/installation.md)
- [Conventions du coffre et commandes de l'utilitaire](../docs/methodology.md)
- [Préservation du contenu](../docs/preservation.md) et [curation ultérieure facultative](../docs/post-curation.md)
- [Évaluation et limites de vérification](../docs/evaluation.md)

Les guides détaillés sont maintenus en anglais et partagés par toutes les éditions du README.

## Contribuer

Les rapports de bugs, corrections ciblées, améliorations de la documentation et corrections de traduction sont les bienvenus. Lisez [CONTRIBUTING.md](../CONTRIBUTING.md) pour la configuration de développement, les vérifications et la distinction entre les références des compétences et les traductions destinées aux lecteurs. Utilisez les [formulaires de signalement](https://github.com/NamhyeonKo/tag-ontology-wiki/issues/new/choose) pour signaler un bug ou suggérer une fonctionnalité.

## Soutien

TOW est gratuit et open source. S'il vous fait gagner du temps, vous pouvez [m'offrir un café](https://buymeacoffee.com/namhyunko).

## Licence

[MIT](../LICENSE)
