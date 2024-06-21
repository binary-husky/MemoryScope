from abc import ABCMeta, abstractmethod

from memory_scope.chat.memory_service import MemoryService


class BaseMemoryChat(metaclass=ABCMeta):

    def __init__(self, chat_name: str, **kwargs):
        self.memory_service = MemoryService(chat_name=chat_name, **kwargs)

    @abstractmethod
    def chat_with_memory(self, query: str):
        """
        :param query:
        :return:
        """

    @abstractmethod
    def run(self):
        """
        :return:
        """
