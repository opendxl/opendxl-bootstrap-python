import pkg_resources
import re
from abc import ABCMeta, abstractmethod
from ConfigParser import NoOptionError
from cStringIO import StringIO
from csv import reader


class TemplateContext(object):
    """
    Context information used to communicate between different components during the
    generation process
    """
    def __init__(self, template):
        """
        Constructs the context object

        :param template: The template that is being used for the generation
        """
        self._template = template
        self._current_dir = ""
        self._file = None
        self._indent_level = 0

    @property
    def template(self):
        """
        Returns the template that is being used for the generation

        :return: The template that is being used for the generation
        """
        return self._template

    @property
    def current_directory(self):
        """
        Returns the current output directory

        :return: The current output directory
        """
        return self._current_dir

    @current_directory.setter
    def current_directory(self, d):
        """
        Sets the current output directory

        :param d: The output directory
        """
        self._current_dir = d

    @property
    def indent_level(self):
        """
        Returns the current indent level

        :return: The current indent level
        """
        return self._indent_level

    @indent_level.setter
    def indent_level(self, indent_level):
        """
        Sets the indent level

        :param indent_level: The indent level
        """
        self._indent_level = indent_level

    @property
    def file(self):
        """
        Returns the file that is currently being written to

        :return: The file that is currently being written to
        """
        return self._file

    @file.setter
    def file(self, f):
        """
        Sets the file to write to
        :param f: The file to write to
        """
        self._file = f

    def write_to_file(self, lines):
        """
        Writes the specified lines to the current file

        :param lines: The lines to write to the file
        """
        for line in lines:
            indent = ""
            for i in range(0, self._indent_level):
                indent += "    "
            self._file.write(indent + line + "\n")


class TemplateConfigSection(object):
    """
    Used to access properties from a particular section of a template configuration
    (as read from the template-specific configuration file)
    """
    def __init__(self, template_config, section_name):
        """
        Constructs the template configuration section

        :param template_config: The template configuration
        :param section_name: The name of the section within the configuration
        """
        self._template_config = template_config
        self._section_name = section_name
        self._config = template_config.config

    def _get_property(self, property_name, default_value=None, required=False):
        """
        Returns the value for the specified property

        :param property_name: The property name
        :param default_value: The default value
        :param required: If the value is required
        :return: The value associated with the specified name
        """
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
        """
        Returns the boolean value for the specified property

        :param property_name: The property name
        :param default_value: The default value
        :param required: If the value is required
        :return: The value for the specified property
        """
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
        """
        Returns a list of values for the specified property (converts comma delimited list to
        Python list)

        :param property_name: The property name
        :param default_value: The default value
        :param required: If the value is required
        :return: A list of values corresponding to the specified property
        """
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


class PythonPackageConfigSection(TemplateConfigSection):
    """
    Section that is used to access properties related to the generation of a Python package.
    This includes high-level information such as the package name, copyright information, etc.
    """

    def __init__(self, template_config, section_name):
        """
        Constructs the configuration section

        :param template_config: The template configuration
        :param section_name: The name of the section within the configuration
        """
        super(PythonPackageConfigSection, self).__init__(template_config, section_name)

    @property
    def name(self):
        """
        Returns the name of the package (used for the Python package name, etc.)

        :return: The name of the package (used for the Python package name, etc.)
        """
        return self._get_property("name", required=True)

    @property
    def full_name(self):
        """
        Returns the "full name" (human readable name) for the package

        :return: The "full name" (human readable name) for the package
        """
        return self._get_property("fullName", required=True)

    @property
    def copyright(self):
        """
        Returns the "copyright" for the package

        :return: The "copyright" for the package
        """
        return self._get_property("copyright", required=False, default_value="")

    def _get_install_requires_list(self):
        """
        Returns the list of package names that the install requires

        :return: The list of package names that the install requires
        """
        return []

    @property
    def install_requires(self):
        """
        Returns a list containing the Python packages that the application requires

        :return: A list containing the Python packages that the application requires
        """
        reqs = self._get_list_property("installRequires", required=False, default_value=[])[:]
        reqs.extend(self._get_install_requires_list())
        return reqs


class TemplateConfig(object):
    """
    The configuration settings for a template
    """

    def __init__(self, config):
        """
        Constructs the configuration

        :param config: The wrapped Python configuration object
        """
        self._config = config

    @property
    def config(self):
        """
        Returns the wrapped Python configuration object

        :return: The wrapped Python configuration object
        """
        return self._config


class Template(object):
    """
    A template type that is used to determine what will be generated (application template vs.
    client wrapper template, etc.)
    """
    __metaclass__ = ABCMeta

    def __init__(self, package):
        """
        Constructs the template

        :param package The package associated with the template (used to derive static resources, etc.)
        """
        self._package = package
        self._template_config = None

    def get_static_resource(self, resource_name, replace_dict=None, package=None):
        """
        Returns a populated static resource (reads resource, performs replacements, returns)

        :param resource_name: The name of the resource
        :param replace_dict: The dictionary for performing replacements
        :param package: The package used to resolve the resource name (relative to the package)
        :return: The populated static resource
        """
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

    @staticmethod
    def create_underline(length, char):
        """
        Used to create an underline of the specified character.

        For example: "========="

        :param length: The length of the underline
        :param char: The character to use
        :return: An underline
        """
        ret = ""
        for x in range(0, length):
            ret += char
        return ret

    @staticmethod
    def create_install_requires(requires_list):
        """
        Used to create the text content for the "install requires" portion of the Python
        setup.py file

        :param requires_list: The list of required packages
        :return: The text content for the "install requires" portion of the Python setup.py file
        """
        ret = ""
        first = True
        for req in requires_list:
            ret += "{1}\n        \"{0}\"".format(req, ("" if first else ","))
            first = False
        return ret

    @abstractmethod
    def _create_template_config(self, config):
        """
        Creates and returns a template-specific configuration from the Python configuration

        :param config: The Python configuration
        :return: A template-specific configuration
        """
        pass

    @abstractmethod
    def _get_root_component(self, context):
        """
        Returns the root component for the template generation

        :param context: The template context
        :return: The root component for the template generation
        """
        pass

    def _do_run(self, context):
        """
        Invoked when the template is being executed (for the purpose of generating output)

        :param context: The template context
        """
        # Validate (determine errors prior to writing files, etc.)
        self._get_root_component(context).execute(context, validate_only=True)
        # Execute
        self._get_root_component(context).execute(context, validate_only=False)

    @property
    def template_config(self):
        """
        Returns the template-specific configuration

        :return: The template-specific configuration
        """
        return self._template_config

    def run(self, config, dest_folder):
        """
        Executes the template (for the purpose of generating output)

        :param config: The template context
        :param dest_folder: The root folder in which to write the output of the generation
        """
        self._template_config = self._create_template_config(config)

        context = TemplateContext(self)
        context.current_directory = dest_folder
        self._do_run(context)
