from dxlbootstrap.generate.core.template \
    import Template, TemplateConfig, TemplateConfigSection, PythonPackageConfigSection
from dxlbootstrap.generate.core.component \
    import DirTemplateComponent, FileTemplateComponent, CodeTemplateComponent
from dxlbootstrap import get_version


class AppTemplateConfig(TemplateConfig):
    """
    Configuration for the application template
    """

    def __init__(self, config):
        """
        Constructs the configuration

        :param config: The Python configuration to wrap
        """
        super(AppTemplateConfig, self).__init__(config)

    @property
    def application_section(self):
        """
        Returns the "application" section of the configuration

        :return: The "application" section of the configuration
        """
        class ApplicationConfigSection(PythonPackageConfigSection):
            """
            Configuration section for the "application"
            """

            def __init__(self, template_config):
                """
                Constructs the section

                :param template_config: The template configuration
                """
                super(ApplicationConfigSection, self).__init__(template_config, "Application")

            @property
            def app_class_name(self):
                """
                Returns the name for the "application" Python class

                :return: The name for the "application" Python class
                """
                return self._get_property("appClassName", required=True)

            @property
            def event_handlers(self):
                """
                Returns the list of "event handler" names for the application

                :return: The list of "event handler" names for the application
                """
                return self._get_list_property("eventHandlers", required=False, default_value=[])

            @property
            def services(self):
                """
                Returns the list of "service" names for the application

                :return: The list of "service" names for the application
                """
                return self._get_list_property("services", required=False, default_value=[])

            def _get_install_requires_list(self):
                """
                Returns the list of package names that the install requires

                :return: The list of package names that the install requires
                """
                return ["dxlbootstrap", "dxlclient"]

        return ApplicationConfigSection(self)

    def get_service_section(self, service_name):
        """
        Returns the configuration section for a particular "service"

        :param service_name: The name of the service
        :return: The configuration section for a particular "service"
        """

        class ServiceConfigSection(TemplateConfigSection):
            """
            Configuration section for a particular "service"
            """
            def __init__(self, template_config):
                """
                Constructs the section

                :param template_config: The template configuration
                """
                super(ServiceConfigSection, self).__init__(template_config, service_name)

            @property
            def service_type(self):
                """
                Returns the service type

                :return: The service type
                """
                return self._get_property("serviceType", required=True)

            @property
            def request_handlers(self):
                """
                Returns the list of request handler "names" for the service
                :return:
                """
                return self._get_list_property("requestHandlers", required=False, default_value=[])

        return ServiceConfigSection(self)

    def get_request_handler_section(self, name):
        """
        Returns the configuration section for a particular "request handler"

        :param name: The name of the request handler
        :return: The configuration section for a particular "request handler"
        """

        class RequestHandlerConfigSection(TemplateConfigSection):
            """
            Configuration section for a particular "request handler"
            """

            def __init__(self, template_config):
                """
                Constructs the section

                :param template_config: The template configuration
                """
                super(RequestHandlerConfigSection, self).__init__(template_config, name)

            @property
            def topic(self):
                """
                Returns the topic associated with the request handler

                :return: The topic associated with the request handler
                """
                return self._get_property("topic", required=True)

            @property
            def class_name(self):
                """
                Returns the class name to use for the request handler

                :return: The class name to use for the request handler
                """
                return self._get_property("className", required=True)

            @property
            def separate_thread(self):
                """
                Returns whether the request handler should be invoked on a thread other than the
                incoming message thread (required if synchronous requests are made in the handler)

                :return: Whether the request handler should be invoked on a thread other than the
                    incoming message thread (required if synchronous requests are made in the handler)
                """
                return self._get_boolean_property("separateThread", required=False, default_value=True)

        return RequestHandlerConfigSection(self)

    def get_event_handler_section(self, name):
        """
        Returns the configuration section for a particular "event handler"

        :param name: The name of the event handler
        :return: The configuration section for a particular "event handler"
        """
        return self.get_request_handler_section(name)


