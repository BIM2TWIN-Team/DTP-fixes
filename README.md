# BIM2TWIN DTP hotfixes

This repo fixes issues in BIM2TWIN DTP originated from Orange IFC injector. The python script fixed the following:

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

The code was extracted from the internal code of WP3 and relies heavily
on [DTP_API](https://github.com/BIM2TWIN-Team/DTP_API).

## How to run the script

> [!CAUTION]
> This script modifies multiple nodes in the graph.

Clone the repo with

```shell
git clone --recurse-submodules git@github.com:BIM2TWIN-Team/DTP-fixes.git
```

Set your `DEV_TOKEN`, `DTP_DOMAIN` and `LOG_DIR` in `DTP_API/DTP_config.xml`

You can run the script with the below command:

```shell
python3 fix_graph.py --target_level element --node_type asbuilt 
```

Please use simulation node with flag `--simulation` or `-s` if you are unsure how the script will perform in your DTP
domain and check the log files. `target_level` indicates the node level to be fixed, and it can
be `element`, `task`, `activity` or `all`.  `node_type` indicate the target node type to be fixed, and it can
be `asbuilt`, `asdesigned` or `all`. By default, above command runs all fixes on as-built nodes at element level. If you
want to run one specific fix (currently only support at element level), please set `fixes`. `fixes`
includes `asdesigned` - add asDesigned param, `type` - remove type as node param and add as link, `iri` - fix node iri
and `all`. The below command fixes iri of all as-built element nodes.

```shell
python3 fix_graph.py --target_level element --node_type asbuilt --fixes iri
```

Session file generated at `LOG_DIR/sessions` can be used to revert node updates with

```shell
python3 fix_graph.py --revert LOG_DIR/sessions/db_session-dd-tt.log
```

or revert multiple session at `LOG_DIR/sessions` by 

```shell
python3 fix_graph.py --revert LOG_DIR/sessions
```
