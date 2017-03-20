import pkg_resources
import re
from abc import ABCMeta, abstractproperty, abstractmethod
from ConfigParser import NoOptionError
from cStringIO import StringIO
from csv import reader


class TemplateContext(object):
    def __init__(self, template):
        self._template = template
        self._current_dir = ""
        self._file = None
        self._indent_level = 0

    @property
    def template(self):
        return self._template

    @property
    def current_directory(self):
        return self._current_dir

    @current_directory.setter
    def current_directory(self, dir):
        self._current_dir = dir

    @property
    def indent_level(self):
        return self._indent_level

    @indent_level.setter
    def indent_level(self, indent_level):
        self._indent_level = indent_level

    @property
    def file(self):
        return self._file

    @file.setter
    def file(self, file):
        self._file = file

    def write_to_file(self, lines):
        for line in lines:
            indent = ""
            for i in range(0, self._indent_level):
                indent += "    "
            self._file.write(indent + line + "\n")


class TemplateConfigSection(object):
    def __init__(self, template_config, section_name):
        self._template_config = template_config
        self._section_name = section_name
        self._config = template_config.config

    def _get_property(self, property_name, default_value=None, required=False):
        ret = None
        try:
            ret = self._config.get(self._section_name, property_name)
        except NoOptionError as ex:
            if default_value is not None:
                ret = default_value
            elif required:
                raise ex
        return ret

    def _get_boolean_property(self, property_name, default_value=None, required=False):
        ret = None
        try:
            ret = self._config.getboolean(self._section_name, property_name)
        except NoOptionError as ex:
            if default_value is not None:
                ret = default_value
            elif required:
                raise ex
        return ret

    def _get_list_property(self, property_name, default_value=None, required=False):
        list_items = []
        list_str = self._get_property(property_name)
        if list_str is not None:
            file_like_object = StringIO(list_str)
            csv_reader = reader(file_like_object, quotechar="'")
            for items in csv_reader:
                for item in items:
                    item = item.strip()
                    if len(item) > 0:
                        list_items.append(item)

        if len(list_items) is 0:
            if default_value is not None:
                list_items = default_value
            elif required:
                raise Exception("No option '{0}' in section: '{1}'".format(property_name, self._section_name))

        return list_items


class TemplateConfig(object):

    def __init__(self, config):
        self._config = config

    @property
    def config(self):
        return self._config


class Template(object):
    __metaclass__ = ABCMeta

    def __init__(self, package):
        """
        """
        self._package = package
        self._template_config = None

    @abstractproperty
    def name(self):
        pass

    def get_static_resource(self, resource_name, replace_dict=None, package=None):
        if package is None:
            package = self._package

        if replace_dict is None:
            replace_dict = {}

        resource_path = '/'.join(("static", resource_name))
        resource = pkg_resources.resource_string(package, resource_path)

        ret_lines = []
        for line in resource.splitlines():
            for key, value in replace_dict.iteritems():
                key = "\$\{" + key + "\}"
                if callable(value):
                    value = value()
                else:
                    value = str(value)
                line = re.sub(key, value, line)
            ret_lines.append(line)

        return ret_lines

    @abstractmethod
    def _create_template_config(self, config):
        pass

    @abstractmethod
    def _get_root_component(self, context):
        pass

    def _do_run(self, context):
        self._get_root_component(context).execute(context, validate_only=True)
        self._get_root_component(context).execute(context, validate_only=False)

    @property
    def template_config(self):
        return self._template_config

    def run(self, config, dest_folder):
        self._template_config = self._create_template_config(config)

        context = TemplateContext(self)
        context.current_directory = dest_folder
        self._do_run(context)