class AppTemplate(Template):
    """
    Template which is used to generate an OpenDXL "application". An application runs persistently and can
    listen for DXL events and/or register DXL services.
    """

    @staticmethod
    def get_name():
        """
        The name of the template

        :return: The name of the template
        """
        return "application-template"

    @staticmethod
    def new_instance():
        """
        Factory method for the template

        :return: A new instance of the application template
        """
        return AppTemplate()

    def __init__(self):
        """
        Constructs the template
        """
        super(AppTemplate, self).__init__(__name__)

    def _create_template_config(self, config):
        """
        Creates and returns the application configuration

        :param config: The Python configuration
        :return: The application configuration
        """
        return AppTemplateConfig(config)

    @staticmethod
    def create_pip_install(config):
        """
        Used to create the text content for "RUN pip install..." lines within the Dockerfile

        :param config: The application configuration
        :return: The text content for "RUN pip install..." lines within the Dockerfile
        """
        ret = ""
        first = True
        for req in config.application_section.install_requires:
            ret += "{1}RUN pip install \"{0}\"".format(req, ("" if first else "\n"))
            first = False
        return ret

    def _build_root_directory(self, context, components_dict):
        """
        Builds the "root" directory components of the output

        :param context: The template context
        :param components_dict: Dictionary containing components by name (and other info)
        :return: The "root" directory components of the output
        """
        config = context.template.template_config
        app_section = config.application_section

        root = DirTemplateComponent("")
        components_dict["root"] = root

        file_comp = FileTemplateComponent("README", "README.tmpl",
                                          {"fullName": app_section.full_name,
                                           "fullNameSep":
                                               self.create_underline(len(app_section.full_name), "="),
                                           "copyright": app_section.copyright})
        root.add_child(file_comp)

        file_comp = FileTemplateComponent("README.md", "README.md.tmpl",
                                          {"fullName": app_section.full_name,
                                           "copyright": app_section.copyright})
        root.add_child(file_comp)

        file_comp = FileTemplateComponent("setup.py", "setup.py.tmpl",
                                          {"name": app_section.name,
                                           "installRequires": self.create_install_requires(
                                               app_section.install_requires)})
        root.add_child(file_comp)

        file_comp = FileTemplateComponent("LICENSE", "LICENSE.tmpl")
        root.add_child(file_comp)

        file_comp = FileTemplateComponent("MANIFEST.in", "MANIFEST.in.tmpl")
        root.add_child(file_comp)

        file_comp = FileTemplateComponent("dist.py", "dist.py.tmpl",
                                          {"name": app_section.name})
        root.add_child(file_comp)

        file_comp = FileTemplateComponent("clean.py", "clean.py.tmpl",
                                          {"name": app_section.name})
        root.add_child(file_comp)

        file_comp = FileTemplateComponent("Dockerfile", "Dockerfile.tmpl",
                                          {"name": app_section.name,
                                           "pipInstall": self.create_pip_install(config)})
        root.add_child(file_comp)

    @staticmethod
    def _build_config_directory(context, components_dict):
        """
        Builds the "config" directory components of the output

        :param context: The template context
        :param components_dict: Dictionary containing components by name (and other info)
        :return: The "config" directory components of the output
        """
        config = context.template.template_config
        app_section = config.application_section
        root = components_dict["root"]

        config_dir = DirTemplateComponent("config")
        root.add_child(config_dir)

        file_comp = FileTemplateComponent("logging.config", "config/logging.config.tmpl")
        config_dir.add_child(file_comp)
        file_comp = FileTemplateComponent("logging.config.dist", "config/logging.config.tmpl")
        config_dir.add_child(file_comp)
        file_comp = FileTemplateComponent("dxlclient.config", "config/dxlclient.config.tmpl")
        config_dir.add_child(file_comp)
        file_comp = FileTemplateComponent("dxlclient.config.dist", "config/dxlclient.config.tmpl")
        config_dir.add_child(file_comp)
        file_comp = FileTemplateComponent(app_section.name + ".config", "config/app.config.tmpl",
                                          {"fullName": app_section.full_name})
        config_dir.add_child(file_comp)
        file_comp = FileTemplateComponent(app_section.name + ".config.dist", "config/app.config.tmpl",
                                          {"fullName": app_section.full_name})
        config_dir.add_child(file_comp)

    @staticmethod
    def _build_sample_directory(context, components_dict):
        """
        Builds the "sample" directory components of the output

        :param context: The template context
        :param components_dict: Dictionary containing components by name (and other info)
        :return: The "sample" directory components of the output
        """
        del context
        root = components_dict["root"]

        sample_dir = DirTemplateComponent("sample")
        root.add_child(sample_dir)

        file_comp = FileTemplateComponent("dxlclient.config", "config/dxlclient.config.tmpl")
        sample_dir.add_child(file_comp)
        file_comp = FileTemplateComponent("dxlclient.config.dist", "config/dxlclient.config.tmpl")
        sample_dir.add_child(file_comp)

        file_comp = FileTemplateComponent("common.py", "sample/common.py.tmpl")
        sample_dir.add_child(file_comp)

        sample_basic_dir = DirTemplateComponent("basic")
        sample_dir.add_child(sample_basic_dir)

        basic_sample_comp = FileTemplateComponent("basic_sample.py", "sample/basic/basic_sample.py.tmpl")
        sample_basic_dir.add_child(basic_sample_comp)
        components_dict["basic_sample_comp"] = basic_sample_comp

    def _build_docs_directory(self, context, components_dict):
        """
        Builds the "docs" directory components of the output

        :param context: The template context
        :param components_dict: Dictionary containing components by name (and other info)
        :return: The "docs" directory components of the output
        """
        config = context.template.template_config
        app_section = config.application_section
        root = components_dict["root"]

        doc_dir = DirTemplateComponent("doc")
        root.add_child(doc_dir)

        file_comp = FileTemplateComponent("conf.py", "doc/conf.py.tmpl",
                                          {"copyright": app_section.copyright,
                                           "fullName": app_section.full_name,
                                           "name": app_section.name})
        doc_dir.add_child(file_comp)

        sdk_dir = DirTemplateComponent("sdk")
        doc_dir.add_child(sdk_dir)

        file_comp = FileTemplateComponent("index.rst", "doc/sdk/index.rst.tmpl",
                                          {"fullName": app_section.full_name,
                                           "fullNameSep":
                                               self.create_underline(len(app_section.full_name), "="),
                                           "name": app_section.name})
        sdk_dir.add_child(file_comp)

        file_comp = FileTemplateComponent("README.html", "doc/sdk/README.html.tmpl",
                                          {"copyright": app_section.copyright,
                                           "fullName": app_section.full_name})
        sdk_dir.add_child(file_comp)

        file_comp = FileTemplateComponent("overview.rst", "doc/sdk/overview.rst.tmpl")
        sdk_dir.add_child(file_comp)

        file_comp = FileTemplateComponent("installation.rst", "doc/sdk/installation.rst.tmpl",
                                          {"name": app_section.name})
        sdk_dir.add_child(file_comp)
        file_comp = FileTemplateComponent("running.rst", "doc/sdk/running.rst.tmpl",
                                          {"name": app_section.name})
        sdk_dir.add_child(file_comp)


        config_title = "{0} ({1}.config)".format(app_section.full_name, app_section.name)
        file_comp = FileTemplateComponent("configuration.rst", "doc/sdk/configuration.rst.tmpl",
                                          {"fullName": app_section.full_name,
                                           "name": app_section.name,
                                           "configTitle": config_title,
                                           "configTitleSep": self.create_underline(len(config_title), "-")})
        sdk_dir.add_child(file_comp)

        file_comp = FileTemplateComponent("sampleconfig.rst", "doc/sdk/sampleconfig.rst.tmpl",
                                          {"fullName": app_section.full_name})
        sdk_dir.add_child(file_comp)

    @staticmethod
    def _build_application_directory(context, components_dict):
        """
        Builds the application directory components of the output

        :param context: The template context
        :param components_dict: Dictionary containing components by name (and other info)
        :return: The application directory components of the output
        """
        def _get_additional_imports():
            """
            Outputs the imports for the "app.py" file (based on whether event and/or request callbacks
            have been defined in the configuration)
            :return: The imports for the "app.py" file (based on whether event and/or request callbacks
                have been defined in the configuration)
            """
            ret = ""
            if components_dict["has_events"] or components_dict["has_services"]:
                ret += "\n"
                if components_dict["has_services"]:
                    ret += "from dxlclient.service import ServiceRegistrationInfo\n"
                    ret += "from requesthandlers import *\n"
                if components_dict["has_events"]:
                    ret += "from eventhandlers import *\n"
            return ret

        config = context.template.template_config
        app_section = config.application_section
        root = components_dict["root"]

        app_dir = DirTemplateComponent(app_section.name)
        root.add_child(app_dir)
        components_dict["app_dir"] = app_dir

        file_comp = FileTemplateComponent("__init__.py", "app/__init__.py.tmpl",
                                          {"appClassName": app_section.app_class_name,
                                           "relPackage": ".app"})
        app_dir.add_child(file_comp)

        app_file_comp = FileTemplateComponent("app.py", "app/app.py.tmpl",
                                              {"appClassName": app_section.app_class_name,
                                               "name": app_section.name,
                                               "fullName": app_section.full_name,
                                               "additionalImports": _get_additional_imports})
        components_dict["app_file_comp"] = app_file_comp

        app_dir.add_child(app_file_comp)

        file_comp = FileTemplateComponent("__main__.py", "app/__main__.py.tmpl",
                                          {"appClassName": app_section.app_class_name,
                                           "name": app_section.name})
        app_dir.add_child(file_comp)

    @staticmethod
    def _build_event_handlers(context, components_dict):
        """
        Builds the event handlers for the application

        :param context: The template context
        :param components_dict: Dictionary containing components by name (and other info)
        """
        config = context.template.template_config
        app_section = config.application_section

        basic_sample_comp = components_dict["basic_sample_comp"]
        app_file_comp = components_dict["app_file_comp"]
        app_dir = components_dict["app_dir"]

        event_handlers = app_section.event_handlers
        if len(event_handlers) > 0:
            components_dict["has_events"] = True
            register_event_handler_def_comp = CodeTemplateComponent("app/code/register_event_handler_def.code.tmpl")
            register_event_handler_def_comp.indent_level = 1
            app_file_comp.add_child(register_event_handler_def_comp)

            file_comp = FileTemplateComponent("eventhandlers.py", "app/eventhandlers.py.tmpl")
            app_dir.add_child(file_comp)

            for handler_name in event_handlers:
                handler_section = config.get_event_handler_section(handler_name)
                code_comp = CodeTemplateComponent("app/code/events_event_callback.code.tmpl",
                                                  {"className": handler_section.class_name,
                                                   "name": handler_name,
                                                   "topic": handler_section.topic})
                file_comp.add_child(code_comp)

                code_comp = CodeTemplateComponent("app/code/register_event_handler.code.tmpl",
                                                  {"className": handler_section.class_name,
                                                   "topic": handler_section.topic,
                                                   "callbackName": handler_name,
                                                   "separateThread": handler_section.separate_thread})
                code_comp.indent_level = 1
                register_event_handler_def_comp.add_child(code_comp)

                event_code_comp = CodeTemplateComponent("sample/basic/code/event.code.tmpl",
                                                        {"topic": handler_section.topic,
                                                         "callbackName": handler_name})
                event_code_comp.indent_level = 1
                basic_sample_comp.add_child(event_code_comp)

    @staticmethod
    def _build_services(context, components_dict):
        """
        Builds the services exposed by the application

        :param context: The template context
        :param components_dict: Dictionary containing components by name (and other info)
        """
        config = context.template.template_config
        app_section = config.application_section

        basic_sample_comp = components_dict["basic_sample_comp"]
        app_file_comp = components_dict["app_file_comp"]
        app_dir = components_dict["app_dir"]

        service_names = app_section.services
        requests_file_comp = None
        if len(service_names) > 0:
            components_dict["has_services"] = True
            register_services_def_comp = CodeTemplateComponent("app/code/register_services_def.code.tmpl")
            register_services_def_comp.indent_level = 1
            app_file_comp.add_child(register_services_def_comp)

            for service_name in service_names:
                service = config.get_service_section(service_name)
                service_create_comp = CodeTemplateComponent("app/code/service_create.code.tmpl",
                                                            {"serviceType": service.service_type,
                                                             "serviceName": service_name})
                service_create_comp.indent_level = 1
                register_services_def_comp.add_child(service_create_comp)

                request_handlers = service.request_handlers
                for handler_name in request_handlers:
                    handler_section = config.get_request_handler_section(handler_name)
                    if requests_file_comp is None:
                        requests_file_comp = FileTemplateComponent("requesthandlers.py", "app/requesthandlers.py.tmpl")
                        app_dir.add_child(requests_file_comp)
                    code_comp = CodeTemplateComponent("app/code/requests_request_callback.code.tmpl",
                                                      {"className": handler_section.class_name,
                                                       "name": handler_name,
                                                       "topic": handler_section.topic})
                    requests_file_comp.add_child(code_comp)

                    code_comp = CodeTemplateComponent("app/code/service_add_topic.code.tmpl",
                                                      {"topic": handler_section.topic,
                                                       "className": handler_section.class_name,
                                                       "separateThread": handler_section.separate_thread,
                                                       "callbackName": handler_name})
                    code_comp.indent_level = 1
                    register_services_def_comp.add_child(code_comp)

                    request_code_comp = CodeTemplateComponent("sample/basic/code/request.code.tmpl",
                                                              {"topic": handler_section.topic,
                                                               "name": handler_name})
                    request_code_comp.indent_level = 1
                    basic_sample_comp.add_child(request_code_comp)

                code_comp = CodeTemplateComponent("app/code/service_register.code.tmpl",)
                code_comp.indent_level = 1
                register_services_def_comp.add_child(code_comp)

    def _get_root_component(self, context):
        """
        Returns the root component for the template generation

        :param context: The template context
        :return: The root component for the template generation
        """

        components_dict = {
            "has_services": False,
            "has_events": False
        }

        self._build_root_directory(context, components_dict)
        self._build_config_directory(context, components_dict)
        self._build_sample_directory(context, components_dict)
        self._build_docs_directory(context, components_dict)
        self._build_application_directory(context, components_dict)
        self._build_event_handlers(context, components_dict)
        self._build_services(context, components_dict)

        return components_dict["root"]
