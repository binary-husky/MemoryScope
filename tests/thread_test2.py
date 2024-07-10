import sys

sys.path.append(".")

import asyncio
from concurrent.futures import ThreadPoolExecutor

from memory_scope.models.llama_index_embedding_model import LlamaIndexEmbeddingModel
from memory_scope.storage.llama_index_es_memory_store import LlamaIndexEsMemoryStore
from memory_scope.utils.logger import Logger
import ray
# Initialize Ray
ray.init()

logger = Logger.get_logger("default")

# Define the class as a Ray actor
@ray.remote
class LlamaIndexEsMemoryStoreProxy(LlamaIndexEsMemoryStore): ...


class ThreadTest(object):
    def __init__(self):
        self.task_list = []
        embedding_model_conf = {
            "module_name": "dashscope_embedding",
            "model_name": "text-embedding-v2",
            "clazz": "models.llama_index_embedding_model",
        }

        config = {
            "index_name": "0708_2",
            "es_url": "http://localhost:9200",
            "embedding_model_conf": embedding_model_conf,
            "use_hybrid": True

        }
        self.es_store = LlamaIndexEsMemoryStoreProxy.remote(**config)   # 不能在async中初始化
        self.logger = logger

    def major_func(self, i: int):
        result = ray.get(self.es_store.retrieve_memories.remote("_", top_k=10, filter_dict={"memory_id": "ggg567"}))
        return result

    def run(self):
        while True:
            executor_internal = ThreadPoolExecutor(max_workers=5)
            f1 = executor_internal.submit(self.major_func, i=1)
            f2 = executor_internal.submit(self.major_func, i=2)
            executor_internal.shutdown()
            f1.result()
            f2.result()



executor = ThreadPoolExecutor(max_workers=5)
t1 = executor.submit(ThreadTest().run)
executor.shutdown()


# Shutdown Ray
ray.shutdown()