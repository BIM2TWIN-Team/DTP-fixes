# -*- coding: utf-8 -*-`

# Copyright University of Cambridge 2023. All Rights Reserved.
# Author: Alwyn Mathew <am3156@cam.ac.uk>
# This file cannot be used without a written permission from the author(s).

import argparse
import os
import time

import yaml
from tqdm import tqdm

from DTP_API.DTP_API import DTPApi
from DTP_API.DTP_config import DTPConfig


class FixDTPGraph:
    """
    The class is used to prepare DTP for progress monitering

    Attributes
    ----------
    DTP_CONFIG : class
        an instance of DTP_Config
    DTP_API : DTP_Api, obligatory
            an instance of DTP_Api

    Methods
    -------
    update_asplanned_dtp_nodes()
        int, returns number of nodes updated
    """

    def __init__(self, dtp_config, dtp_api):
        """
        Parameters
        ----------
        dtp_config : DTP_Config, obligatory
            an instance of DTP_Config
        dtp_api : DTP_Api, obligatory
            an instance of DTP_Api
        """
        self.DTP_CONFIG = dtp_config
        self.DTP_API = dtp_api

    def __filter_asplanned(self, all_element):
        """

        Parameters
        ----------
        all_element : dict, obligatory
            Dictionary of all element nodes
        Returns
        -------
        dict
            Dictionary of filtered elements into as-planned and as-performed
        """
        filtered_node = {'as_planned': []}
        as_designed_uri = self.DTP_CONFIG.get_ontology_uri('isAsDesigned')
        for each_dict in all_element['items']:
            if as_designed_uri not in each_dict.keys() or each_dict[as_designed_uri] is True:
                filtered_node['as_planned'].append(each_dict['_iri'])
                if 'ifc:Class' in each_dict:
                    filtered_node['as_planned'].append([each_dict['_iri'], each_dict['ifc:Class']])

        return filtered_node

    def __update_node(self, iri, prev_ifc_class_value, convert_map):
        """
        Method to update node params

        Parameters
        ----------
        iri: str, obligatory
            a valid IRI of a node.
        prev_ifc_class_value: str, obligatory
            old ifcClass value
        convert_map
            ontology ifcClass conversion maps

        Returns
        -------
        bool
            return True if the node is updated and False otherwise.
        """
        new_ifc_class_value = convert_map[prev_ifc_class_value]
        delete_resp = self.DTP_API.delete_param_in_node(node_iri=iri, field="ifc:Class",
                                                        previous_field_value=prev_ifc_class_value)
        if delete_resp:
            add_resp = self.DTP_API.add_param_in_node(node_iri=iri,
                                                      field=self.DTP_CONFIG.get_ontology_uri('hasElementType'),
                                                      field_value=new_ifc_class_value)

            return True if add_resp else False
        else:
            return False

    def update_asplanned_dtp_nodes(self, convert_map):
        """
        Updates AsDesigned parameter in as-planned element nodes

        Returns
        -------
        int
            The number of updated nodes
        convert_maps
            ontology ifcClass conversion maps
        """
        num_updates = 0
        all_element = self.DTP_API.query_all_pages(self.DTP_API.fetch_element_nodes)
        filtered_nodes = self.__filter_asplanned(all_element)
        for as_planned in tqdm(filtered_nodes['as_planned']):
            # update IfcClass field
            # TODO: Remove False from below once a solution is found to replace ifc:Class
            if isinstance(as_planned, list) and False:
                iri, prev_ifc_class_value = as_planned
                # some classes are ignored
                if convert_map[prev_ifc_class_value] == 'ignore':
                    continue
                update_resp = self.__update_node(iri, prev_ifc_class_value, convert_map)
                if not update_resp:
                    raise Exception(f"Failed to update node {iri}")
            else:
                # update asDesigned field
                self.DTP_API.update_asdesigned_param_node(as_planned, is_as_designed=True)
            num_updates += 1
        return num_updates


def parse_args():
    """
    Get parameters from user
    """
    parser = argparse.ArgumentParser(description='Fix DTP graph')
    parser.add_argument('--simulation', '-s', default=False, action='store_true')
    parser.add_argument('--log_dir', '-l', type=str, help='path to log dir', required=True)
    parser.add_argument('--revert', '-r', type=str, help='path to session log file')

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.simulation:
        print('Running in the simulator mode.')
    if not os.path.exists(args.log_dir) and not args.revert:
        os.makedirs(args.log_dir)
    log_path = os.path.join(args.log_dir, f"db_session-{time.strftime('%Y%m%d-%H%M%S')}.log")
    dtp_config = DTPConfig('DTP_API/DTP_config.xml')
    dtp_api = DTPApi(dtp_config, simulation_mode=args.simulation)

    if args.revert:
        print(f'Reverting session from {args.revert}')
        dtp_api.revert_last_session(args.revert)
        print(f'Session Reverted.')
    else:
        dtp_api.init_logger(log_path)
        prepareDTP = FixDTPGraph(dtp_config, dtp_api)
        ontology_map = yaml.safe_load(open('ontology_map.yaml'))
        num_element = prepareDTP.update_asplanned_dtp_nodes(ontology_map)
        print('Number of updated element', num_element)
