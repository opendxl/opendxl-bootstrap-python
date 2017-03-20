from dxlbootstrap.generate.core.template import Template, TemplateConfig, TemplateConfigSection
from dxlbootstrap.generate.core.component import DirTemplateComponent, FileTemplateComponent, CodeTemplateComponent
from dxlbootstrap import get_version


class AppTemplateConfig(TemplateConfig):

    def __init__(self, config):
        super(AppTemplateConfig, self).__init__(config)

    @property
    def application_section(self):
        class ApplicationConfigSection(TemplateConfigSection):
            def __init__(self, template_config):
                super(ApplicationConfigSection, self).__init__(template_config, "Application")

            @property
            def name(self):
                return self._get_property("name", required=True)

            @property
            def full_name(self):
                return self._get_property("fullName", required=True)

            @property
            def app_class_name(self):
                return self._get_property("appClassName", required=True)

            @property
            def copyright(self):
                return self._get_property("copyright", required=False, default_value="")

            @property
            def event_handlers(self):
                return self._get_list_property("eventHandlers", required=False, default_value=[])

            @property
            def services(self):
                return self._get_list_property("services", required=False, default_value=[])

            @property
            def install_requires(self):
                reqs = self._get_list_property("installRequires", required=False, default_value=[])[:]
                reqs.insert(0, "dxlbootstrap=={0}".format(get_version()))
                reqs.insert(0, "dxlclient")
                return reqs

        return ApplicationConfigSection(self)

    def get_service_section(self, service_name):
        class ServiceConfigSection(TemplateConfigSection):
            def __init__(self, template_config):
                super(ServiceConfigSection, self).__init__(template_config, service_name)

            @property
            def service_type(self):
                return self._get_property("serviceType", required=True)

            @property
            def request_handlers(self):
                return self._get_list_property("requestHandlers", required=False, default_value=[])

        return ServiceConfigSection(self)

    def get_request_handler_section(self, name):
        class RequestHandlerConfigSection(TemplateConfigSection):
            def __init__(self, template_config):
                super(RequestHandlerConfigSection, self).__init__(template_config, name)

            @property
            def topic(self):
                return self._get_property("topic", required=True)

            @property
            def class_name(self):
                return self._get_property("className", required=True)

            @property
            def separate_thread(self):
                return self._get_boolean_property("separateThread", required=False, default_value=True)

        return RequestHandlerConfigSection(self)

    def get_event_handler_section(self, name):
        return self.get_request_handler_section(name)


