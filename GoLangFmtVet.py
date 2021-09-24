import os
import shlex
import subprocess
import sys
from pathlib import Path

import sublime
import sublime_plugin


def file_is_golang(filename):
    return any([filename.endswith(ext) for ext in [".go"]])


def extension_is_valid(current_view_obj):
    current_filename = current_view_obj.file_name()
    return file_is_golang(current_filename)


class SideBarCommand(sublime_plugin.WindowCommand):

    enabled = False
    visible = True

    def get_path(self, paths):
        try:
            return paths[0]
        except IndexError:
            return self.window.active_view().file_name()

    def is_enabled(self, paths):
        return file_is_golang(self.get_path(paths))

    def is_visible(self, paths):
        return file_is_golang(self.get_path(paths))


class SideBarGoFmtCommand(SideBarCommand):

    def description(self,):
        return "Format Current File (`go fmt <filename>`)"

    def on_done(self, source, base, leaf):
        pass

    def run(self, paths):
        source = self.get_path(paths)
        base, leaf = os.path.split(source)
        name, _ = os.path.splitext(leaf)
        return None


class SideBarGoVetCommand(SideBarCommand):

    def description(self,):
        return "Lint Current File (`go vet <filename>`)"

    def on_done(self, source, base, leaf):
        pass

    def run(self, paths):
        source = self.get_path(paths)
        base, leaf = os.path.split(source)
        name, _ = os.path.splitext(leaf)
        return None


class GoFmtCommand(sublime_plugin.TextCommand):

    def __init__(self, view):
        super().__init__(view)
        self.proc_env = os.environ.copy()
        self.preexec_fn = (None if (sys.platform == "win32") else os.setsid)
        # Hide the console window on Windows
        self.startupinfo = None
        if os.name == "nt":
            self.startupinfo = subprocess.STARTUPINFO()
            self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        else:
            pass
        self.shell_cmd = "gofmt"
        self.encoding = "UTF-8"
        self.gofmt_proc = None
        return None

    def run(self, edit, *args):
        print("go_fmt")
        current_view = self.view
        current_region = sublime.Region(0, current_view.size())
        try:
            current_text = None
            if current_region.empty():
                all_regions = current_view.get_regions()
                current_region = all_regions[0]
                current_text = current_view.substr(current_region)
            else:
                current_text = current_view.substr(current_region)

            if self.shell_cmd and sys.platform == "win32":
                # Use shell=True on Windows, so self.shell_cmd is passed through with the correct escaping
                self.gofmt_proc = subprocess.Popen(
                    self.shell_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    startupinfo=self.startupinfo,
                    env=self.proc_env,
                    shell=True,
                )
            elif self.shell_cmd and sys.platform == "darwin":
                # Use a login shell on OSX, otherwise the users expected env vars won't be setup
                self.gofmt_proc = subprocess.Popen(
                    ["/usr/bin/env", "bash", "-l", "-c", self.shell_cmd],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    startupinfo=self.startupinfo,
                    env=self.proc_env,
                    preexec_fn=self.preexec_fn,
                    shell=False,
                )
            elif self.shell_cmd and sys.platform == "linux":
                # Explicitly use /bin/bash on Linux, to keep Linux and OSX as
                # similar as possible. A login shell is explicitly not used for
                # linux, as it's not required
                self.gofmt_proc = subprocess.Popen(
                    ["/usr/bin/env", "bash", "-c", self.shell_cmd],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    startupinfo=self.startupinfo,
                    env=self.proc_env,
                    preexec_fn=self.preexec_fn,
                    shell=False,
                )
            else:
                pass
            try:
                (stdout, stderr) = self.gofmt_proc.communicate(
                    input=bytes(current_text, encoding=self.encoding),
                )
                formatted_text = stdout.decode(self.encoding)
                current_view.replace(edit, current_region, formatted_text)
            finally:
                try:
                    self.gofmt_proc.kill()
                except:
                    pass
        except Exception as err:
            print(err)
            sublime.status_message(str(err))
        print("go_fmt: Done!")
        return None


class GoVetCommand(sublime_plugin.TextCommand):

    def __init__(self, view):
        super().__init__(view)
        self.proc_env = os.environ.copy()
        self.preexec_fn = (None if (sys.platform == "win32") else os.setsid)
        # Hide the console window on Windows
        self.startupinfo = None
        if os.name == "nt":
            self.startupinfo = subprocess.STARTUPINFO()
            self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        else:
            pass
        self.shell_cmd = ["go", "vet"]
        self.encoding = "UTF-8"
        self.gofmt_proc = None
        return None

    def run(self, edit, *args):
        print("go_vet")
        current_view = self.view
        current_region = sublime.Region(0, current_view.size())
        current_filename = current_view.sheet().file_name()
        current_directory = Path(current_filename).parent.absolute()
        try:
            current_text = None
            if current_region.empty():
                all_regions = current_view.get_regions()
                current_region = all_regions[0]
                current_text = current_view.substr(current_region)
            else:
                current_text = current_view.substr(current_region)

            if self.shell_cmd and sys.platform == "win32":
                # Use shell=True on Windows, so self.shell_cmd is passed through with the correct escaping
                self.gofmt_proc = subprocess.Popen(
                    self.shell_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    startupinfo=self.startupinfo,
                    env=self.proc_env,
                    cwd=current_directory,
                    shell=True,
                )
            elif self.shell_cmd and (sys.platform in ("darwin", "linux")):
                # Use a login shell on OSX, otherwise the users expected env vars won't be setup
                self.gofmt_proc = subprocess.Popen(
                    self.shell_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    startupinfo=self.startupinfo,
                    env=self.proc_env,
                    cwd=current_directory,
                    preexec_fn=self.preexec_fn,
                    shell=False,
                )
            else:
                pass
            try:
                print(f"current_filename: {current_filename}")
                (stdout, stderr) = self.gofmt_proc.communicate(
                    input=bytes(current_filename, encoding=self.encoding),
                )
                formatted_text = stderr.decode(self.encoding)
                content = formatted_text
                row = 0
                col = 0
                current_view.show_popup(
                    content,
                    0x0,
                    0,
                    640,
                    200,
                )
            finally:
                try:
                    self.gofmt_proc.kill()
                except:
                    pass
        except Exception as err:
            print(err)
            sublime.status_message(str(err))
        print("go_vet: Done!")
        return None


class GoFmtVet(sublime_plugin.ViewEventListener):
    def on_pre_save(self,):
        pass
        # current_view = self.view
        # valid_ext = extension_is_valid(current_view)
        # if valid_ext:
        #     current_view.run_command("go_fmt")
        #     current_view.run_command("go_vet")

    def on_pre_save_async(self,):
        pass

    def on_text_command(self, command_name, args):
        pass
