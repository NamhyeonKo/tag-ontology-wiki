<h1 align="center">TOW — Tag Ontology for Wiki</h1>

<p align="center">
  <a href="https://github.com/NamhyeonKo/tag-ontology-wiki/stargazers"><img alt="stars" src="https://img.shields.io/github/stars/NamhyeonKo/tag-ontology-wiki?label=stars"></a>
  <a href="https://github.com/NamhyeonKo/tag-ontology-wiki/releases/latest"><img alt="release" src="https://img.shields.io/github/v/release/NamhyeonKo/tag-ontology-wiki?label=release"></a>
  <a href="../LICENSE"><img alt="license" src="https://img.shields.io/github/license/NamhyeonKo/tag-ontology-wiki?label=license"></a>
</p>

<p align="center"><a href="../README.md">English</a> · <a href="README.ko.md">한국어</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.zh-TW.md">繁體中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.es.md">Español</a> · <a href="README.fr.md">Français</a></p>

Un plugin de habilidades para agentes que conecta una bóveda de Obsidian con un proyecto de programación: busca en ambos por concepto, etiqueta documentos del proyecto mediante metadatos `.tow/` y envía el contenido seleccionado a la bóveda como una nota nueva. No modifica los documentos del proyecto y conserva el contenido en el mantenimiento de la bóveda. Funciona en Claude Code, Codex y Google Antigravity.

> **Versión:** 0.5.8.

## Descripción general

El mantenimiento habitual conserva la prosa, el contenido de las fórmulas y del código, y los valores de las tablas; solo cambia el frontmatter y el formato seleccionados. La curación posterior opcional sigue tus propias plantillas y las operaciones que elijas explícitamente. TOW funciona con las estructuras de bóveda existentes, incluidas las notas sin frontmatter. Su propuesta opcional de LLM Wiki centrada en etiquetas tiene tres capas que se pueden elegir de forma independiente:

- **Carpetas PARA**: Projects, Areas, Resources, Archives.
- **Campos de clasificación** en el frontmatter: `category`, `type`, `status`, `kind`.
- **Una ontología de etiquetas conceptuales**: un diccionario de etiquetas con alias y relaciones entre conceptos más amplios y más específicos.

Elige PARA durante la configuración o conserva tus propias carpetas. Las búsquedas habituales y el trabajo sobre el cuerpo de las notas no requieren diccionarios ni limpieza de metadatos. Las consultas ejecutan una sola búsqueda con `tow search`, que combina conceptos del diccionario de etiquetas, títulos, encabezados, texto y propiedades mediante AND, OR y NOT; después solo abren las notas que describen en la respuesta. Las propiedades disponibles mejoran la precisión. Las convenciones completas están en [docs/methodology.md](../docs/methodology.md).

TOW instala doce flujos de trabajo en el entorno local de tu agente. Los flujos exclusivos de la bóveda gestionan notas de Obsidian; desde un proyecto, `tow-query` busca tanto en la bóveda conectada como en el proyecto actual, y `tow-send-vault` crea una nota nueva en la bóveda con el contenido seleccionado tras tu aprobación. Las etiquetas y los hashes del proyecto se guardan en los metadatos `.tow/` del proyecto; los documentos del proyecto no se modifican.

