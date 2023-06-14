# BIM2TWIN DTP fixes

This repo fixes issues in BIM2TWIN DTP originated from Orange IFC injector. The python script will add `asDesigned` and
replace `ifc:Class` with `https://www.bim2twin.eu/ontology/Core#hasElementType` in as-planned element nodes.

The code was extracted from the internal code of WP3.

> **Warning**
> This script modified multiple nodes in the graph.

Clone the repo with 

```shell
git clone --recurse-submodules git@github.com:BIM2TWIN-Team/DTP-fixes.git
```

Set your `DEV_TOKEN` and `DTP_DOMAIN` in `DTP_API/DTP_config.xml`

You can run the script with the below command:

```shell
python3 fix_graph.py --log_dir path/to/session-log/dir
```

Please use simulation node with flag `--simulation` or `-s` if you are unsure how the script will perform in your DTP
domain and check the log files.