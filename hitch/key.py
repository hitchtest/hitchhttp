from hitchstory import StoryCollection, BaseEngine, validate
from hitchrun import Path, hitch_maintenance
from pathquery import pathq
import hitchpython
import hitchserve
import hitchtrigger
from strictyaml import Int
import sys
from pexpect import EOF


KEYPATH = Path(__file__).abspath().dirname()


class Paths(object):
    def __init__(self, keypath):
        self.keypath = keypath
        self.project = keypath.parent
        self.state = keypath.parent.joinpath('state')
        self.genpath = Path(sys.executable).abspath().dirname().parent.parent


class Engine(BaseEngine):
    def __init__(self, keypath):
        self.path = Paths(keypath)

    def set_up(self):
        self.path.project = self.path.keypath.parent
        self.path.state = self.path.keypath.parent.joinpath("state")
        self.monitor = hitchtrigger.Monitor(self.path.genpath.joinpath("projectmonitor.db"))

        self.python_package = hitchpython.PythonPackage(
            python_version=self.preconditions.get('python_version', '3.5.0')
        )
        self.python_package.build()

        self.pip = self.python_package.cmd.pip.in_dir(self.path.keypath)
        self.python = self.python_package.cmd.python.in_dir(self.path.keypath)

        # Install dev requiremnts
        with self.monitor.block(
            "dev_{}".format(self.preconditions.get('python_version', '3.5.0')),
            self.monitor.modified([self.path.keypath.joinpath("dev_requirements.txt")])
        ).context() as trigger:
            if trigger:
                self.pip("install", "-r", "dev_requirements.txt").run()

        self.pip("uninstall", "hitchhttp", "-y").ignore_errors().run()
        self.pip("install", ".").in_dir(self.path.project).run()

        self.services = hitchserve.ServiceBundle(
            str(self.path.project),
            startup_timeout=8.0,
            shutdown_timeout=1.0
        )

        self.services['IPython'] = hitchpython.IPythonKernelService(self.python_package)

        self.services.startup(interactive=False)
        self.ipython_kernel_filename = self.services['IPython'].wait_and_get_ipykernel_filename()
        self.ipython_step_library = hitchpython.IPythonStepLibrary()
        self.ipython_step_library.startup_connection(self.ipython_kernel_filename)
        self.shutdown_connection = self.ipython_step_library.shutdown_connection


    def run_command(self, command):
        self.ipython_step_library.run(command)


    def tear_down(self):
        try:
            self.shutdown_connection()
        except:
            pass
        if hasattr(self, 'services'):
            self.services.shutdown()



STORY_COLLECTION = StoryCollection(pathq(KEYPATH).ext("story"), Engine(KEYPATH))


def test(*words):
    """
    Run test with words.
    """
    print(STORY_COLLECTION.shortcut(*words).play().report())


def ci():
    """
    Run all stories.
    """
    lint()
    print(STORY_COLLECTION.ordered_by_name().play().report())


def hitch(*args):
    """
    Hitch maintenance commands.
    """
    hitch_maintenance(*args)


def lint():
    """
    Lint all code.
    """
    print("placeholder")


def clean():
    print("destroy all created vms")
