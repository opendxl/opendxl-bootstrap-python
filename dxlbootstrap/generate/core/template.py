from __future__ import absolute_import
from abc import ABCMeta, abstractmethod
from csv import reader
from io import StringIO
from operator import itemgetter
import re
import pkg_resources
from ..._exceptions import NoOptionError


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
    def current_directory(self, d): # pylint: disable=invalid-name
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
    def file(self, f): # pylint: disable=invalid-name
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
            for _ in range(0, self._indent_level):
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
        ret = default_value
        if self._config.has_option(self._section_name, property_name):
            ret = self._config.get(self._section_name, property_name)
        elif required:
            raise NoOptionError(property_name, self._section_name)
        return ret

    def _get_boolean_property(self, property_name, default_value=None, required=False):
        """
        Returns the boolean value for the specified property

        :param property_name: The property name
        :param default_value: The default value
        :param required: If the value is required
        :return: The value for the specified property
        """
        ret = default_value
        if self._config.has_option(self._section_name, property_name):
            ret = self._config.getboolean(self._section_name, property_name)
        elif required:
            raise NoOptionError(property_name, self._section_name)
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
                    if item:
                        list_items.append(item)

        if not list_items:
            if default_value is not None:
                list_items = default_value
            elif required:
                raise NoOptionError(property_name, self._section_name)

        return list_items


class PythonPackageConfigSection(TemplateConfigSection):
    """
    Section that is used to access properties related to the generation of a Python package.
    This includes high-level information such as the package name, copyright information, etc.
    """

    DEFAULT_LANGUAGE_VERSION = "2.7.9"
    UNIVERSAL_LANGUAGE_VERSION = "universal"

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

    @staticmethod
    def _get_install_requires_list():
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

    @property
    def language_versions(self):
        """
        Returns a list containing the Python language versions that the
        application requires.

        :return: A list of the Python language versions that the application
            requires.
        """
        versions = \
            [version.lower() for version in self._get_list_property(
                "languageVersions", required=False,
                default_value=[self.DEFAULT_LANGUAGE_VERSION])]
        if self.UNIVERSAL_LANGUAGE_VERSION in versions:
            versions = [self.UNIVERSAL_LANGUAGE_VERSION]
        else:
            version_component_list = []
            for version in versions:
                if not re.match(r'^\d+(\.\d*){0,2}$', version):
                    raise Exception("Unexpected value in languageVersions: " +
                                    version + ". Expected X(.Y.Z) format " +
                                    "(for example, '2', '2.7', or '2.7.9') or '" +
                                    self.UNIVERSAL_LANGUAGE_VERSION + "'.")
                version_components = re.split(r'\D+', version)
                while len(version_components) < 3:
                    version_components.append('x')
                version_component_list.append(version_components)
                sorted_by_z = sorted(version_component_list, key=itemgetter(2))
                sorted_by_y = sorted(sorted_by_z, key=itemgetter(1))
                sorted_by_x = sorted(sorted_by_y, key=itemgetter(0))
                versions = [".".join(version_components).replace(".x", "") \
                            for version_components in sorted_by_x]
        return versions


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


