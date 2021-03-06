Sublime Text Complex Build plugin
=================================

Sublime Text plugin that allows creating more complex build environments, with multiple commands and variables.

This plugin is helpful if you want to:
* have multiple build commands that you frequently invoke
    * i.e., Build, Clean, Configure, Run
* have different parameters to the build commands that you want to change frequently
    * i.e., mode (debug/release/reldev), targets, run parameters, build arguments, etc.
* tailor the build system to fit your needs

Installation
------------

Install using [Package Control](https://packagecontrol.io):

* Open the Sublime Text *Command Palette*
* Select *Package Control: Install Package*
* Select *ComplexBuild*

Example usage
-------------

## User's perspective

Let's assume we have a CMake project. As a consequence, the following operations will be frequently performed:
* Configure the build system
* Build all
* Clean
* Run the build executable

For this project, we frequently modify the following parameters:
* the mode (debug/release/reldev)
* the target to be built
* additional configuration arguments to be passed to CMake
* additional build arguments to be passed when building
* run arguments (to be passed when executing the resulting executable)

At the end of this exercise, we expect the build menu (Cmd+Shift+B or Ctrl+Shift+B) to show something like:

![Build menu](https://github.com/lucteo/s-images/raw/master/build_menu.png)

Selecting "Change Options" should show something like:

![Options menu](https://github.com/lucteo/s-images/raw/master/options_menu.png)

The user can change these options; for some of them (i.e., mode, target) the user needs to chose from a set of fix values, and for others, the user can enter the corresponding textual values.

After setting up the right parameters, the users can *Configure* the project, *Build* or *Clean* the selected target, or *Run* the executable generated by building the solution. If the user encounters some problems with the build commands, it can always use the *Print build variables* command to print all the variables defined, together with all their values.

## Implementing the above scheme

For the purpose of this example, we will use a per-project build scheme; the same can be accomplished with a stand-alone Sublime Text build scheme (.sublime-build file).

There are several things that need to be configured, each in its own section:
* the `build_systems` section, containing the entries in the build menu
* the `ComplexBuild_options` section, describing the options for the build
* the `ComplexBuild_values` describing the pre-defined values we will use for the build
* the `ComplexBuild`, as part of the project settings, where user-chosen values will be stored

The first 3 sections can be placed in a dedicated Sublime Text build scheme, but the last one will always be saved in the project settings.

### `build_system` section

For our example, the `build_systems` section should be configured like the following:
```json
"build_systems":
[
    {
        "name": "Testability build",
        "target": "complex_build_exec",
        "target_cmd": "${cmdbuild}",
        "target_dir": "${builddir}",
        "variants":
        [
            {
                "name": "Change Options",
                "target": "complex_build_options"
            },
            {
                "name": "Configure",
                "target": "complex_build_exec",
                "target_cmd": "${cmdconfigure}"
            },
            {
                "name": "Clean",
                "target": "complex_build_exec",
                "target_cmd": "${cmdclean}"
            },
            {
                "name": "Run",
                "target": "complex_build_exec",
                "target_cmd": "${cmdrun}",
                "target_dir": "${rundir}"
            },
            {
                "name": "Print build variables",
                "target": "complex_build_print_vars"
            }
        ]
    }
],
```

ComplexBuild defines 3 commands that can be used in build systems:
* `complex_build_exec` -- executes the command given as `target_cmd` in the directory `target_dir`
* `complex_build_options` -- shows a menu with the options to be configured by the user
* `complex_build_print_vars` -- prints the variables currently available

We notice that the actual parameters to the `complex_build_exec` are in the form `${var_name}`. ComplexBuild replaces them with the values configured for these variables. The values of these variables can be defined in two paces: as build values, or as user-specified values

### `ComplexBuild_values` section

Here the user defines variables/values that are used directly by the build system, and typically cannot be specified by the user. For our example, we have

```json
"ComplexBuild_values":
{
    "builddir": "${project_path}",
    "rundir": "${project_path}",
    "cmdconfigure": "/usr/local/bin/cmake ${configure_args} -DCMAKE_BUILD_TYPE=${mode}",
    "cmdbuild": "make ${build_args} ${target}",
    "cmdclean": "make clean",
    "cmdrun": "${executable} ${run_args}"
},
```

We define the actual commands to be executed for each build action, along with the directories to be used for building and for running the application (in our case it's just the project path)

### The `ComplexBuild_options` section

In this section we define the menu presented to the user to easily select between different build configurations. For our example, we can have:

```json
"ComplexBuild_options":
[
    {
        "name": "Set mode",
        "show": "${mode}",
        "choices":
        [
            {
                "name": "Debug",
                "set":
                {
                    "mode": "Debug"
                }
            },
            {
                "name": "RelDev",
                "set":
                {
                    "mode": "RelDev"
                }
            },
            {
                "name": "Release",
                "set":
                {
                    "mode": "Release"
                }
            }
        ]
    },
    {
        "name": "Set target",
        "show": "${executable}",
        "choices":
        [
            {
                "name": "testability",
                "set":
                {
                    "target": "mytest",
                    "executable": "./mytest"
                }
            },
            {
                "name": "perf_test",
                "set":
                {
                    "target": "perfTest",
                    "executable": "./perfTest"
                }
            }
        ]
    },
    {
        "name": "Set configure args",
        "show": "${configure_args}",
        "edit_value": "configure_args"
    },
    {
        "name": "Set build args",
        "show": "${build_args}",
        "edit_value": "build_args"
    },
    {
        "name": "Set run args",
        "show": "${run_args}",
        "edit_value": "run_args"
    }
],
```

There are two types of options we can configure: _choices_, for which the user will be presented with drop-down lists, or _edit values_ for which the user will be presented with an edit field in which the options will be introduced. All these options have a name, and optionally a text to be displayed when showing the option; this text is usually the value of the variable that can be changed.

For the `edit_value` types of options, we need to provide a variable name in which the text introduced by the user will be placed. Chocices can allow a more advanced changing of the values; for each choice that the user can have, we can set one or more variables in a `set` list. For example, we may enable/disable different build options, stored in different variables, when we switch between debug and release builds.


### Saved options

All the values that the user will set through the _Change Options_ menu will be stored as project settings (part of the .sublime-project file). For our project, one possible configuration would be:

```json
"settings":
{
    "ComplexBuild":
    {
        "build_args": "-j4",
        "configure_args": "-G \"Unix Makefiles\"",
        "target": "mytest",
        "executable": "./mytest",
        "mode": "Release",
        "run_args": ""
    }
}
```

These will be overwritten whenever the user changes the settings from the _Change Options_ menu.
The values present here will override any value set in the `ComplexBuild_values` section.


---

With these simple configurations, one can build more and more complex build system. We can have a lot of variables that can be easily configured from an options menu, and applied as arguments to the actual build commands.

<details>
<summary><b>Complete .sublime-project file (click to expand)</b></summary>

```json
{
    "ComplexBuild_options":
    [
        {
            "name": "Set mode",
            "show": "${mode}",
            "choices":
            [
                {
                    "name": "Debug",
                    "set":
                    {
                        "mode": "Debug"
                    }
                },
                {
                    "name": "RelDev",
                    "set":
                    {
                        "mode": "RelDev"
                    }
                },
                {
                    "name": "Release",
                    "set":
                    {
                        "mode": "Release"
                    }
                }
            ]
        },
        {
            "name": "Set target",
            "show": "${executable}",
            "choices":
            [
                {
                    "name": "testability",
                    "set":
                    {
                        "target": "mytest",
                        "executable": "./mytest"
                    }
                },
                {
                    "name": "perf_test",
                    "set":
                    {
                        "target": "perfTest",
                        "executable": "./perfTest"
                    }
                }
            ]
        },
        {
            "name": "Set configure args",
            "show": "${configure_args}",
            "edit_value": "configure_args"
        },
        {
            "name": "Set build args",
            "show": "${build_args}",
            "edit_value": "build_args"
        },
        {
            "name": "Set run args",
            "show": "${run_args}",
            "edit_value": "run_args"
        }
    ],
    "ComplexBuild_values":
    {
        "builddir": "${project_path}",
        "rundir": "${project_path}",
        "cmdconfigure": "/usr/local/bin/cmake ${configure_args} -DCMAKE_BUILD_TYPE=${mode}",
        "cmdbuild": "make ${build_args} ${target}",
        "cmdclean": "make clean",
        "cmdrun": "${executable} ${run_args}"
    },
    "build_systems":
    [
        {
            "name": "Testability build",
            "target": "complex_build_exec",
            "target_cmd": "${cmdbuild}",
            "target_dir": "${builddir}",
            "variants":
            [
                {
                    "name": "Change Options",
                    "target": "complex_build_options"
                },
                {
                    "name": "Configure",
                    "target": "complex_build_exec",
                    "target_cmd": "${cmdconfigure}"
                },
                {
                    "name": "Clean",
                    "target": "complex_build_exec",
                    "target_cmd": "${cmdclean}"
                },
                {
                    "name": "Run",
                    "target": "complex_build_exec",
                    "target_cmd": "${cmdrun}",
                    "target_dir": "${rundir}"
                },
                {
                    "name": "Print build variables",
                    "target": "complex_build_print_vars"
                }
            ]
        }
    ],
    "folders":
    [
        {
            "path": "."
        },
    ],
    "settings":
    {
        "ComplexBuild":
        {
            "build_args": "-j4",
            "configure_args": "-G \"Unix Makefiles\"",
            "target": "mytest",
            "executable": "./mytest",
            "mode": "Release",
            "run_args": ""
        }
    }
}
```

</details>


Useful shortcuts
----------------

These build customization can be even more useful with the right keyboard shortcuts, to ease accessing the build features.

We recommend the following additional key configurations to be added to the key bindings:

```json
{ "keys": ["f5"], "command": "build", "args": { "variant": "Run"} },
{ "keys": ["alt+f7"], "command": "complex_build_options"},
{ "keys": ["alt+b"], "command": "show_panel" , "args" : {"panel": "output.exec"} },
```

With these additions, then the following shortcuts can be used to interact with the build system:

Key shortcut | Meaning
------------ | -------
Cmd+Shift+B (or Ctrl+Shift+B) | shows the build menu; typically used to select _Configure_, _Clean_ or the main build command
F7 or Cmd+B (or Ctrl+B) | runs the last build command selected
Alt+F7 | allows easy change of the build options
F5 | run the selected program
Alt+B | shows the last console output
