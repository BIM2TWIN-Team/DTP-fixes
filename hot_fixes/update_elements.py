# -*- coding: utf-8 -*-`

# Copyright University of Cambridge 2023. All Rights Reserved.
# Author: Alwyn Mathew <am3156@cam.ac.uk>
# This file cannot be used without a written permission from the author(s).

import argparse

import yaml
from tqdm import tqdm

from DTP_API.DTP_API import DTPApi
from DTP_API.DTP_config import DTPConfig

ONTOLOGY_BASE_URL = "https://www.bim2twin.eu/ontology"


class UpdateElements:
    """
    The class is used to fix element nodes

    Attributes
    ----------
    DTP_CONFIG : class
        an instance of DTP_Config
    DTP_API : DTP_Api, obligatory
            an instance of DTP_Api

    Methods
    -------
    update_element_nodes(node_type, convert_map)
        dict, returns number of as-planned and as-performed nodes updated
    update_asplanned_element_nodes(target_nodes, convert_map)
        int, returns number of as-planned nodes updated
    update_asperf_element_nodes(target_nodes, convert_map)
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

    def __filter_element_nodes(self, all_element, fixes):
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
        filtered_node = {
            'as_planned': {'as_designed': [], 'type': [], 'iri': []},
            'as_perf': {'as_designed': [], 'type': [], 'iri': []}
        }
        as_designed_uri = self.DTP_CONFIG.get_ontology_uri('isAsDesigned')
        has_element_type_uri = self.DTP_CONFIG.get_ontology_uri('hasElementType')
        for each_dict in tqdm(all_element['items']):

            # as-designed node
            condition_ad = '/ifc' in each_dict['_iri'] or each_dict[
                as_designed_uri] is True if as_designed_uri in each_dict else '/ifc' in each_dict['_iri']
            if condition_ad:
                if as_designed_uri not in each_dict.keys() and fixes in ["asdesigned", "all"]:
                    filtered_node['as_planned']['as_designed'].append(each_dict['_iri'])
                if 'ifc:Class' in each_dict.keys() and fixes in ["type", "all"]:
                    filtered_node['as_planned']['type'].append([each_dict['_iri'], each_dict['ifc:Class']])
                if '/ifcas_built-' in each_dict['_iri'] and fixes in ["iri", "all"]:
                    filtered_node['as_planned']['iri'].append(each_dict['_iri'])

            # as-built node
            condition_ab = '/asbuilt' in each_dict['_iri'] or each_dict[
                as_designed_uri] if as_designed_uri in each_dict else '/ifc' in each_dict['_iri']
            if condition_ab:
                if 'ifc:Class' in each_dict.keys() and fixes in ["asdesigned", "all"]:
                    filtered_node['as_perf']['as_designed'].append([each_dict['_iri'], each_dict['ifc:Class']])
                if has_element_type_uri in each_dict.keys() and fixes in ["type", "all"]:
                    filtered_node['as_perf']['type'].append([each_dict['_iri'], each_dict[has_element_type_uri]])
                if '/as_builtifc-' in each_dict['_iri'] and fixes in ["iri", "all"]:
                    filtered_node['as_perf']['iri'].append(each_dict['_iri'])

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

    def __update_element_node_iri(self, node_iri, updated_node_iri):
        """
        Update element node iri

        Parameters
        ----------
        node_iri: str
            iri of target node
        updated_node_iri:str
            updated iri of target node
        Returns
        -------
        bool
            return True if the node is updated and False otherwise.
        """
        node_info = self.DTP_API.fetch_node_with_iri(node_iri)['items'][0]
        delete_resp = self.DTP_API.delete_node_from_graph_with_iri(node_iri)
        if not delete_resp:
            raise Exception(f"Failed to delete node {node_iri}")

        progress = node_info[self.DTP_CONFIG.get_ontology_uri('progress')]
        timestamp = node_info[self.DTP_CONFIG.get_ontology_uri('timeStamp')]
        geometric_defect = None

        for out_edge in node_info['_outE']:
            if not out_edge['_label'] in [self.DTP_CONFIG.get_ontology_uri('hasElementType'),
                                          self.DTP_CONFIG.get_ontology_uri('intentStatusRelation'),
                                          self.DTP_CONFIG.get_ontology_uri('hasGeometricDefect')]:
                raise Exception(
                    f"intentStatusRelation, hasGeometricDefect or hasElementType not found! {out_edge['_label']}")

            if out_edge['_label'] == self.DTP_CONFIG.get_ontology_uri('hasElementType'):
                element_type = out_edge['_targetIRI']

            elif out_edge['_label'] == self.DTP_CONFIG.get_ontology_uri('intentStatusRelation'):
                target_iri = out_edge['_targetIRI']

            elif out_edge['_label'] == self.DTP_CONFIG.get_ontology_uri('hasGeometricDefect'):
                geometric_defect = out_edge['_targetIRI']

        create_resp = self.DTP_API.create_asbuilt_node(updated_node_iri, progress, timestamp, element_type, target_iri)
        link_resp = self.DTP_API.link_node_element_to_defect(updated_node_iri,
                                                             geometric_defect) if geometric_defect else True

        return True if create_resp and link_resp else False

    def update_asplanned_element_nodes(self, target_nodes, convert_map):
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
        as_designed_ud, type_ud, iri_ud = target_nodes['as_designed'], target_nodes['type'], target_nodes['iri']

        # update node type
        if type_ud:
            print("Updating as-designed type nodes...")
        for as_planned in tqdm(type_ud):
            iri, prev_ifc_class_value = as_planned
            # some classes are ignored
            if ONTOLOGY_BASE_URL not in prev_ifc_class_value:
                try:
                    if convert_map[prev_ifc_class_value] == 'ignore':
                        continue
                except KeyError:
                    raise Exception(f"'{prev_ifc_class_value}' in node {iri} not found in ontology")

            self.__update_element_type(iri, prev_ifc_class_value, convert_map)
            num_updates += 1

        # update asDesigned field
        if as_designed_ud:
            print("Updating as-designed asDesigned field...")
        for as_planned_iri in tqdm(as_designed_ud):
            self.DTP_API.update_asdesigned_param_node(as_planned_iri, is_as_designed=True)
            num_updates += 1

        return num_updates

    def update_asperf_element_nodes(self, target_nodes, convert_map):
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
        print("Updating as-built element nodes...")
        num_updates = 0
        as_designed_ud, type_ud, iri_ud = target_nodes['as_designed'], target_nodes['type'], target_nodes['iri']

        # update node type
        if type_ud:
            print("Updating as-built type nodes...")
        for as_perf in tqdm(type_ud):
            iri, prev_ifc_class_value = as_perf
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

        # update asDesigned field
        if as_designed_ud:
            print("Updating as-built asDesigned field...")
        for as_perf_iri in tqdm(as_designed_ud):
            self.DTP_API.update_asdesigned_param_node(as_perf_iri, is_as_designed=False)
            num_updates += 1

        # update iri
        if iri_ud:
            print("Updating as-built iri ...")
        for as_perf_iri in tqdm(iri_ud):
            updated_as_perf_iri = as_perf_iri.replace('/as_builtifc-', '/as_built-')
            update_resp = self.__update_element_node_iri(as_perf_iri, updated_as_perf_iri)
            if not update_resp:
                raise Exception(f"Failed to update iri: {as_perf_iri}")
            num_updates += 1

        return num_updates

    def update_element_nodes(self, node_type, fixes, convert_map):
        """
        Update element nodes

        Parameters
        ----------
        node_type: str
            node type
        fixes: str
            fixes to be done
        convert_map: dict
            ontology ifcClass conversion maps
        Returns
        -------
        dict
            The number of updated nodes
        """
        num_updates = {'as_planned': 0, 'as_perf': 0}
        print("Fetching element nodes...")
        all_element = self.DTP_API.query_all_pages(self.DTP_API.fetch_element_nodes)
        filtered_nodes = self.__filter_element_nodes(all_element, fixes)
        if node_type == 'asbuilt':
            num_updates['as_perf'] = self.update_asperf_element_nodes(filtered_nodes['as_perf'], convert_map)
        elif node_type == 'asdesigned':
            num_updates['as_planned'] = self.update_asplanned_element_nodes(filtered_nodes['as_planned'], convert_map)
        else:
            num_updates['as_perf'] = self.update_asperf_element_nodes(filtered_nodes['as_perf'], convert_map)
            num_updates['as_planned'] = self.update_asplanned_element_nodes(filtered_nodes['as_planned'], convert_map)
        return num_updates


# Below code snippet for testing only

def parse_args():
    """
    Get parameters from user
    """
    parser = argparse.ArgumentParser(description='Fix element level nodes in DTP graph')
    parser.add_argument('--simulation', '-s', default=False, action='store_true')
    parser.add_argument('--node_type', '-n', type=str, choices=['asbuilt', 'asdesigned', 'all'],
                        help='type of nodes to be updated', required=True)

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.simulation:
        print('Running in the simulator mode.')
    dtp_config = DTPConfig('DTP_API/DTP_config.xml')
    dtp_api = DTPApi(dtp_config, simulation_mode=args.simulation)

    fixElements = UpdateElements(dtp_config, dtp_api)
    element_type_map = yaml.safe_load(open('element_type_map.yaml'))
    fixes = 'asdesigned'
    num_updates = fixElements.update_element_nodes(args.node_type, fixes, element_type_map)
    print(f"Updated {num_updates['as_planned']} as-designed and {num_updates['as_perf']} as-built element nodes")
