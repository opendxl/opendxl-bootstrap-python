import os


class TemplateComponent(object):

    def __init__(self):
        self._children = []

    def on_pre_execute(self, context, validate_only):
        pass

    def on_post_execute(self, context, validate_only):
        pass

    def on_execute(self, context, validate):
        pass

    def execute(self, context, validate_only=False):
        self.on_pre_execute(context, validate_only)
        self.on_execute(context, validate_only)
        for child in self._children:
            child.execute(context, validate_only)
        self.on_post_execute(context, validate_only)

    def add_child(self, component):
        self._children.append(component)


class DirTemplateComponent(TemplateComponent):
    def __init__(self, directory_name):
        super(DirTemplateComponent, self).__init__()
        self.prev_directory_name = None
        self._directory_name = directory_name

    def on_pre_execute(self, context, validate_only):
        self.prev_directory_name = context.current_directory
        context.current_directory = os.path.join(self.prev_directory_name, self._directory_name)

    def on_post_execute(self, context, validate_only):
        context.current_directory = self.prev_directory_name

    def on_execute(self, context, validate_only):
        if validate_only:
            return

        if not os.path.exists(context.current_directory):
            os.makedirs(context.current_directory)


class CodeTemplateComponent(TemplateComponent):
    def __init__(self, template_path, replace_dict=None):
        super(CodeTemplateComponent, self).__init__()
        self._template_path = template_path
        self._replace_dict = replace_dict
        self._indent_level = 0

    @property
    def indent_level(self):
        return self._indent_level

    @indent_level.setter
    def indent_level(self, indent_level):
        self._indent_level = indent_level

    def on_pre_execute(self, context, validate_only):
        context.indent_level += self._indent_level

    def on_post_execute(self, context, validate_only):
        context.indent_level -= self._indent_level

    def on_execute(self, context, validate_only):
        if validate_only:
            return

        context.write_to_file(
            context.template.get_static_resource(self._template_path, self._replace_dict))


class FileTemplateComponent(CodeTemplateComponent):
    def __init__(self, file_name, template_path, replace_dict=None):
        super(FileTemplateComponent, self).__init__(template_path, replace_dict)
        self._file_name = file_name

    def on_pre_execute(self, context, validate_only):
        if validate_only:
            return

        context.file = open(os.path.join(context.current_directory, self._file_name), "w")

    def on_post_execute(self, context, validate_only):
        if validate_only:
            return

        context.file.close()
        context.file = None
