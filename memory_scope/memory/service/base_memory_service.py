import threading
from abc import ABCMeta, abstractmethod
from typing import List, Dict

from memory_scope.memory.operation.base_operation import BaseOperation
from memory_scope.scheme.message import Message
from memory_scope.utils.logger import Logger


class BaseMemoryService(metaclass=ABCMeta):
    """
    An abstract base class for managing memory operations within a multi-threaded context.
    It sets up the infrastructure for operation handling, message storage, and synchronization,
    along with logging capabilities and customizable configurations.
    """

    def __init__(self,
                 memory_operations: Dict[str, dict],
                 read_memory_key: str = "read_memory",
                 read_message_key: str = "read_message",
                 **kwargs):
        """
        Initializes the BaseMemoryService with operation definitions, keys for memory access,
        and additional keyword arguments for flexibility.

        Args:
            memory_operations (Dict[str, dict]): A dictionary defining available memory operations.
            read_memory_key (str): The key indicating a read memory operation. Defaults to "read_memory".
            read_message_key (str): The key for reading messages. Defaults to "read_message".
            **kwargs: Additional parameters to customize service behavior.
        """
        self.memory_operations: Dict[str, dict] = memory_operations
        self.read_memory_key: str = read_memory_key
        self.read_message_key: str = read_message_key

        self._operation_dict: Dict[str, BaseOperation] = {}
        self._op_description_dict: Dict[str, str] = {}
        self.chat_messages: List[Message] = []
        self.message_lock = threading.Lock()

        self.logger = Logger.get_logger()
        self.kwargs = kwargs

    @abstractmethod
    def _init_operation(self, memory_operations: Dict[str, dict]):
        """
        Initializes the memory operations with a given dictionary of operations.

        This method is to be implemented by subclasses to set up or configure
        the memory operations based on the provided dictionary.

        Args:
            memory_operations (Dict[str, dict]): A dictionary containing configuration
                                                 details for each memory operation.

        Raises:
            NotImplementedError: This exception is raised to indicate that the method
                                  needs to be overridden in the subclass.
        """
        raise NotImplementedError

    @abstractmethod
    def add_messages(self, messages: List[Message] | Message):
        raise NotImplementedError

    def start_service(self, **kwargs):
        """
        This method is intended to initiate the service with provided keyword arguments,
        preparing the necessary resources for executing operations.
        
        Args:
            **kwargs: Additional keyword arguments used to configure the service upon startup.
        """
        pass

    @abstractmethod
    def do_operation(self, op_name: str, **kwargs):
        """
        Abstract method defining the interface for executing a specific operation by its name.
        This method must be implemented by subclasses to provide the actual operation logic.

        Args:
            op_name (str): The name identifying the operation to be performed.
            **kwargs: Additional keyword arguments required for the operation execution.

        Raises:
            NotImplementedError: This exception is raised when the method is not overridden in a subclass.
        """
        raise NotImplementedError

    @property
    def op_description_dict(self) -> Dict[str, str]:
        """
        Property to retrieve a dictionary mapping operation keys to their descriptions.
        Lazily initializes the dictionary on first access.

        Returns:
            Dict[str, str]: A dictionary where keys are operation identifiers and values are their descriptions.
        """
        if not self._op_description_dict:
            self._op_description_dict = {k: v.description for k, v in self._operation_dict.items()}
        return self._op_description_dict

    def read_memory(self):
        """
        Executes the operation associated with reading memory.
        Asserts that the operation for reading memory has been initialized.

        Returns:
            Any: The result of the read memory operation.
        """
        assert self.read_memory_key in self._operation_dict, f"op={self.read_memory_key} is not inited!"
        return self.do_operation(self.read_memory_key)

    def read_message(self):
        """
        Executes the operation associated with reading messages.
        Asserts that the operation for reading messages has been initialized.

        Returns:
            Any: The result of the read message operation.
        """
        assert self.read_message_key in self._operation_dict, f"op={self.read_message_key} is not inited!"
        return self.do_operation(self.read_message_key)

    def stop_service(self):
        """
        Placeholder method to stop the service.
        Intended to be overridden by subclasses to define specific shutdown logic.
        """
        pass