class AppTemplate(Template):

    @staticmethod
    def get_name():
        return "application-template"

    @staticmethod
    def new_instance():
        return AppTemplate()

    def __init__(self):
        super(AppTemplate, self).__init__(__name__)

    def _create_template_config(self, config):
        return AppTemplateConfig(config)

    @staticmethod
    def create_border(length, char):
        ret = ""
        for x in range(0, length):
            ret += char
        return ret

    @staticmethod
    def create_install_requires(config):
        ret = ""
        first = True
        for req in config.application_section.install_requires:
            ret += "{1}\n        \"{0}\"".format(req, ("" if first else ","))
            first = False
        return ret

    @staticmethod
    def create_pip_install(config):
        ret = ""
        first = True
        for req in config.application_section.install_requires:
            ret += "{1}RUN pip install \"{0}\"".format(req, ("" if first else "\n"))
            first = False
        return ret

    def _build_root_directory(self, context, components_dict):
        config = context.template.template_config

        root = DirTemplateComponent("")
        components_dict["root"] = root

        file_comp = FileTemplateComponent("README", "README.tmpl",
                                          {"fullName": config.application_section.full_name,
                                           "fullNameSep":
                                               self.create_border(len(config.application_section.full_name), "="),
                                           "copyright": config.application_section.copyright})
        root.add_child(file_comp)

        file_comp = FileTemplateComponent("README.md", "README.md.tmpl",
                                          {"fullName": config.application_section.full_name,
                                           "copyright": config.application_section.copyright})
        root.add_child(file_comp)

        file_comp = FileTemplateComponent("setup.py", "setup.py.tmpl",
                                          {"name": config.application_section.name,
                                           "installRequires": self.create_install_requires(config)})
        root.add_child(file_comp)

        file_comp = FileTemplateComponent("LICENSE", "LICENSE.tmpl")
        root.add_child(file_comp)

        file_comp = FileTemplateComponent("MANIFEST.in", "MANIFEST.in.tmpl")
        root.add_child(file_comp)

        file_comp = FileTemplateComponent("dist.py", "dist.py.tmpl",
                                          {"name": config.application_section.name})
        root.add_child(file_comp)

        file_comp = FileTemplateComponent("Dockerfile", "Dockerfile.tmpl",
                                          {"name": config.application_section.name,
                                           "pipInstall": self.create_pip_install(config)})
        root.add_child(file_comp)

    def _build_config_directory(self, context, components_dict):
        config = context.template.template_config
        root = components_dict["root"]

        config_dir = DirTemplateComponent("config")
        root.add_child(config_dir)

        file_comp = FileTemplateComponent("logging.config", "config/logging.config.tmpl")
        config_dir.add_child(file_comp)

        file_comp = FileTemplateComponent("dxlclient.config", "config/dxlclient.config.tmpl")
        config_dir.add_child(file_comp)

        file_comp = FileTemplateComponent(config.application_section.name + ".config", "config/app.config.tmpl")
        config_dir.add_child(file_comp)

    def _build_sample_directory(self, context, components_dict):
        del context
        root = components_dict["root"]

        sample_dir = DirTemplateComponent("sample")
        root.add_child(sample_dir)

        file_comp = FileTemplateComponent("dxlclient.config", "config/dxlclient.config.tmpl")
        sample_dir.add_child(file_comp)

        file_comp = FileTemplateComponent("common.py", "sample/common.py.tmpl")
        sample_dir.add_child(file_comp)

        sample_basic_dir = DirTemplateComponent("basic")
        sample_dir.add_child(sample_basic_dir)

        basic_sample_comp = FileTemplateComponent("basic_sample.py", "sample/basic/basic_sample.py.tmpl")
        sample_basic_dir.add_child(basic_sample_comp)
        components_dict["basic_sample_comp"] = basic_sample_comp

    def _build_docs_directory(self, context, components_dict):

        config = context.template.template_config
        root = components_dict["root"]

        doc_dir = DirTemplateComponent("doc")
        root.add_child(doc_dir)

        file_comp = FileTemplateComponent("conf.py", "doc/conf.py.tmpl",
                                          {"copyright": config.application_section.copyright,
                                           "fullName": config.application_section.full_name,
                                           "name": config.application_section.name})
        doc_dir.add_child(file_comp)

        sdk_dir = DirTemplateComponent("sdk")
        doc_dir.add_child(sdk_dir)

        file_comp = FileTemplateComponent("index.rst", "doc/sdk/index.rst.tmpl",
                                          {"fullName": config.application_section.full_name,
                                           "fullNameSep":
                                               self.create_border(len(config.application_section.full_name), "="),
                                           "name": config.application_section.name})
        sdk_dir.add_child(file_comp)

        file_comp = FileTemplateComponent("README.html", "doc/sdk/README.html.tmpl",
                                          {"copyright": config.application_section.copyright,
                                           "fullName": config.application_section.full_name})
        sdk_dir.add_child(file_comp)

        file_comp = FileTemplateComponent("overview.rst", "doc/sdk/overview.rst.tmpl")
        sdk_dir.add_child(file_comp)

        file_comp = FileTemplateComponent("installation.rst", "doc/sdk/installation.rst.tmpl",
                                          {"name": config.application_section.name})
        sdk_dir.add_child(file_comp)

        config_title = "{0} ({1}.config)".format(config.application_section.full_name, config.application_section.name)
        file_comp = FileTemplateComponent("configuration.rst", "doc/sdk/configuration.rst.tmpl",
                                          {"fullName": config.application_section.full_name,
                                           "name": config.application_section.name,
                                           "configTitle": config_title,
                                           "configTitleSep": self.create_border(len(config_title), "-")})
        sdk_dir.add_child(file_comp)

        file_comp = FileTemplateComponent("sampleconfig.rst", "doc/sdk/sampleconfig.rst.tmpl",
                                          {"fullName": config.application_section.full_name})
        sdk_dir.add_child(file_comp)

    def _build_application_directory(self, context, components_dict):
        def _get_additional_imports():
            ret = ""
            if components_dict["has_events"] or components_dict["has_services"]:
                ret += "\n"
                if components_dict["has_services"]:
                    ret += "from dxlclient.service import ServiceRegistrationInfo\n"
                    ret += "from requests import *\n"
                if components_dict["has_events"]:
                    ret += "from events import *\n"
            return ret

        config = context.template.template_config
        root = components_dict["root"]

        app_dir = DirTemplateComponent(config.application_section.name)
        root.add_child(app_dir)
        components_dict["app_dir"] = app_dir

        file_comp = FileTemplateComponent("__init__.py", "app/__init__.py.tmpl",
                                          {"appClassName": config.application_section.app_class_name})
        app_dir.add_child(file_comp)

        app_file_comp = FileTemplateComponent("app.py", "app/app.py.tmpl",
                                              {"appClassName": config.application_section.app_class_name,
                                               "name": config.application_section.name,
                                               "fullName": config.application_section.full_name,
                                               "additionalImports": _get_additional_imports})
        components_dict["app_file_comp"] = app_file_comp

        app_dir.add_child(app_file_comp)

        file_comp = FileTemplateComponent("__main__.py", "app/__main__.py.tmpl",
                                          {"appClassName": config.application_section.app_class_name,
                                           "name": config.application_section.name})
        app_dir.add_child(file_comp)

    def _build_event_handlers(self, context, components_dict):
        config = context.template.template_config

        basic_sample_comp = components_dict["basic_sample_comp"]
        app_file_comp = components_dict["app_file_comp"]
        app_dir = components_dict["app_dir"]

        event_handlers = config.application_section.event_handlers
        if len(event_handlers) > 0:
            components_dict["has_events"] = True
            register_event_handler_def_comp = CodeTemplateComponent("app/code/register_event_handler_def.code.tmpl")
            register_event_handler_def_comp.indent_level = 1
            app_file_comp.add_child(register_event_handler_def_comp)

            file_comp = FileTemplateComponent("events.py", "app/events.py.tmpl")
            app_dir.add_child(file_comp)

            for handler_name in event_handlers:
                handler_section = config.get_event_handler_section(handler_name)
                code_comp = CodeTemplateComponent("app/code/events_event_callback.code.tmpl",
                                                  {"className": handler_section.class_name,
                                                   "name": handler_name,
                                                   "topic" : handler_section.topic})
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

    def _build_services(self, context, components_dict):
        config = context.template.template_config

        basic_sample_comp = components_dict["basic_sample_comp"]
        app_file_comp = components_dict["app_file_comp"]
        app_dir = components_dict["app_dir"]

        service_names = config.application_section.services
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
                        requests_file_comp = FileTemplateComponent("requests.py", "app/requests.py.tmpl")
                        app_dir.add_child(requests_file_comp)
                    code_comp = CodeTemplateComponent("app/code/requests_request_callback.code.tmpl",
                                                      {"className": handler_section.class_name,
                                                       "name": handler_name,
                                                       "topic": handler_section.topic})
                    requests_file_comp.add_child(code_comp)

                    code_comp = CodeTemplateComponent("app/code/service_add_topic.code.tmpl",
                                                      {"topic": handler_section.topic,
                                                       "className": handler_section.class_name,
                                                       "separateThread": handler_section.separate_thread})
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
