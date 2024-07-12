import json
import os.path
from typing import Dict

import yaml

from memory_scope.utils.global_context import G_CONTEXT


class PromptHandler(object):
    """
    The `PromptHandler` class manages prompt messages by loading them from YAML or JSON files and dictionaries, 
    supporting language selection based on a global context, and providing dictionary-like access to the prompt messages.
    """

    def __init__(self, class_path: str, prompt_file: str = "", prompt_dict: dict = None, **kwargs):
        """
        Initializes the PromptHandler with paths to prompt sources and additional keyword arguments.

        Args:
            class_path (str): The path to the class where prompts are utilized.
            prompt_file (str, optional): The path to an external file containing prompts. Defaults to "".
            prompt_dict (dict, optional): A dictionary directly containing prompt definitions. Defaults to None.
            **kwargs: Additional keyword arguments that might be used in prompt handling.
        """
        self._class_path: str = class_path
        self._prompt_dict: Dict[str, str] = {}
        self.kwargs = kwargs

        file_path = self._class_path.strip(".py")

        self.add_prompt_file(file_path)

        if prompt_file:
            self.add_prompt_file(prompt_file)

        if prompt_dict:
            self.add_prompt_dict(prompt_dict)

    @staticmethod
    def file_path_completion(file_path: str) -> str:
        """
        Attempts to complete the given file path by appending either a `.yaml` or `.json` extension 
        based on the existence of the respective file. If neither exists, an exception is raised.

        Args:
            file_path (str): The base path of the file to be completed.

        Returns:
            str: The completed file path with the appropriate extension.

        Raises:
            RuntimeError: If neither the `.yaml` nor `.json` file exists at the given path.
        """
        if file_path.endswith(".yaml") or file_path.endswith(".json"):
            return file_path

        if os.path.exists(f"{file_path}.yaml"):
            return f"{file_path}.yaml"

        if os.path.exists(f"{file_path}.json"):
            return f"{file_path}.json"

        raise RuntimeError(f"{file_path}/yaml/json is not exists!")

    def add_prompt_file(self, file_path: str):
        """
        Adds prompt messages from a YAML or JSON file to the internal dictionary.

        This method supports loading prompts from files ending with '.yaml' or '.json'.
        It uses the respective libraries to parse the content and merge it into the current prompt dictionary.

        Args:
            file_path (str): The path to the YAML or JSON file containing the prompts.
        """
        file_path = self.file_path_completion(file_path)

        prompt_dict = {}

        if file_path.endswith(".yaml"):
            # Load prompts from a YAML file
            with open(file_path) as f:
                prompt_dict = yaml.load(f, yaml.FullLoader)

        elif file_path.endswith(".json"):
            # Load prompts from a JSON file (corrected file handling)
            with open(file_path) as f:
                prompt_dict = json.load(f)

        # Merge the loaded prompts into the existing dictionary
        self.add_prompt_dict(prompt_dict)

    def add_prompt_dict(self, prompt_dict: dict):
        """
        Adds prompt messages from a dictionary, ensuring each message has a valid entry for the current language.

        Args:
            prompt_dict (dict): A dictionary where keys represent prompt identifiers and values are nested dictionaries
                               containing language-specific prompt messages.

        Raises:
            RuntimeError: If a prompt message for the current language is not found.
        """
        for key, language_dict in prompt_dict.items():
            prompts = language_dict.get(G_CONTEXT.language)
            if not prompts:
                raise RuntimeError(f"{key}.prompt.{G_CONTEXT.language} is empty!")
            self._prompt_dict[key] = prompts.strip()

    @property
    def prompt_dict(self):
        """
        Retrieves the internal dictionary containing all prompt messages.

        Returns:
            dict: The dictionary of prompt messages with keys as identifiers and values as prompt strings.
        """
        return self._prompt_dict

    def __getitem__(self, key: str):
        """
        Enables accessing prompt messages using dictionary-like indexing.

        Args:
            key (str): The identifier for the prompt message.

        Returns:
            str: The prompt message corresponding to the given key.
        """
        return self._prompt_dict[key]

    def __setitem__(self, key: str, value: str):
        """
        Allows setting prompt messages using dictionary-like item assignment.

        Args:
            key (str): The identifier for the prompt message.
            value (str): The new prompt message content.
        """
        self._prompt_dict[key] = value

    def __getattr__(self, key: str):
        """
        Overrides attribute access to provide prompt messages dynamically.

        Args:
            key (str): The identifier for the prompt message attempted to access as an attribute.

        Returns:
            str: The prompt message corresponding to the given attribute-like key.
        """
        return self._prompt_dict[key]