El paquete contiene habilidades, convenciones compartidas y el auxiliar de Python [`scripts/tow.py`](../scripts/tow.py). Este auxiliar comprueba las reglas de clasificación y llama a la CLI de npm [`tag-ontology`](https://github.com/NamhyeonKo/obsidian-tag-ontology) para analizar notas, consultar etiquetas y validar o modificar el diccionario. El entorno de tu agente proporciona el modelo y las herramientas de archivos.

TOW utiliza la CLI de Tag Ontology para consultar etiquetas y validar o gestionar diccionarios. Instala el [plugin Tag Ontology para Obsidian](https://github.com/NamhyeonKo/obsidian-tag-ontology) ([página del plugin de la comunidad](https://community.obsidian.md/plugins/tag-ontology)) junto con TOW para explorar visualmente, en un grafo, la jerarquía de etiquetas y las relaciones que gestionas.

```text
tag-ontology@0.3.1        comprobaciones del diccionario, consultas, ediciones, análisis de notas
      ▲  npx tag-ontology … --json
tow (este plugin)         comprobaciones de las convenciones de la bóveda, habilidades
      ▲  Claude Code / Codex / Antigravity
tu bóveda de Obsidian
```

## Habilidades

| Habilidad | Cuándo usarla | Cambios |
| --- | --- | --- |
| `tow-setup` | Configurar una bóveda, conectarla para usarla desde un proyecto o registrar metadatos del proyecto | Inspecciona primero los nombres; solo escribe metadatos `.tow/` aprobados o la conexión personal |
| `tow-send-vault` | Enviar contenido seleccionado del proyecto a la bóveda conectada | Crea una nota nueva tras la aprobación; conserva el cuerpo seleccionado salvo que se pida transformarlo |
| `tow-query` | Buscar documentos mediante condiciones en lenguaje natural, propiedades personalizadas, etiquetas o texto | Solo lectura; una consulta de `tow search` (AND, OR, NOT) sobre conceptos, títulos, texto y campos; muestra coincidencias y solo abre las notas que describe en la respuesta |
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

Para el mantenimiento exclusivo de la bóveda, ábrela como espacio de trabajo del entorno. Los archivos TOW de la bóveda están en `tow/`, visible; los metadatos de proyectos externos permanecen en `.tow/`. Para usar TOW desde un proyecto, abre el proyecto y selecciona `tow-setup` para conectar la bóveda y registrar los metadatos del proyecto. En una sesión nueva del proyecto, selecciona `tow-query` y envía:

```text
Mi bóveda está en /absolute/path/to/vault. Busca notas de proyectos sobre RAG por categoría
o concepto, excluyendo los documentos sustituidos. Busca tanto en este proyecto como en la
bóveda conectada, lee las notas coincidentes antes de resumirlas y devuelve origen, rutas,
motivos de coincidencia y cantidad. No modifiques archivos.
```

Puedes buscar sin registrar el proyecto ni tener diccionarios; para etiquetar el proyecto se necesitan metadatos `.tow/`. La conexión personal se guarda en `$TOW_VAULT` o `~/.tow/config.json`, nunca en los archivos del proyecto. Si el directorio actual está dentro de una bóveda, esa bóveda tiene prioridad sobre la conexión personal; usa `--root` para elegirla explícitamente. Las consultas desde una bóveda solo buscan en ella. Para organizar la bóveda, selecciona `tow-setup`; preguntará si quieres PARA y conservará la estructura y el esquema existentes. La nueva configuración de la bóveda se guarda en `tow/config.json`; las bóvedas antiguas `.tow/` y 0.4.x siguen siendo legibles hasta migrarlas a `tow/`. La migración lleva los documentos de reglas Markdown heredados a `tow/tags.md` / `tow/categories.md`; actualiza los enlaces a los archivos antiguos si los eliminas. Consulta la [guía de configuración](../docs/installation.md#configure-the-vault) y las [instrucciones de conexión del proyecto](../docs/installation.md#connect-a-vault-to-a-project).

## CLI y comprobaciones de configuración

El auxiliar utiliza `npx --yes tag-ontology@0.3.1`; npm obtiene esa versión exacta cuando hace falta. Los comandos manuales del auxiliar utilizan la ruta de `scripts/tow.py` instalado. El nombre `tow` en las convenciones es una abreviatura de esa ruta.

Ni TOW 0.5.8 ni `tag-ontology` 0.3.1 tienen un comando `doctor`. Empieza con:

```bash
python3 --version
node --version
npx --yes tag-ontology@0.3.1 --version
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
