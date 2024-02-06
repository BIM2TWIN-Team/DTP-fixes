# -*- coding: utf-8 -*-`

# Copyright University of Cambridge 2023. All Rights Reserved.
# Author: Alwyn Mathew <am3156@cam.ac.uk>
# This file cannot be used without a written permission from the author(s).

import argparse
import os.path

from DTP_API_DTC.DTP_API import DTPApi
from DTP_API_DTC.DTP_config import DTPConfig
from hot_fixes_dtc.update_elements import UpdateElements


def parse_args():
    """
    Get parameters from user
    """
    parser = argparse.ArgumentParser(description='Fix DTP graph with DTC ontology')
    parser.add_argument('--simulation', '-s', default=False, action='store_true')
    parser.add_argument('--revert', '-r', type=str, help='path to session log file')
    parser.add_argument('--target_level', type=str, choices=['element', 'task', 'activity', 'all'],
                        help='node level to be updated')
    parser.add_argument('--node_type', type=str, choices=['asbuilt', 'asdesigned', 'all'],
                        help='type of nodes to be updated')
    parser.add_argument('--fixes', type=str, choices=['asdesigned', 'progress', 'all'],
                        help='type of fix needed', default='all')

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.simulation:
        print('Running in the simulator mode.')
    dtp_config = DTPConfig('DTP_API_DTC/DTP_config.xml')
    dtp_api = DTPApi(dtp_config, simulation_mode=args.simulation)

    if args.revert:
        print(f'Reverting session from {args.revert}')
        if os.path.isfile(args.revert):
            dtp_api.revert_last_session(args.revert)
        elif os.path.isdir(args.revert):
            dtp_api.revert_sessions(args.revert)
        else:
            raise Exception(f"{args.revert} should be path to either a file or directory!")
    else:

        assert args.target_level in ['element', 'task', 'activity', 'all'], "Target level not set!"
        assert args.node_type in ['asbuilt', 'asdesigned', 'all'], "Node type not set!"

        if args.target_level in ["element", "all"]:
            fixElements = UpdateElements(dtp_config, dtp_api)
            num_updates = fixElements.update_element_nodes(args.node_type, args.fixes)
            print(f"Updated {num_updates['as_planned']} as-designed and {num_updates['as_perf']} as-built "
                  f"element nodes")

        if args.target_level == "task":
            raise NotImplementedError("task level fixes not found!")

        if args.target_level == "activity":
            raise NotImplementedError("activity level fixes not found!")
