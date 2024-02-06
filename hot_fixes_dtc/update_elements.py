# -*- coding: utf-8 -*-`

# Copyright University of Cambridge 2023. All Rights Reserved.
# Author: Alwyn Mathew <am3156@cam.ac.uk>
# This file cannot be used without a written permission from the author(s).

import argparse

from tqdm import tqdm

from DTP_API_DTC.DTP_API import DTPApi
from DTP_API_DTC.DTP_API import DTPConfig

ONTOLOGY_BASE_URL = "https://dtc-ontology.cms.ed.tum.de/ontology"
B2T_BASE_URL = "https://www.bim2twin.eu/ontology"


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
            'as_planned': {'as_designed': [], 'progress': [], 'iri': []},
            'as_perf': {'as_designed': [], 'type': [], 'iri': []}
        }
        b2t_asdesigned_iri = B2T_BASE_URL + "/Core#isAsDesigned"
        for each_dict in tqdm(all_element['items']):

            # as-designed
            if b2t_asdesigned_iri in each_dict.keys() and fixes in ['asdesigned', 'all']:
                node_iri, as_design_val = each_dict['_iri'], each_dict[b2t_asdesigned_iri]
                # as-designed node
                if as_design_val:
                    filtered_node['as_planned']['as_designed'].append((node_iri, as_design_val))
                # as-built node
                if not as_design_val:
                    filtered_node['as_perf']['as_designed'].append((node_iri, as_design_val))

            # progress
            if self.DTP_CONFIG.get_ontology_uri('progress') in each_dict.keys() and self.DTP_CONFIG.get_ontology_uri(
                    'isAsDesigned') and fixes in ['progress', 'all']:
                node_iri, progress_val = each_dict['_iri'], each_dict[self.DTP_CONFIG.get_ontology_uri('progress')]
                filtered_node['as_planned']['progress'].append((each_dict['_iri'], progress_val))

        return filtered_node

    def update_asplanned_element_nodes(self, target_nodes):
        """
        Updates as-planned element nodes

        Parameters
        ----------
        target_nodes: dict
            Dictionary with target node info

        Returns
        -------
        int
            The number of updated nodes
        """
        print("Updating as-designed nodes...")
        num_updates = 0
        b2t_asdesigned_iri = B2T_BASE_URL + "/Core#isAsDesigned"

        # update asDesigned field
        if target_nodes['as_designed']:
            print("Updating as-designed IRI...")
        for as_planned_iri, as_designed_val in tqdm(target_nodes['as_designed']):
            delete_resp = self.DTP_API.delete_param_in_node(node_iri=as_planned_iri, field=b2t_asdesigned_iri,
                                                            previous_field_value=as_designed_val)
            if delete_resp:
                add_resp = self.DTP_API.add_param_in_node(node_iri=as_planned_iri,
                                                          field=self.DTP_CONFIG.get_ontology_uri('isAsDesigned'),
                                                          field_value=as_designed_val)
                assert add_resp, f"Cant update isAsDesigned of node {as_planned_iri}"
            num_updates += 1

        # remove progress field
        if target_nodes['progress']:
            print("Removing progress...")
        for as_planned_iri, progress_val in tqdm(target_nodes['progress']):
            delete_resp = self.DTP_API.delete_param_in_node(node_iri=as_planned_iri,
                                                            field=self.DTP_CONFIG.get_ontology_uri('progress'),
                                                            previous_field_value=progress_val)
            assert delete_resp, f"Cant remove progress of node {as_planned_iri}"
            num_updates += 1

        return num_updates

    def update_asperf_element_nodes(self, target_nodes):
        """
        Updates as-performed element nodes

        Parameters
        ----------
        target_nodes: dict
            Dictionary with target node info

        Returns
        -------
        int
            The number of updated nodes
        """
        print("Updating as-built element nodes...")
        num_updates = 0
        b2t_asdesigned = B2T_BASE_URL + "/Core#isAsDesigned"

        # update asDesigned field
        if target_nodes['as_designed']:
            print("Updating as-designed IRI...")
        for as_planned_iri, as_designed_val in tqdm(target_nodes['as_designed']):
            delete_resp = self.DTP_API.delete_param_in_node(node_iri=as_planned_iri, field=b2t_asdesigned,
                                                            previous_field_value=as_designed_val)
            if delete_resp:
                add_resp = self.DTP_API.add_param_in_node(node_iri=as_planned_iri,
                                                          field=self.DTP_CONFIG.get_ontology_uri('isAsDesigned'),
                                                          field_value=as_designed_val)
                assert add_resp, f"Cant update isAsDesigned of node {target_nodes['iri']}"
            num_updates += 1

        return num_updates

    def update_element_nodes(self, node_type, fixes):
        """
        Update element nodes

        Parameters
        ----------
        node_type: str
            node type
        fixes: str
            fixes to be done
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
            num_updates['as_perf'] = self.update_asperf_element_nodes(filtered_nodes['as_perf'])
        elif node_type == 'asdesigned':
            num_updates['as_planned'] = self.update_asplanned_element_nodes(filtered_nodes['as_planned'])
        else:
            num_updates['as_perf'] = self.update_asperf_element_nodes(filtered_nodes['as_perf'])
            num_updates['as_planned'] = self.update_asplanned_element_nodes(filtered_nodes['as_planned'])
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
    fixes = 'asdesigned'

    fixElements = UpdateElements(dtp_config, dtp_api)
    num_updates = fixElements.update_element_nodes(args.node_type, fixes)
    print(f"Updated {num_updates['as_planned']} as-designed and {num_updates['as_perf']} as-built element nodes")
