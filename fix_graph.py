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

ONTOLOGY_BASE_URL = "https://www.bim2twin.eu/ontology"


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
    update_dtp_nodes(node_type, convert_map)
        dict, returns number of as-planned and as-performed nodes updated
    update_asplanned_dtp_nodes(target_nodes, convert_map)
        int, returns number of as-planned nodes updated
    update_asperf_dtp_nodes(target_nodes, convert_map)
        int, returns number of as-performed nodes updated
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

    def __filter_nodes(self, all_element):
        """
        Filter as-built and as-designed nodes according to the requirements

        Parameters
        ----------
        all_element : dict, obligatory
            Dictionary of all element nodes
        Returns
        -------
        dict
            Dictionary of filtered elements into as-planned and as-performed
        """
        print("Filtering nodes...")
        filtered_node = {'as_planned': [], 'as_perf': []}
        as_designed_uri = self.DTP_CONFIG.get_ontology_uri('isAsDesigned')
        has_element_type_uri = self.DTP_CONFIG.get_ontology_uri('hasElementType')
        for each_dict in tqdm(all_element['items']):
            # as-designed node
            if 'ifc' in each_dict['_iri'] or each_dict[as_designed_uri] is True:
                if as_designed_uri not in each_dict.keys():
                    filtered_node['as_planned'].append(each_dict['_iri'])
                if 'ifc:Class' in each_dict.keys():
                    filtered_node['as_planned'].append([each_dict['_iri'], each_dict['ifc:Class']])
            # as-built node
            if 'asbuilt' in each_dict['_iri'] or each_dict[as_designed_uri] is False:
                if 'ifc:Class' in each_dict.keys():
                    filtered_node['as_perf'].append([each_dict['_iri'], each_dict['ifc:Class']])
                if has_element_type_uri in each_dict.keys():
                    filtered_node['as_perf'].append([each_dict['_iri'], each_dict[has_element_type_uri]])

        return filtered_node

    def __update_element_type(self, iri, prev_ifc_class_value, convert_map):
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
        if ONTOLOGY_BASE_URL in prev_ifc_class_value:
            target_field = self.DTP_CONFIG.get_ontology_uri('hasElementType')
            new_ifc_class_value = prev_ifc_class_value
        else:
            target_field = "ifc:Class"
            new_ifc_class_value = convert_map[prev_ifc_class_value]

        # remove field
        delete_resp = self.DTP_API.delete_param_in_node(node_iri=iri, field=target_field,
                                                        previous_field_value=prev_ifc_class_value)
        if not delete_resp:
            # if deleting param failed, check if the node contain the field or not
            node = self.DTP_API.fetch_node_with_iri(iri)['items'][0]
            delete_resp = False if target_field in node.keys() else True
            if not delete_resp:
                raise Exception(f"Failed to delete {target_field} param from node {iri}")

        if delete_resp:
            # link node with hasElementType
            link_resp = self.DTP_API.link_node_element_to_element_type(element_node_iri=iri,
                                                                       element_type_iri=new_ifc_class_value)
            if not link_resp:
                raise Exception(f"Failed to link node {iri} to {new_ifc_class_value}")

            return True if link_resp else False
        else:
            return False

    def update_asplanned_dtp_nodes(self, target_nodes, convert_map):
        """
        Updates as-planned element nodes

        Parameters
        ----------
        target_nodes: dict
            Dictionary with target node info
        convert_map
            ontology ifcClass conversion maps

        Returns
        -------
        int
            The number of updated nodes
        """
        print("Updating as-designed nodes...")
        num_updates = 0
        for as_planned in tqdm(target_nodes):
            # update IfcClass field
            if isinstance(as_planned, list):
                iri, prev_ifc_class_value = as_planned
                # some classes are ignored
                if ONTOLOGY_BASE_URL not in prev_ifc_class_value:
                    try:
                        if convert_map[prev_ifc_class_value] == 'ignore':
                            continue
                    except KeyError:
                        raise Exception(f"'{prev_ifc_class_value}' in node {iri} not found in ontology")

                self.__update_element_type(iri, prev_ifc_class_value, convert_map)
            else:
                # update asDesigned field
                iri = as_planned
                self.DTP_API.update_asdesigned_param_node(iri, is_as_designed=True)
            num_updates += 1
        return num_updates

    def update_asperf_dtp_nodes(self, target_nodes, convert_map):
        """
        Updates as-performed element nodes

        Parameters
        ----------
        target_nodes: dict
            Dictionary with target node info
        convert_map
            ontology ifcClass conversion maps

        Returns
        -------
        int
            The number of updated nodes
        """
        print("Updating as-built nodes...")
        num_updates = 0
        for as_planned in tqdm(target_nodes):
            # update IfcClass field
            iri, prev_ifc_class_value = as_planned
            # some classes are ignored
            if ONTOLOGY_BASE_URL not in prev_ifc_class_value:
                try:
                    if convert_map[prev_ifc_class_value] == 'ignore':
                        continue
                except KeyError:
                    raise Exception(f"'{prev_ifc_class_value}' in node {iri} not found in ontology")

            update_resp = self.__update_element_type(iri, prev_ifc_class_value, convert_map)
            if not update_resp:
                raise Exception(f"Failed to update node {iri}")
            num_updates += 1
        return num_updates

    def update_dtp_nodes(self, node_type, convert_map):
        """
        Update DTP nodes

        Parameters
        ----------
        node_type: str
            node type
        convert_map: dict
            ontology ifcClass conversion maps
        Returns
        -------
        dict
            The number of updated nodes
        """
        num_updates = {'as_planned': 0, 'as_perf': 0}
        print("Fetching nodes...")
        all_element = self.DTP_API.query_all_pages(self.DTP_API.fetch_element_nodes)
        filtered_nodes = self.__filter_nodes(all_element)
        if node_type == 'asbuilt':
            num_updates['as_perf'] = self.update_asperf_dtp_nodes(filtered_nodes['as_perf'], convert_map)
        elif node_type == 'asdesigned':
            num_updates['as_planned'] = self.update_asplanned_dtp_nodes(filtered_nodes['as_planned'], convert_map)
        else:
            num_updates['as_perf'] = self.update_asperf_dtp_nodes(filtered_nodes['as_perf'], convert_map)
            num_updates['as_planned'] = self.update_asplanned_dtp_nodes(filtered_nodes['as_planned'], convert_map)
        return num_updates


def parse_args():
    """
    Get parameters from user
    """
    parser = argparse.ArgumentParser(description='Fix DTP graph')
    parser.add_argument('--simulation', '-s', default=False, action='store_true')
    parser.add_argument('--revert', '-r', type=str, help='path to session log file')
    parser.add_argument('--node_type', '-n', type=str, choices=['asbuilt', 'asdesigned', 'all'],
                        help='type of nodes to be updated')

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.simulation:
        print('Running in the simulator mode.')
    dtp_config = DTPConfig('DTP_API/DTP_config.xml')
    dtp_api = DTPApi(dtp_config, simulation_mode=args.simulation)

    if args.revert:
        print(f'Reverting session from {args.revert}')
        dtp_api.revert_last_session(args.revert)
        print(f'Session Reverted.')
    else:
        assert args.node_type, "Please set node type with --node_type"
        fixDTP = FixDTPGraph(dtp_config, dtp_api)
        ontology_map = yaml.safe_load(open('ontology_map.yaml'))
        num_updates = fixDTP.update_dtp_nodes(args.node_type, ontology_map)
        print(f"Updated {num_updates['as_planned']} as-designed nodes and {num_updates['as_perf']} as-built nodes")
