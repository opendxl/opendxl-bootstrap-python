from dxlbootstrap.generate.core.template \
    import Template, TemplateConfig, PythonPackageConfigSection
from dxlbootstrap.generate.core.component \
    import DirTemplateComponent, FileTemplateComponent, CodeTemplateComponent
from dxlbootstrap import get_version


class ClientTemplateConfig(TemplateConfig):
    """
    Configuration for the client template
    """

    def __init__(self, config):
        """
        Constructs the configuration

        :param config: The Python configuration to wrap
        """
        super(ClientTemplateConfig, self).__init__(config)

    @property
    def client_section(self):
        """
        Returns the "client" section of the configuration

        :return: The "client" section of the configuration
        """
        class ClientConfigSection(PythonPackageConfigSection):
            """
            Configuration section for the "client"
            """

            def __init__(self, template_config):
                """
                Constructs the section

                :param template_config: The template configuration
                """
                super(ClientConfigSection, self).__init__(template_config, "Client")

            @property
            def client_class_name(self):
                """
                Returns the name for the "client" Python class

                :return: The name for the "client" Python class
                """
                return self._get_property("clientClassName", required=True)

            @property
            def include_example_method(self):
                """
                Returns whether to include an example method in the client class that demonstrates
                wrapping a DXL service invocation.

                :return: Whether to include an example method in the client class that demonstrates
                    wrapping a DXL service invocation.
                """
                return self._get_boolean_property("includeExampleMethod", required=False, default_value=True)

            def _get_install_requires_list(self):
                """
                Returns the list of package names that the install requires

                :return: The list of package names that the install requires
                """
                return ["dxlbootstrap", "dxlclient"]

        return ClientConfigSection(self)


