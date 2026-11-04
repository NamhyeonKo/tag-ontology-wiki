# TOW — Tag Ontology for Wiki

Un plugin de compétences pour agents qui permet de gérer des documents **dans votre coffre Obsidian** : rechercher des notes, gérer le frontmatter et corriger la mise en forme tout en préservant le contenu. Il fonctionne dans Claude Code, Codex et Google Antigravity, avec le coffre comme espace de travail.

[English](../README.md) · [한국어](README.ko.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [Español](README.es.md) · [Français](README.fr.md)

> **Version :** 0.4.1.

## Présentation

La maintenance courante préserve le texte, le contenu des formules et du code, ainsi que les valeurs des tableaux ; seuls les éléments de frontmatter et de mise en forme sélectionnés changent. La curation ultérieure facultative suit vos propres modèles et les opérations que vous choisissez explicitement. TOW fonctionne avec les structures de coffre existantes, y compris les notes sans frontmatter. Sa méthode facultative de LLM Wiki centrée sur les tags comporte trois couches sélectionnables indépendamment :

- **Dossiers PARA** : Projects, Areas, Resources, Archives.
- **Champs de classification** dans le frontmatter : `category`, `type`, `status`, `kind`.
- **Une ontologie de tags conceptuels** : un dictionnaire de tags avec des alias et des relations entre concepts plus généraux et plus spécifiques.

Choisissez PARA lors de la configuration ou conservez vos propres dossiers. La recherche courante et le travail sur le corps des notes ne nécessitent ni dictionnaires ni nettoyage des métadonnées. Les requêtes utilisent d'abord Obsidian CLI, puis une recherche de fichiers à périmètre limité si nécessaire, avant de vérifier le contenu ; les propriétés disponibles améliorent la précision. Les conventions complètes figurent dans [docs/methodology.md](../docs/methodology.md).

TOW installe onze workflows dans votre agent de programmation local. Vous indiquez le coffre et les notes ; l'agent lit les fichiers concernés, recherche les classifications et les tags conceptuels, puis propose des changements délimités à votre approbation. Les fichiers restent dans votre coffre Obsidian.

Le paquet contient des compétences, des conventions partagées et l'utilitaire Python [`scripts/tow.py`](../scripts/tow.py). Cet utilitaire vérifie les règles de classification et appelle la CLI npm [`tag-ontology`](https://github.com/NamhyeonKo/obsidian-tag-ontology) pour analyser les notes, interroger les tags et valider ou modifier le dictionnaire. L'environnement de votre agent fournit le modèle et les outils de gestion de fichiers.

TOW utilise la CLI Tag Ontology pour interroger les tags et valider ou gérer les dictionnaires. Installez le [plugin Tag Ontology pour Obsidian](https://github.com/NamhyeonKo/obsidian-tag-ontology) ([page du plugin communautaire](https://community.obsidian.md/plugins/tag-ontology)) avec TOW pour explorer visuellement, dans un graphe, la hiérarchie des tags et les relations que vous gérez.

```text
tag-ontology@0.1.3        vérifications du dictionnaire, requêtes, modifications, analyse des notes
      ▲  npx tag-ontology … --json
tow (ce plugin)           vérifications des conventions du coffre, compétences
      ▲  Claude Code / Codex / Antigravity
votre coffre Obsidian
```

## Compétences

| Compétence | Quand l'utiliser | Changements |
| --- | --- | --- |
| `tow-setup` | Choisir PARA ou une structure existante ; activer les dictionnaires si souhaité | Liste uniquement les dossiers de premier niveau ; crée les dossiers, dictionnaires et `tow.json` après approbation ; ne déplace jamais de notes |
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

Ouvrez le coffre comme espace de travail de votre environnement. Dans une nouvelle session, sélectionnez `tow-query` avec l'invocation propre à votre environnement indiquée ci-dessus, puis envoyez :

```text
Mon coffre se trouve dans /absolute/path/to/vault. Trouve les notes de projet sur RAG par catégorie
ou concept, en excluant les documents remplacés. Lis les notes correspondantes avant de
les résumer et renvoie leurs chemins et leur nombre. Ne modifie aucun fichier.
```

Vous pouvez effectuer une recherche immédiatement sans configuration. Pour une organisation facultative, sélectionnez `tow-setup` ; il vous demande si vous souhaitez PARA et préserve votre structure et votre schéma existants. TOW lit `tow.json` à la racine du coffre ; les paramètres omis utilisent les valeurs par défaut du [guide de configuration](../docs/installation.md#configure-the-vault). L'installation ne crée ni ne migre de coffre.

## CLI et vérifications de configuration

L'utilitaire utilise `npx --yes tag-ontology@0.1.3` ; npm récupère cette version exacte lorsque c'est nécessaire. Les commandes manuelles de l'utilitaire utilisent le chemin du fichier `scripts/tow.py` installé. Dans les conventions, le nom `tow` est une abréviation de ce chemin.

Ni TOW 0.4.1 ni `tag-ontology` 0.1.3 ne possèdent de commande `doctor`. Commencez par :

```bash
python3 --version
node --version
npx --yes tag-ontology@0.1.3 --version
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
