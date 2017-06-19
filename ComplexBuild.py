import sublime, sublime_plugin

import os, copy, re

class ComplexBuildExecCommand(sublime_plugin.WindowCommand):
    """ Provides a way to execute parameterized build commands.
        All the variables in the build commands are replaced with their corresponding project value.
    """

    def __init__(self, *args, **kwds):
        sublime_plugin.WindowCommand.__init__(self, *args, **kwds)

    def run(self, **kwds):
        settings = OurSettings(self.window, kwds)

        # Make sure to use the file_regex from the build
        fileRegex = '';
        if 'file_regex' in kwds:
            fileRegex = kwds['file_regex']

        cmd = settings.expand(kwds['target_cmd']);
        working_dir = settings.expand(kwds['target_dir']);

        print("ComplexBuildExecCommand: '%s'" % cmd)

        # Make sure to echo our command first
        print(cmd)
        cmd = 'ECHO Running \"%s\" && %s' % (cmd, cmd)


        self.window.run_command("exec", {
            "cmd": cmd,
            "working_dir": working_dir,
            "file_regex": fileRegex,
            "shell": True
        })

class ComplexBuildPrintVarsCommand(sublime_plugin.WindowCommand):
    """ Command that prints the current values of our build variables """
    def __init__(self, *args, **kwds):
        sublime_plugin.WindowCommand.__init__(self, *args, **kwds)

    def run(self, **kwds):
        settings = OurSettings(self.window, kwds)

        # Show the output panel
        output_view = self.window.get_output_panel("exec")
        self.window.run_command("show_panel", {"panel": "output.exec"})
        output_view.set_read_only(False)

        # Write all the settings values
        for key in sorted(settings._values):
            output_view.run_command("append", {"characters": "%s: %s\n" % (key, settings.expand('${'+key+'}'))})

        # Make sure we leave the output view in a read-only state
        output_view.set_read_only(True)


class ComplexBuildOptionsCommand(sublime_plugin.WindowCommand):
    """ Runs the build options menu. """
    def __init__(self, *args, **kwds):
        self._settings = None
        self._cur_option = None
        self._edit_value = None
        sublime_plugin.WindowCommand.__init__(self, *args, **kwds)

    def run(self, **kwds):
        self._settings = OurSettings(self.window, kwds)

        # Show the options that we've got
        toShow = [[opt["name"], self._settings.expand(opt["show"])] for opt in self._settings._options]
        self._show_quick_panel(toShow, self._on_option_selected)

    def _on_option_selected(self, index):
        """Called when an option is selected; presents the choices for the selected option"""
        if index >= 0:
            self._cur_option = self._settings._options[index]
            # Is this a choice option, or an edit value?
            if "choices" in self._cur_option:
                choicesToShow = [c["name"] for c in self._cur_option["choices"]]
                self._show_quick_panel(choicesToShow, self._on_choice_selected)
            else:
                name = self._cur_option['name']
                self._edit_value = self._cur_option['edit_value']
                lastVal = self._settings.expand("${%s}" % self._edit_value)
                self.window.show_input_panel(name, lastVal, self._on_input_command_done, None, None)

    def _on_choice_selected(self, index):
        """Called when a choice is selected; changes the project settings accordingly"""
        if index >= 0:
            cur_choice = self._cur_option["choices"][index]
            values_to_set = cur_choice["set"]
            # Set all the values associated with a choice
            for key in values_to_set:
                self._settings.set_value(key, values_to_set[key])
        self._cur_option = None

    def _on_input_command_done(self, text):
        self._settings.set_value(self._edit_value, text)

    def _show_quick_panel(self, options, done):
        """Shows a quick panel in Sublime; works even for nested panels"""
        sublime.set_timeout(lambda: self.window.show_quick_panel(options, done), 10)


class OurSettings:
    """ Provides the means for working with the ComplexBuild settings """
    def __init__(self, window, kwds):
        self._window = window
        self._values = {}
        self._options = []

        # First read all the values from the keywords (build settings)
        if 'ComplexBuild_options' in kwds:
            self._options = kwds['ComplexBuild_options']
        if 'ComplexBuild_values' in kwds:
            self._values = kwds['ComplexBuild_values']

        # Read all the settings from the project data
        projData = self._window.project_data()
        # General settings
        if 'ComplexBuild_options' in projData:
            self._options.extend(projData['ComplexBuild_options'])
        if 'ComplexBuild_values' in projData:
            self._values.update(projData['ComplexBuild_values'])
        # Transient settings
        if 'settings' in projData:
            projSettings = projData['settings']
            if 'ComplexBuild' in projSettings:
                self._values.update(projSettings['ComplexBuild'])

        # Add the settings corresponding to the active view/project
        curFile = window.active_view().file_name()
        fileName = os.path.basename(curFile)
        baseName, extension = os.path.splitext(fileName)
        self._values['file'] = curFile
        self._values['file_path'] = os.path.dirname(curFile)
        self._values['file_name'] = fileName
        self._values['file_extension'] = extension
        self._values['file_base_name'] = baseName
        self._values['packages'] = sublime.packages_path()
        projFile = window.project_file_name()
        projFileName = os.path.basename(projFile)
        projBaseName, projExtension = os.path.splitext(projFileName)
        self._values['project'] = projFile
        self._values['project_path'] = os.path.dirname(projFile)
        self._values['project_name'] = projFileName
        self._values['project_extension'] = projExtension
        self._values['project_base_name'] = projBaseName

    def set_value(self, key, value):
        # Read the project data
        projData = self._window.project_data()
        if not 'settings' in projData:
            projData['settings'] = {}
        projSettings = projData['settings']
        if not 'ComplexBuild' in projSettings:
            projSettings['ComplexBuild'] = {}
        complexBuildProjSettings = projSettings['ComplexBuild']

        # Do the change
        complexBuildProjSettings[key] = value

        # Save back the project data
        self._window.set_project_data(projData)

        # Also set our user-values
        self._values[key] = value

    def expand(self, s):
        # Substitute all variables from our string
        needs_replace = True
        while needs_replace:
            needs_replace = False
            for key in self._values:
                oldStr = s
                s = s.replace("${%s}" % key, self._values[key])
                if s.find('${') < 0:     # Break if there is nothing else to replace
                    return s
                needs_replace = needs_replace or (oldStr != s)
        return s
