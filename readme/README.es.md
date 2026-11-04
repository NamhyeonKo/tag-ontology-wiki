# TOW — Tag Ontology for Wiki

Un plugin de habilidades para agentes que permite gestionar documentos **dentro de tu bóveda de Obsidian**: buscar notas, gestionar el frontmatter y corregir el formato conservando el contenido. Funciona en Claude Code, Codex y Google Antigravity con la bóveda como espacio de trabajo.

[English](../README.md) · [한국어](README.ko.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [Español](README.es.md) · [Français](README.fr.md)

> **Versión:** 0.4.1.

## Descripción general

El mantenimiento habitual conserva la prosa, el contenido de las fórmulas y del código, y los valores de las tablas; solo cambia el frontmatter y el formato seleccionados. La curación posterior opcional sigue tus propias plantillas y las operaciones que elijas explícitamente. TOW funciona con las estructuras de bóveda existentes, incluidas las notas sin frontmatter. Su propuesta opcional de LLM Wiki centrada en etiquetas tiene tres capas que se pueden elegir de forma independiente:

- **Carpetas PARA**: Projects, Areas, Resources, Archives.
- **Campos de clasificación** en el frontmatter: `category`, `type`, `status`, `kind`.
- **Una ontología de etiquetas conceptuales**: un diccionario de etiquetas con alias y relaciones entre conceptos más amplios y más específicos.

Elige PARA durante la configuración o conserva tus propias carpetas. Las búsquedas habituales y el trabajo sobre el cuerpo de las notas no requieren diccionarios ni limpieza de metadatos. Las consultas usan primero Obsidian CLI, después búsquedas en archivos con un alcance delimitado cuando hace falta y, por último, la verificación del contenido; las propiedades disponibles mejoran la precisión. Las convenciones completas están en [docs/methodology.md](../docs/methodology.md).

TOW instala once flujos de trabajo en tu agente de programación local. Indicas la bóveda y las notas; el agente lee los archivos pertinentes, busca clasificaciones y etiquetas conceptuales, y propone cambios de alcance delimitado para que los apruebes. Los archivos permanecen en tu bóveda de Obsidian.

El paquete contiene habilidades, convenciones compartidas y el auxiliar de Python [`scripts/tow.py`](../scripts/tow.py). Este auxiliar comprueba las reglas de clasificación y llama a la CLI de npm [`tag-ontology`](https://github.com/NamhyeonKo/obsidian-tag-ontology) para analizar notas, consultar etiquetas y validar o modificar el diccionario. El entorno de tu agente proporciona el modelo y las herramientas de archivos.

TOW utiliza la CLI de Tag Ontology para consultar etiquetas y validar o gestionar diccionarios. Instala el [plugin Tag Ontology para Obsidian](https://github.com/NamhyeonKo/obsidian-tag-ontology) ([página del plugin de la comunidad](https://community.obsidian.md/plugins/tag-ontology)) junto con TOW para explorar visualmente, en un grafo, la jerarquía de etiquetas y las relaciones que gestionas.

```text
tag-ontology@0.1.3        comprobaciones del diccionario, consultas, ediciones, análisis de notas
      ▲  npx tag-ontology … --json
tow (este plugin)         comprobaciones de las convenciones de la bóveda, habilidades
      ▲  Claude Code / Codex / Antigravity
tu bóveda de Obsidian
```

## Habilidades

| Habilidad | Cuándo usarla | Cambios |
| --- | --- | --- |
| `tow-setup` | Elegir PARA o una estructura existente; habilitar diccionarios opcionalmente | Solo enumera las carpetas de nivel superior; crea carpetas, diccionarios y `tow.json` tras la aprobación; nunca mueve notas |
| `tow-query` | Buscar documentos mediante condiciones en lenguaje natural, propiedades personalizadas, etiquetas o texto | Solo lectura; primero la CLI, después archivos con alcance delimitado como alternativa; coincidencias verificadas y candidatos inferidos por separado |
| `tow-check` | Comprobar frontmatter, Markdown, fórmulas, código, tablas y referencias | Primero informa; las correcciones de sintaxis seleccionadas conservan la prosa, el contenido y los valores |
| `tow-tag-suggest` | Recomendar etiquetas conceptuales para las notas seleccionadas | Aplica solo las adiciones o eliminaciones que selecciones |
| `tow-tag-sync` | Registrar nuevas etiquetas, resolver alias o conciliar el diccionario | Primero propone; aplica los cambios aprobados en el diccionario y las etiquetas |
| `tow-classify` | Registrar categorías, reclasificar notas, convertir campos heredados | Requiere aprobar las entradas y conversiones; los cambios retroactivos se eligen por separado |
| `tow-link` | Enlazar menciones existentes de títulos o alias | Solo las primeras menciones aprobadas; conserva las palabras mostradas |
| `tow-edit` | Realizar revisiones explícitas del cuerpo según tu plantilla o reglas | Solo contenido nuevo o vacío seleccionado, o transformaciones seleccionadas; pregunta si faltan reglas |
| `tow-merge` | Consolidar explícitamente según los destinos y las reglas elegidos | Transferencia literal por defecto; decisiones por caso y confirmación separada para descartar |
| `tow-review` | Revisar notas según tus reglas y proponer revisiones posteriores | Solo lectura hasta que se seleccione una operación posterior concreta |
| `tow-ingest` | Archivar o revisar fuentes explícitamente según las reglas que elijas | Archivado literal por defecto; no presupone metadatos, derivación ni reescritura |

Los tres entornos comparten estas habilidades, las convenciones y la CLI. En Claude Code, invoca `/tow:tow-query`; en Codex, selecciona `tow-query` con `$` o `/skills`; en Antigravity, invoca `/tow-query`.

## Conservación y revisión posterior opcional

Los cambios que afectan solo a los metadatos utilizan instantáneas independientes y `tow verify-body` para comprobar los bytes exactos del cuerpo. El formato incluye la sintaxis de Markdown, los delimitadores matemáticos, las delimitaciones de bloques de código, el formato específico de cada lenguaje y las tablas, pero nunca cambia su contenido. Las correcciones ambiguas o que no se pueden verificar se mantienen como informes. Se trata de instrucciones para las habilidades más una comparación limitada de bytes, no de un verificador semántico universal ni de un mecanismo de seguridad impuesto por el entorno.

`tow-edit`, `tow-merge`, `tow-ingest` y `tow-review` conservan sus nombres y son flujos opcionales de curación posterior. Reutilizan las plantillas y reglas que hayas proporcionado o establecido; una solicitud general de limpieza o una plantilla por sí sola no autoriza reescribir prosa ya existente, generar una nota central ni dividir notas. Consulta [conservación](../docs/preservation.md) y [curación posterior](../docs/post-curation.md).

## Requisitos

- Claude Code, Codex o Google Antigravity con compatibilidad con plugins
- Git, para la instalación desde GitHub
- Node.js 22.18 o posterior, con npm/npx en `PATH`, al utilizar las funciones opcionales de análisis u ontología de `tag-ontology`
- Obsidian CLI es opcional; la búsqueda nativa requiere que esté habilitada y que la bóveda de destino sea accesible en la aplicación en ejecución. La búsqueda en archivos sigue disponible sin ella
- Python 3.10 o posterior (solo biblioteca estándar)

Las habilidades leen los archivos de la bóveda cuyo alcance delimites y aplican solo los cambios que apruebes. El entorno de tu agente procesa el contenido de las notas abiertas según sus propios ajustes de modelo y privacidad. TOW no tiene backend alojado; npm descarga la CLI con la versión fijada y el entorno controla el acceso a los archivos.

## Instalar desde GitHub

Instala directamente desde este repositorio público. El registro en el directorio oficial es opcional. Los comandos siguientes utilizan `main`; después de la instalación, inicia una nueva sesión del entorno. Consulta la [guía de instalación y resolución de problemas](../docs/installation.md) para la verificación, los ajustes de la bóveda y las actualizaciones.

### Claude Code

```text
/plugin install tow --marketplace NamhyeonKo/tag-ontology-wiki
```

En versiones de Claude Code anteriores a 2.1.275:

```text
/plugin marketplace add NamhyeonKo/tag-ontology-wiki
/plugin install tow@tag-ontology-wiki
```

### Codex

Ejecuta en tu terminal:

```bash
codex plugin marketplace add NamhyeonKo/tag-ontology-wiki --ref main
codex plugin add tow@tag-ontology-wiki
```

### Antigravity

Ejecuta en tu terminal y, después, inicia una nueva sesión de Antigravity:

```bash
agy plugin install https://github.com/NamhyeonKo/tag-ontology-wiki
```

## Actualizar

Ejecuta los comandos de tu entorno en la terminal y, después, inicia una nueva sesión.

**Claude Code:**

```bash
claude plugin update tow@tag-ontology-wiki
```

**Codex:**

```bash
codex plugin marketplace upgrade tag-ontology-wiki
codex plugin add tow@tag-ontology-wiki
```

**Antigravity:** vuelve a instalar desde la misma fuente.

```bash
agy plugin install https://github.com/NamhyeonKo/tag-ontology-wiki
```

Confirma la versión instalada con el comando de lista o detalles de plugins de tu entorno. Consulta [actualizaciones y resolución de problemas](../docs/installation.md#update) para conocer el comportamiento y las comprobaciones específicos de cada entorno.

## Primer uso

Abre la bóveda como espacio de trabajo de tu entorno. En una sesión nueva, selecciona `tow-query` mediante la invocación específica de tu entorno indicada arriba y envía:

```text
Mi bóveda está en /absolute/path/to/vault. Busca notas de proyectos sobre RAG por categoría
o concepto, excluyendo los documentos sustituidos. Lee las notas que coincidan antes de
resumirlas y devuelve sus rutas y su cantidad. No modifiques archivos.
```

Puedes buscar de inmediato sin configurar nada. Para organizar de forma opcional, selecciona `tow-setup`; te pregunta si quieres PARA y conserva tu estructura y esquema existentes. TOW lee `tow.json` en la raíz de la bóveda; los ajustes omitidos utilizan los valores predeterminados de la [guía de configuración](../docs/installation.md#configure-the-vault). La instalación no crea ni migra una bóveda.

## CLI y comprobaciones de configuración

El auxiliar utiliza `npx --yes tag-ontology@0.1.3`; npm obtiene esa versión exacta cuando hace falta. Los comandos manuales del auxiliar utilizan la ruta de `scripts/tow.py` instalado. El nombre `tow` en las convenciones es una abreviatura de esa ruta.

Ni TOW 0.4.1 ni `tag-ontology` 0.1.3 tienen un comando `doctor`. Empieza con:

```bash
python3 --version
node --version
npx --yes tag-ontology@0.1.3 --version
```

Ejecuta `lint` de TOW solo para los metadatos de TOW que hayas adoptado; las comprobaciones del diccionario se aplican solo a las funciones de ontología inicializadas. La ausencia de metadatos o diccionarios opcionales no es un fallo de instalación. Después sigue las [comprobaciones de configuración](../docs/installation.md#check-the-setup) para verificar el plugin instalado, la configuración, los diccionarios y las etiquetas de las notas. `lint` cubre los campos de clasificación y el recuento de etiquetas; la habilidad de comprobación añade la revisión del formato y las referencias nota por nota. Un resultado limpio de lint por sí solo no cubre todas las comprobaciones de las habilidades.

## Documentación

- [Instalación, ajustes de la bóveda y resolución de problemas](../docs/installation.md)
- [Convenciones de la bóveda y comandos del auxiliar](../docs/methodology.md)
- [Conservación del contenido](../docs/preservation.md) y [curación posterior opcional](../docs/post-curation.md)
- [Evaluación y límites de verificación](../docs/evaluation.md)

Las guías detalladas se mantienen en inglés y son compartidas por todas las ediciones del README.

## Contribuir

Son bienvenidos los informes de errores, las correcciones puntuales, las mejoras de documentación y las correcciones de traducción. Lee [CONTRIBUTING.md](../CONTRIBUTING.md) para conocer la configuración de desarrollo, las comprobaciones y la distinción entre las referencias de las habilidades y las traducciones para lectores. Utiliza los [formularios de incidencias](https://github.com/NamhyeonKo/tag-ontology-wiki/issues/new/choose) para informar de un error o sugerir una función.

## Apoyo

TOW es gratuito y de código abierto. Si te ahorra tiempo, puedes [invitarme a un café](https://buymeacoffee.com/namhyunko).

## Licencia

[MIT](../LICENSE)
