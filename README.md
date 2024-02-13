# BIM2TWIN DTP hotfixes

This repo fixes issues in BIM2TWIN DTP originated from Orange IFC injector. The python script fixed the following:

**B2T ontology:**

* Element level fixes
    * Add `asDesigned` to nodes
    * Remove `ifc:Class` from nodes
    * Add `https://www.bim2twin.eu/ontology/Core#hasElementType` as links
    * Fix node IRI
* Task level fixes
    * Remove `https://www.bim2twin.eu/ontology/Core#hasTaskType` as node field
    * Add `https://www.bim2twin.eu/ontology/Core#hasTaskType` as links
* Activity level fixes
    * Remove `https://www.bim2twin.eu/ontology/Core#hasTaskType` as node field
    * Add `https://www.bim2twin.eu/ontology/Core#hasTaskType` as links

**DTC ontology:**

* Element level fixes
    * Fixed `asDesigned` IRI
    * Remove `https://dtc-ontology.cms.ed.tum.de/ontology#progress` from as-planned nodes

The code was extracted from the internal code of WP3 and relies heavily
on [DTP_API](https://github.com/BIM2TWIN-Team/DTP_API)
and [DTP_API_DTC](https://github.com/BIM2TWIN-Team/DTP_API-journal).

## How to run the script

> [!CAUTION]
> This script modifies multiple nodes in the graph.

Clone the repo with

```shell
git clone --recurse-submodules git@github.com:BIM2TWIN-Team/DTP-fixes.git
```

Set your `DEV_TOKEN`, `DTP_DOMAIN` and `LOG_DIR` in `DTP_API/DTP_config.xml`

### B2T ontology

You can run the script with the below command for **B2T ontology**:

```shell
python3 fix_graph.py --target_level element --node_type asbuilt 
```

| Flags        | Valid arguments              |
|--------------|------------------------------|
| target_level | element, task, activity, all |
| node_type    | asbuilt, asdesigned, all     |
| fixes        | asdesigned, type, iri, all   |

Please use simulation node with flag `--simulation` or `-s` if you are unsure how the script will perform in your DTP
domain and check the log files. `target_level` indicates the node level to be fixed, and it can
be `element`, `task`, `activity` or `all`.  `node_type` indicate the target node type to be fixed, and it can
be `asbuilt`, `asdesigned` or `all`. By default, above command runs all fixes on as-built nodes at element level. If you
want to run one specific fix (currently only support at element level), please set `fixes`. `fixes` for **B2T ontology**
includes `asdesigned` - add asDesigned param, `type` - remove type as node param and add as link, `iri` - fix node iri
and `all`. The below command fixes iri of all as-built element nodes.

```shell
python3 fix_graph.py --target_level element --node_type asbuilt --fixes iri
```

### DTC ontology

The below command fixes `asdesigned` iri of as-designed element nodes:

```shell
python3 fix_graph_dtc.py --target_level element --node_type asdesigned 
```

| Flags        | Valid arguments            |
|--------------|----------------------------|
| target_level | element                    |
| node_type    | asbuilt, asdesigned, all   |
| fixes        | asdesigned,  progress, all |

`fixes` for [DTC ontology](https://dtc-ontology.cms.ed.tum.de/ontology/index.html) includes `asdesigned` - fix asDesigned iri, `progress` - remove progress param from
as-designed nodes, and `all`.

## Revert changes

Session file generated at `LOG_DIR/sessions` can be used to revert node updates with

```shell
python3 fix_graph.py --revert LOG_DIR/sessions/db_session-dd-tt.log
```

or revert multiple session at `LOG_DIR/sessions` by

```shell
python3 fix_graph.py --revert LOG_DIR/sessions
```
