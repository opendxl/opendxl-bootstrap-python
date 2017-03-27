import os


class TemplateComponent(object):
    """
    Base class for components, which are responsible for outputting content during
    the generation process. Derived classes include directory, file, and code
    fragment components.
    """

    def __init__(self):
        """
        Constructs the component
        """
        self._children = []

    def on_pre_execute(self, context, validate_only):
        """
        Invoked prior to execution of the component

        :param context: The template context
        :param validate_only: Whether to only perform validation (don't create output)
        """
        pass

    def on_post_execute(self, context, validate_only):
        """
        Invoked after execution of the component

        :param context: The template context
        :param validate_only: Whether to only perform validation (don't create output)
        """
        pass

    def on_execute(self, context, validate_only):
        """
        Invoked when the component is executed (creates output, etc.)

        :param context: The template context
        :param validate_only: Whether to only perform validation (don't create output)
        """
        pass

    def execute(self, context, validate_only=False):
        """
        Executes the component (creates output, etc.)

        :param context: The template context
        :param validate_only: Whether to only perform validation (don't create output)
        """
        self.on_pre_execute(context, validate_only)
        self.on_execute(context, validate_only)
        for child in self._children:
            child.execute(context, validate_only)
        self.on_post_execute(context, validate_only)

    def add_child(self, component):
        """
        Adds a child component

        :param component: The child component to add
        """
        self._children.append(component)


class DirTemplateComponent(TemplateComponent):
    """
    Component which represents a directory in the output
    """

    def __init__(self, directory_name):
        """
        Constructs the component

        :param directory_name: The name of the directory
        """
        super(DirTemplateComponent, self).__init__()
        self.prev_directory_name = None
        self._directory_name = directory_name

    def on_pre_execute(self, context, validate_only):
        """
        Invoked prior to execution of the component

        :param context: The template context
        :param validate_only: Whether to only perform validation (don't create output)
        """
        self.prev_directory_name = context.current_directory
        context.current_directory = os.path.join(self.prev_directory_name, self._directory_name)

    def on_post_execute(self, context, validate_only):
        """
        Invoked after execution of the component

        :param context: The template context
        :param validate_only: Whether to only perform validation (don't create output)
        """
        context.current_directory = self.prev_directory_name

    def on_execute(self, context, validate_only):
        """
        Invoked when the component is executed (creates output, etc.)

        :param context: The template context
        :param validate_only: Whether to only perform validation (don't create output)
        """
        if validate_only:
            return

        if context.current_directory and not os.path.exists(context.current_directory):
            os.makedirs(context.current_directory)


class CodeTemplateComponent(TemplateComponent):
    """
    Component which represents a code fragment in the output
    """

    def __init__(self, template_path, replace_dict=None):
        """
        Constructs the component

        :param template_path: Path to the template file (which contains the fragment)
        :param replace_dict: The dictionary for performing replacements
        """
        super(CodeTemplateComponent, self).__init__()
        self._template_path = template_path
        self._replace_dict = replace_dict
        self._indent_level = 0

    @property
    def indent_level(self):
        """
        Relative indent level (from indent in context)
        :return: Returns the relative indent level (from indent in context)

        """
        return self._indent_level

    @indent_level.setter
    def indent_level(self, indent_level):
        """
        Sets the relative indent level (from indent in context)

        :param indent_level: The relative indent level (from indent in context)
        """
        self._indent_level = indent_level

    def on_pre_execute(self, context, validate_only):
        """
        Invoked prior to execution of the component

        :param context: The template context
        :param validate_only: Whether to only perform validation (don't create output)
        """
        context.indent_level += self._indent_level

    def on_post_execute(self, context, validate_only):
        """
        Invoked after execution of the component

        :param context: The template context
        :param validate_only: Whether to only perform validation (don't create output)
        """
        context.indent_level -= self._indent_level

    def on_execute(self, context, validate_only):
        """
        Invoked when the component is executed (creates output, etc.)

        :param context: The template context
        :param validate_only: Whether to only perform validation (don't create output)
        """
        if validate_only:
            return

        context.write_to_file(
            context.template.get_static_resource(self._template_path, self._replace_dict))


class FileTemplateComponent(CodeTemplateComponent):
    """
    Component which represents a file in the output
    """

    def __init__(self, file_name, template_path, replace_dict=None):
        """
        Constructs the component

        :param file_name: The name of the output file
        :param template_path: Path to the template file (which contains the fragment)
        :param replace_dict: The dictionary for performing replacements
        """
        super(FileTemplateComponent, self).__init__(template_path, replace_dict)
        self._file_name = file_name

    def on_pre_execute(self, context, validate_only):
        """
        Invoked prior to execution of the component

        :param context: The template context
        :param validate_only: Whether to only perform validation (don't create output)
        """
        if validate_only:
            return

        context.file = open(os.path.join(context.current_directory, self._file_name), "w")

    def on_post_execute(self, context, validate_only):
        """
        Invoked after execution of the component

        :param context: The template context
        :param validate_only: Whether to only perform validation (don't create output)
        """
        if validate_only:
            return

        context.file.close()
        context.file = None