class Template(ABCMeta('ABC', (object,), {'__slots__': ()})): # compatible metaclass with Python 2 *and* 3
    """
    A template type that is used to determine what will be generated (application template vs.
    client wrapper template, etc.)
    """

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
        resource = pkg_resources.resource_string(package, resource_path).decode("utf8")

        ret_lines = []
        for line in resource.splitlines():
            for key, value in replace_dict.items():
                key = r"\$\{" + key + r"\}"
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
        for _ in range(0, length):
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

    @staticmethod
    def _has_only_python_2_support(versions):
        """
        Determines from a list of supported language versions if only Python 2
        is supported.

        :param versions: List of supported language versions in the configuration.
        :return: Returns true if the configuration only supports Python 2.x.
            Otherwise, returns false - most likely, if the configuration
            supports at least one Python 3.x version.
        """
        return versions[len(versions) - 1][0] == '2'

    @staticmethod
    def remove_z_version(version):
        """
        Removes a .Z version from a version string in X.Y.Z format. If the
        version string is not in X.Y.Z format, the version passed into
        the method is returned unchanged.

        :param version: The version string to parse.
        :return: A string with the .Z portion of the version removed.
        """
        if version.count(".") == 2:
            version = version.rpartition(".")[0]
        return version

    @staticmethod
    def create_dist_version_tag(versions, create_bdist_wheel_args=True):
        """
        Returns a tag to be applied to the name of a Python wheel package built
        with the setup.py bdist_wheel command. For example, if the supported
        versions for the package are "2" and "3", the return tag would be
        "py2.py3".

        :param versions: List of supported language versions in the configuration.
        :param create_bdist_wheel_args: If true, return the tag as the full
            parameter to be passed to the setup.py bdist_wheel command - for
            example, --python-tag py27. If false, return the tag as just the tag
            itself - for example, py27.
        :returns: The dist version tag.
        """
        version_tag = '"--universal"' if create_bdist_wheel_args else "py2.py3"
        if PythonPackageConfigSection.UNIVERSAL_LANGUAGE_VERSION not in versions:
            version_tag = '"--python-tag", "' \
                if create_bdist_wheel_args else ""
            for version in versions:
                version_tag = version_tag + "py" + Template.remove_z_version(
                    version).replace(".", "") + "."
            version_tag = version_tag[:-1]
            if create_bdist_wheel_args:
                version_tag += '"'
        return version_tag

    @staticmethod
    def create_language_requires(versions):
        """
        Returns a language requirement string for use as the 'python_requires'
        argument in setup.py.

        :param versions: List of supported versions in the configuration.
        :returns: The string for use with the 'python_requires' field in
            setup.py.
        """
        if PythonPackageConfigSection.UNIVERSAL_LANGUAGE_VERSION in versions:
            language_requires = ">=2.7.9,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*"
        else:
            language_requires = ">=" + versions[0]
            if Template._has_only_python_2_support(versions):
                language_requires = language_requires + ",<3"
        return language_requires

    @staticmethod
    def create_classifiers(versions):
        """
        Returns the text portion of the classifiers section of a setup.py file,
        with classifiers for supported language versions.

        :param versions: List of supported language versions in the configuration.
        :return: The string for use with the 'classifiers' field in setup.py.
        """
        program_language_base = '"Programming Language : Python'
        line_delimiter = "\n        "
        classifiers = line_delimiter + program_language_base + '",'
        if PythonPackageConfigSection.UNIVERSAL_LANGUAGE_VERSION in versions:
            versions = ["2", "2.7", "3", "3.4", "3.5", "3.6"]
        for version in versions:
            classifiers = classifiers + line_delimiter + \
                          program_language_base + " :: " + \
                          Template.remove_z_version(version) + '",'
        classifiers = classifiers[:-1]
        return classifiers

    @staticmethod
    def create_docker_image_language_version(versions):
        """
        Return the language version for the base Docker image to be built for
        an application.

        :param versions: List of supported language versions in the configuration.
        :return: The language version for use in the Dockerfile.
        """
        return Template.remove_z_version(
            PythonPackageConfigSection.DEFAULT_LANGUAGE_VERSION \
                if PythonPackageConfigSection.UNIVERSAL_LANGUAGE_VERSION in versions \
                else versions[0])

    @staticmethod
    def create_installation_doc_version_text(versions):
        """
        Return the supported language version text for use in the installation
        documentation.

        :param versions: List of supported language versions in the configuration.
        :return: The language version text.
        """
        os_text = " installed within a Windows or Linux environment."
        if PythonPackageConfigSection.UNIVERSAL_LANGUAGE_VERSION in versions:
            version_text = \
                "2.7.9 or higher in the Python 2.x series or " + \
                "3.4.0 or higher in the Python 3.x series" + \
                os_text
        else:
            version_text = ""
            for i, version in enumerate(versions):
                if i == len(versions) - 1 and len(versions) > 1:
                    version_text += "or "
                version_text = version_text + version
                if i < len(versions) - 1:
                    if len(versions) > 2:
                        version_text += ","
                    version_text += " "
            if len(versions) == 1:
                version_text += " or higher"
            version_text += os_text
            if Template._has_only_python_2_support(versions):
                version_text += " (Python 3 is not supported at this time)"
        return version_text