class ClientTemplate(Template):
    """
    Template which is used to generate an OpenDXL "client" wrapper. The purpose of the client wrapper
    is to hide low-level details such as DXL topics and message formats.
    """

    @staticmethod
    def get_name():
        """
        The name of the template

        :return: The name of the template
        """
        return "client-template"

    @staticmethod
    def new_instance():
        """
        Factory method for the template

        :return: A new instance of the client template
        """
        return ClientTemplate()

    def __init__(self):
        """
        Constructs the template
        """
        super(ClientTemplate, self).__init__(__name__)

    def _create_template_config(self, config):
        """
        Creates and returns the client configuration

        :param config: The Python configuration
        :return: The client configuration
        """
        return ClientTemplateConfig(config)

    def _build_root_directory(self, context, components_dict):
        """
        Builds the "root" directory components of the output

        :param context: The template context
        :param components_dict: Dictionary containing components by name (and other info)
        :return: The "root" directory components of the output
        """
        config = context.template.template_config
        client_section = config.client_section

        root = DirTemplateComponent("")
        components_dict["root"] = root

        file_comp = FileTemplateComponent("README", "../../app/static/README.tmpl",
                                          {"fullName": client_section.full_name,
                                           "fullNameSep":
                                               self.create_underline(len(client_section.full_name), "="),
                                           "copyright": client_section.copyright})
        root.add_child(file_comp)

        file_comp = FileTemplateComponent("README.md", "../../app/static/README.md.tmpl",
                                          {"fullName": client_section.full_name,
                                           "copyright": client_section.copyright})
        root.add_child(file_comp)

        file_comp = FileTemplateComponent("setup.py", "../../app/static/setup.py.tmpl",
                                          {"name": client_section.name,
                                           "installRequires": self.create_install_requires(
                                               client_section.install_requires)})
        root.add_child(file_comp)

        file_comp = FileTemplateComponent("LICENSE", "../../app/static/LICENSE.tmpl")
        root.add_child(file_comp)

        file_comp = FileTemplateComponent("MANIFEST.in", "../../app/static/MANIFEST.in.tmpl")
        root.add_child(file_comp)

        file_comp = FileTemplateComponent("dist.py", "dist.py.tmpl",
                                          {"name": client_section.name})
        root.add_child(file_comp)
        file_comp = FileTemplateComponent("clean.py", "../../app/static/clean.py.tmpl",
                                          {"name": client_section.name})
        root.add_child(file_comp)

    @staticmethod
    def _build_client_directory(context, components_dict):
        """
        Builds the client directory components of the output

        :param context: The template context
        :param components_dict: Dictionary containing components by name (and other info)
        :return: The client directory components of the output
        """

        config = context.template.template_config
        client_section = config.client_section
        root = components_dict["root"]

        client_dir = DirTemplateComponent(client_section.name)
        root.add_child(client_dir)
        components_dict["client_dir"] = client_dir

        file_comp = FileTemplateComponent("__init__.py", "../../app/static/app/__init__.py.tmpl",
                                          {"appClassName": client_section.client_class_name,
                                           "relPackage": ".client"})
        client_dir.add_child(file_comp)

        include_example = client_section.include_example_method
        file_comp = FileTemplateComponent("client.py", "client/client.py.tmpl",
                                          {"clientClassName": client_section.client_class_name,
                                           "fullName": client_section.full_name,
                                           "additionalImports":
                                               ("from dxlclient.message import Request\n"
                                                "from dxlbootstrap.util import MessageUtils\n"
                                                if include_example else "")})

        if include_example:
            comp = CodeTemplateComponent("client/code/example_method.code.tmpl")
            comp.indent_level = 1
            file_comp.add_child(comp)

        client_dir.add_child(file_comp)

    @staticmethod
    def _build_sample_directory(context, components_dict):
        """
        Builds the "sample" directory components of the output

        :param context: The template context
        :param components_dict: Dictionary containing components by name (and other info)
        :return: The "sample" directory components of the output
        """
        config = context.template.template_config
        client_section = config.client_section
        root = components_dict["root"]

        sample_dir = DirTemplateComponent("sample")
        root.add_child(sample_dir)

        file_comp = FileTemplateComponent("dxlclient.config", "../../app/static/config/dxlclient.config.tmpl")
        sample_dir.add_child(file_comp)
        file_comp = FileTemplateComponent("dxlclient.config.dist", "../../app/static/config/dxlclient.config.tmpl")
        sample_dir.add_child(file_comp)

        file_comp = FileTemplateComponent("common.py", "../../app/static/sample/common.py.tmpl")
        sample_dir.add_child(file_comp)

        sample_basic_dir = DirTemplateComponent("basic")
        sample_dir.add_child(sample_basic_dir)

        include_example = client_section.include_example_method
        basic_sample_comp = FileTemplateComponent("basic_sample.py", "sample/basic/basic_sample.py.tmpl",
                                                  {"clientClassName": client_section.client_class_name,
                                                   "name": client_section.name,
                                                   "additionalImports": (
                                                       "from dxlbootstrap.util import MessageUtils\n"
                                                       if include_example else "")})
        if include_example:
            comp = CodeTemplateComponent("sample/basic/code/invoke_example_method.code.tmpl")
            comp.indent_level = 1
            basic_sample_comp.add_child(comp)

        sample_basic_dir.add_child(basic_sample_comp)

    def _build_docs_directory(self, context, components_dict):
        """
        Builds the "docs" directory components of the output

        :param context: The template context
        :param components_dict: Dictionary containing components by name (and other info)
        :return: The "docs" directory components of the output
        """
        config = context.template.template_config
        client_section = config.client_section
        root = components_dict["root"]

        doc_dir = DirTemplateComponent("doc")
        root.add_child(doc_dir)

        file_comp = FileTemplateComponent("conf.py", "../../app/static/doc/conf.py.tmpl",
                                          {"copyright": client_section.copyright,
                                           "fullName": client_section.full_name,
                                           "name": client_section.name})
        doc_dir.add_child(file_comp)

        sdk_dir = DirTemplateComponent("sdk")
        doc_dir.add_child(sdk_dir)

        file_comp = FileTemplateComponent("index.rst", "doc/sdk/index.rst.tmpl",
                                          {"fullName": client_section.full_name,
                                           "fullNameSep":
                                               self.create_underline(len(client_section.full_name), "="),
                                           "name": client_section.name})
        sdk_dir.add_child(file_comp)

        file_comp = FileTemplateComponent("README.html", "../../app/static/doc/sdk/README.html.tmpl",
                                          {"copyright": client_section.copyright,
                                           "fullName": client_section.full_name})
        sdk_dir.add_child(file_comp)

        file_comp = FileTemplateComponent("overview.rst", "../../app/static/doc/sdk/overview.rst.tmpl")
        sdk_dir.add_child(file_comp)

        file_comp = FileTemplateComponent("installation.rst", "doc/sdk/installation.rst.tmpl",
                                          {"name": client_section.name})
        sdk_dir.add_child(file_comp)

        file_comp = FileTemplateComponent("sampleconfig.rst", "../../app/static/doc/sdk/sampleconfig.rst.tmpl",
                                          {"fullName": client_section.full_name})
        sdk_dir.add_child(file_comp)

    def _get_root_component(self, context):
        """
        Returns the root component for the template generation

        :param context: The template context
        :return: The root component for the template generation
        """

        components_dict = {}

        self._build_root_directory(context, components_dict)
        self._build_client_directory(context, components_dict)
        self._build_sample_directory(context, components_dict)
        self._build_docs_directory(context, components_dict)

        return components_dict["root"]
