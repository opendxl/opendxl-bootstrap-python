# -*- coding: utf-8 -*-
################################################################################
# Copyright (c) 2017 McAfee Inc. - All Rights Reserved.
################################################################################

import logging
from ConfigParser import ConfigParser

from dxlbootstrap.generate.templates.app.template import AppTemplate

# Configure local logger
logger = logging.getLogger(__name__)


class DxlBootstrap(object):
    """
    The purpose of the DXL Bootstrap application is to generate the structure and related
    files necessary (a project) for developing a DXL integration. Multiple templates are
    available which control the type of project to generate (a client wrapper, a persistent
    application which exposes services, etc.).
    """

    # The list of available templates
    _TEMPLATES = [
        AppTemplate()
    ]

    def __init__(self):
        """
        """
        self._templates = {}
        for template in DxlBootstrap._TEMPLATES:
            self._templates[template.name] = template

    @staticmethod
    def _load_configuration(config_file):
        """
        :param config_file:
        :return:
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
        :param template_name:
        :param config_file:
        :param dest_folder:
        :return:
        """
        try:
            if template_name not in self._templates:
                raise Exception("An unknown template name was specified '{0}'".format(template_name))

            template = self._templates[template_name]
            template.run(self._load_configuration(config_file), dest_folder)
            print "Generation succeeded."
        except Exception as e:
            print "Error: {0}\n".format(str(e))
            logger.exception("Error during generation.")
