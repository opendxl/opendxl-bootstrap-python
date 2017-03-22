# -*- coding: utf-8 -*-
################################################################################
# Copyright (c) 2017 McAfee Inc. - All Rights Reserved.
################################################################################

import logging
from ConfigParser import ConfigParser

from dxlbootstrap.generate.templates.app.template import AppTemplate
from dxlbootstrap.generate.templates.client.template import ClientTemplate

# Configure local logger
logger = logging.getLogger(__name__)


class DxlBootstrap(object):
    """
    The purpose of the OpenDXL Bootstrap application is to generate the structure and related
    files necessary (a project) for developing a DXL integration. Multiple templates are
    available which control the type of project to generate (a client wrapper, a persistent
    application which exposes services, etc.).
    """

    # The list of template factories by name
    _TEMPLATES = {
        AppTemplate.get_name(): AppTemplate.new_instance,
        ClientTemplate.get_name(): ClientTemplate.new_instance
    }

    def __init__(self):
        """
        Constructs the application
        """
        pass

    @staticmethod
    def templates():
        """
        Returns the supported templates

        :return: The supported templates
        """
        return DxlBootstrap._TEMPLATES

    @staticmethod
    def _load_configuration(config_file):
        """
        Loads and returns the configuration for the template that is being used

        :param config_file: The configuration file path
        :return: The configuration for the template that is being used
        """
        config = ConfigParser()
        read_files = config.read(config_file)
        if len(read_files) is not 1:
            raise Exception(
                "Error attempting to read configuration file: {0}".format(
                    config_file))
        return config

    def run(self, template_name, config_file, dest_folder):
        """
        Runs the bootstrap application

        :param template_name: The name of the template to use for the generation
        :param config_file: The configuration file for the specified template
        :param dest_folder: The output directory for the generation
        """
        try:
            if template_name not in self._TEMPLATES:
                raise Exception("An unknown template name was specified '{0}'".format(template_name))

            template = self._TEMPLATES[template_name]()
            template.run(self._load_configuration(config_file), dest_folder)
            print "Generation succeeded."
        except Exception as e:
            print "Error: {0}\n".format(str(e))
            logger.exception("Error during generation.")
