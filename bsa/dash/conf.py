"""
This module defines the configuration used by the BSA.

It contains the default configuration which is generated when the program is
first run, as well as the code responsible for the serialization and
deserialization of the config file itself. The config file is stored using
the TOML format.
"""

from dataclasses import dataclass
import os
import toml


@dataclass
class Conf:
    """
    Define configuration to be used across modules.

    This class serializes the config, (or creates a new one) then places the
    configuration itself into attributes for easy access. When instantiated,
    it creates a config object which is used across the program to access
    settings.
    """

    # Base configuration
    BASE = {
        'host': 'localhost',
        'port': 8080,
        # Resolves to the directory that main.py is located in
        'root_directory': os.getcwd(),
        'web_directory': os.path.join(os.getcwd(), "www"),
        'login_timeout': 10,
        'enable_admin_interface': True,
        'number_of_rounds': 7,
        'questions_per_round': 8,
        'number_of_bonus_rounds': 1,
        'questions_per_bonus_round': 8
    }
    
    host: str
    port: int
    root_directory: str
    web_directory: str
    login_timeout: int
    enable_admin_interface: bool
    number_of_rounds: int
    questions_per_round: int
    number_of_bonus_rounds: int
    questions_per_bonus_round: int

    def __init__(self):
        # Try loading config from file. If it doesn't exist, use the base conf.
        try:
            config = toml.load(os.path.join(os.getcwd(), "conf.toml"))
        except FileNotFoundError:
            with open("conf.toml", "w") as conf:
                toml.dump(Conf.BASE, conf)
            config = Conf.BASE

        # Set config as attributes.
        for key, value in config.items():
            setattr(self, key, value)
    
    @property
    def template_directory(self) -> str:
        return os.path.join(self.web_directory, "templates/")
    
    @property
    def static_directory(self) -> str:
        return os.path.join(self.web_directory, "static/")
    
    @property
    def storage_directory(self) -> str:
        return os.path.join(self.root_directory, "storage/")

# Instantiate config. This variable is the item that gets
# imported by everything else.
conf = Conf()
