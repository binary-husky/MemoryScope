from typing import List

from memory_scope.constants.common_constants import QUERY_WITH_TS, RETRIEVE_MEMORY_NODES
from memory_scope.enumeration.memory_status_enum import MemoryNodeStatus
from memory_scope.enumeration.memory_type_enum import MemoryTypeEnum
from memory_scope.memory.worker.memory_base_worker import MemoryBaseWorker
from memory_scope.scheme.memory_node import MemoryNode
from memory_scope.utils.timer import timer


class RetrieveMemoryWorker(MemoryBaseWorker):
    """
    Retrieves memories based on specified criteria such as status, type, and timestamp.
    Processes these memories concurrently, sorts them by similarity, and logs the activity,
    facilitating efficient memory retrieval operations within a given scope.
    """

    @timer
    def retrieve_from_observation(self, query: str) -> List[MemoryNode]:
        """
        Retrieves memory nodes from observation based on a query, considering active memories 
        with specific types. If the retrieval limit is not set, an empty list is returned.

        Args:
            query (str): The query string used to filter and rank the memory nodes.

        Returns:
            List[MemoryNode]: A list of MemoryNode objects that match the query criteria, 
                             sorted by their relevance. Returns an empty list if no retrieval limit is configured.
        """
        if not self.retrieve_obs_top_k:
            return []

        filter_dict = {
            "user_name": self.user_name,
            "target_name": self.target_name,
            "status": MemoryNodeStatus.ACTIVE.value,
            "memory_type": [MemoryTypeEnum.OBSERVATION.value, MemoryTypeEnum.OBS_CUSTOMIZED.value],
        }
        # ⭐ Retrieve memories matching the query, filtered by the specified conditions, 
        #     limited to a certain number, and sorted by relevance.
        return self.memory_store.retrieve_memories(query=query,
                                                   top_k=self.retrieve_obs_top_k,
                                                   filter_dict=filter_dict)

    @timer
    def retrieve_from_insight_and_profile(self, query: str) -> List[MemoryNode]:
        """
        Retrieves memories marked as insights from the database based on a query, filtered by user, target, and set to active status.

        Args:
            query (str): The search query to match against the insights.

        Returns:
            List[MemoryNode]: A list of MemoryNode objects that match the query criteria, limited by 'retrieve_ins_pf_top_k'.
                              Returns an empty list if 'retrieve_ins_pf_top_k' is not set.
        """
        if not self.retrieve_ins_pf_top_k:
            return []

        filter_dict = {
            "user_name": self.user_name,
            "target_name": self.target_name,
            "status": MemoryNodeStatus.ACTIVE.value,
            "memory_type": MemoryTypeEnum.INSIGHT.value,
        }
        # ⭐ Retrieve insights matching the query, filtered, and limited by top_k
        return self.memory_store.retrieve_memories(query=query,
                                                   top_k=self.retrieve_ins_pf_top_k,
                                                   filter_dict=filter_dict)

    @timer
    def retrieve_expired_memory(self, query: str) -> List[MemoryNode]:
        if not self.retrieve_expired_top_k:
            return []

        filter_dict = {
            "user_name": self.user_name,
            "target_name": self.target_name,
            "status": MemoryNodeStatus.EXPIRED.value,
            "memory_type": [MemoryTypeEnum.OBSERVATION.value, MemoryTypeEnum.OBS_CUSTOMIZED.value],
        }
        return self.memory_store.retrieve_memories(query=query,
                                                   top_k=self.retrieve_expired_top_k,
                                                   filter_dict=filter_dict)

    def _run(self):
        """
        Executes the main retrieval流程 for memories. It fetches the query from the context, initiates concurrent tasks 
        to retrieve memories from observations, insights, and expired sources, collects the results, sorts them by 
        similarity score, logs the details, and finally sets the retrieved memory nodes.

        The method follows these steps:
        1. Retrieves the query from the worker's context.
        2. Submits tasks to asynchronously retrieve memories from various sources.
        3. Gathers the results from all submitted tasks.
        4. Logs the total number of collected memory nodes.
        5. Sorts the memory nodes based on their similarity scores in descending order.
        6. Logs detailed information about each memory node.
        7. Stores the processed memory nodes for further use.
        """
        query, _ = self.get_context(QUERY_WITH_TS)
        self.submit_thread_task(self.retrieve_from_observation, query=query)
        self.submit_thread_task(self.retrieve_from_insight_and_profile, query=query)
        self.submit_thread_task(self.retrieve_expired_memory, query=query)

        memory_node_list: List[MemoryNode] = []
        for result in self.gather_thread_result():
            if result:
                memory_node_list.extend(result)
        self.logger.info(f"memory_node_list.size={len(memory_node_list)}")

        if not memory_node_list:
            self.continue_run = False
            return

        memory_node_list = sorted(memory_node_list, key=lambda x: x.score_similar, reverse=True)
        for node in memory_node_list:
            self.logger.info(f"recall_stage: content={node.content} score={node.score_similar} "
                             f"type={node.memory_type} status={node.status}")
        self.set_memories(RETRIEVE_MEMORY_NODES, memory_node_list)
