# -*- coding: utf-8 -*-`

# Copyright University of Cambridge 2023. All Rights Reserved.
# Author: Alwyn Mathew <am3156@cam.ac.uk>
# This file cannot be used without a written permission from the author(s).

import argparse

from tqdm import tqdm

from DTP_API.DTP_API import DTPApi
from DTP_API.DTP_config import DTPConfig


class UpdateTasks:
    """
    The class is used to fix task level nodes

    Attributes
    ----------
    DTP_CONFIG : class
        an instance of DTP_Config
    DTP_API : DTP_Api, obligatory
            an instance of DTP_Api

    Methods
    -------
    update_nodes(node_type, convert_map)
        dict, returns number of as-planned and as-performed nodes updated
    update_task_nodes(target_nodes)
        int, returns number of nodes updated
    update_action_nodes(target_nodes)
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

    def __filter_task_nodes(self, all_task):
        """
        Filter nodes according to the requirements

        Parameters
        ----------
        all_task : dict, obligatory
            Dictionary of all activity/operation nodes
        Returns
        -------
        dict
            Dictionary of filtered nodes
        """
        print("Filtering nodes...")
        filtered_node = {'as_planned': [], 'as_perf': []}
        has_task_type_uri = self.DTP_CONFIG.get_ontology_uri('hasTaskType')
        for each_dict in tqdm(all_task['as_planned']['items']):
            if has_task_type_uri in each_dict.keys():
                filtered_node['as_planned'].append([each_dict['_iri'], each_dict[has_task_type_uri]])
        for each_dict in tqdm(all_task['as_perf']['items']):
            if has_task_type_uri in each_dict.keys():
                filtered_node['as_perf'].append([each_dict['_iri'], each_dict[has_task_type_uri]])

        return filtered_node

    def __update_task_type(self, iri, prev_task_type):
        """
        Method to update node params

        Parameters
        ----------
        iri: str, obligatory
            a valid IRI of a node.
        prev_task_type: str, obligatory
            old activity type

        Returns
        -------
        bool
            return True if the node is updated and False otherwise.
        """
        target_field = self.DTP_CONFIG.get_ontology_uri('hasTaskType')
        new_task_type = prev_task_type

        # remove field
        delete_resp = self.DTP_API.delete_param_in_node(node_iri=iri, field=target_field,
                                                        previous_field_value=prev_task_type)
        if not delete_resp:
            # if deleting param failed, check if the node contain the field or not
            node = self.DTP_API.fetch_node_with_iri(iri)['items'][0]
            delete_resp = False if target_field in node.keys() else True
            if not delete_resp:
                raise Exception(f"Failed to delete {target_field} param from node {iri}")

        if delete_resp:
            # link node with task type
            link_resp = self.DTP_API.link_node_to_task_type(element_node_iri=iri,
                                                            element_type_iri=new_task_type)
            if not link_resp:
                raise Exception(f"Failed to link node {iri} to {new_task_type}")

            return True if link_resp else False
        else:
            return False

    def update_task_nodes(self, target_nodes):
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
        print("Updating task nodes...")
        num_updates = 0
        for target_node in tqdm(target_nodes):
            iri, prev_type = target_node
            update_resp = self.__update_task_type(iri, prev_type)
            if not update_resp:
                raise Exception(f"Failed to update node {iri}")
            num_updates += 1
        return num_updates

    def update_action_nodes(self, target_nodes):
        """
        Updates operation nodes

        Parameters
        ----------
        target_nodes: dict
            Dictionary with target node info

        Returns
        -------
        int
            The number of updated nodes
        """
        print("Updating action nodes...")
        num_updates = 0
        for target_node in tqdm(target_nodes):
            iri, prev_type = target_node
            update_resp = self.__update_task_type(iri, prev_type)
            if not update_resp:
                raise Exception(f"Failed to update node {iri}")
            num_updates += 1
        return num_updates

    def update_nodes(self, node_type):
        """
        Update element nodes

        Parameters
        ----------
        node_type: str
            node type

        Returns
        -------
        dict
            The number of updated nodes
        """
        num_updates = {'as_planned': 0, 'as_perf': 0}
        tasks = {}
        print("Fetching tasks/action nodes...")
        tasks['as_planned'] = self.DTP_API.query_all_pages(self.DTP_API.fetch_task_nodes)
        tasks['as_perf'] = self.DTP_API.query_all_pages(self.DTP_API.fetch_action_nodes)
        filtered_nodes = self.__filter_task_nodes(tasks)
        if node_type == 'asbuilt':
            num_updates['as_perf'] = self.update_action_nodes(filtered_nodes['as_perf'])
        elif node_type == 'asdesigned':
            num_updates['as_planned'] = self.update_task_nodes(filtered_nodes['as_planned'])
        else:
            num_updates['as_perf'] = self.update_action_nodes(filtered_nodes['as_perf'])
            num_updates['as_planned'] = self.update_task_nodes(filtered_nodes['as_planned'])
        return num_updates


# Below code snippet for testing only

def parse_args():
    """
    Get parameters from user
    """
    parser = argparse.ArgumentParser(description='Fix task level nodes in DTP graph')
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

    fixTask = UpdateTasks(dtp_config, dtp_api)
    num_updates = fixTask.update_nodes(args.node_type)
    print(f"Updated {num_updates['as_planned']} task nodes and {num_updates['as_perf']} action nodes")
