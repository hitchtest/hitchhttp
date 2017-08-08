from subprocess import call
from os import path
from commandlib import run
import hitchpython
import hitchserve
from hitchstory import StoryCollection, StorySchema, BaseEngine, exceptions, validate
from hitchrun import expected
from commandlib import Command
import strictyaml
from strictyaml import MapPattern, Str, Map, Int, Optional, load, Enum
from pathquery import pathq
import hitchtest
import hitchdoc
from commandlib import python
from hitchrun import DIR
from hitchrun.decorators import ignore_ctrlc
import requests


from jinja2.environment import Environment
from jinja2 import DictLoader


class Engine(BaseEngine):
    """Python engine for running tests."""
    schema = StorySchema(
        preconditions=Map({
            "example.yaml": Str(),
            "code": Str(),
            "analysis_code": Str(),
        }),
        params=Map({
            "python version": Str(),
        }),
        about={
            "description": Str(),
            Optional("importance"): Int(),
        },
    )

    def __init__(self, keypath, settings):
        self.path = keypath
        self.settings = settings

    def set_up(self):
        """Set up your applications and the test environment."""
        self.path.state = self.path.gen.joinpath("state")
        
        if self.path.state.exists():
            self.path.state.rmtree()
        self.path.state.mkdir()

        self.python_package = hitchpython.PythonPackage(
            self.preconditions.get('python_version', '3.5.0')
        )
        self.python_package.build()

        self.pip = self.python_package.cmd.pip
        self.python = self.python_package.cmd.python

        # Install debugging packages
        with hitchtest.monitor([self.path.key.joinpath("debugrequirements.txt")]) as changed:
            if changed:
                run(self.pip("install", "-r", "debugrequirements.txt").in_dir(self.path.key))

        # Uninstall and reinstall
        with hitchtest.monitor(pathq(self.path.project.joinpath("hitchhttp")).ext("py")) as changed:
            if changed:
                run(self.pip("uninstall", "hitchhttp", "-y").ignore_errors())
                run(self.pip("install", ".").in_dir(self.path.project))
        
        self.path.state.joinpath("example.yaml").write_text(self.preconditions['example.yaml'])
        self.path.state.joinpath("myserver.py").write_text(self.preconditions['code'])
        
        self.services = hitchserve.ServiceBundle(
            str(self.path.project),
            startup_timeout=2.0,
            shutdown_timeout=2.0,
        )

    
    def server_starts(self, message=""):
        self.services['Server'] = hitchserve.Service(
            command=self.python(self.path.state.joinpath("myserver.py")).in_dir(self.path.state),
            log_line_ready_checker=lambda line: message in line,
        )
        self.services.startup(interactive=False)
    
    @validate(
        request=Map({
            "method": Enum(["GET", "POST"]),
            "url": Str(),
        }),
        expected_response=Map({
            "code": Int(),
            "content": Str(),
        })
    )
    def request(self, request, expected_response=None):
        import requests
        response = requests.request(
            request['method'].lower(),
            request['url'],
            #data=data,
            #headers=headers,
            #timeout=timeout
        )

        if expected_response is not None:
            assert expected_response['code'] == response.status_code
            try:
                assert expected_response['content'] == response.content.decode('utf8')
            except AssertionError:
                raise AssertionError("{0} expected, saw {1}".format(expected_response['content'], response.content.decode('utf8')))

        
    
    def server_stopped_normally(self):
        if self.services is not None:
            self.services.shutdown()

    def run_command(self, command):
        self.ipython_step_library.run(command)
        self.doc.step("code", command=command)

    def code(self, command):
        self.ipython_step_library.run(command)
        self.doc.step("code", command=command)

    #@validate(exception=Str())
    #def raises_exception(self, command, exception, why=''):
        #"""
        #Command raises exception.
        #"""
        #import re
        #self.error = self.ipython_step_library.run(
            #command, swallow_exception=True
        #).error
        #if self.error is None:
            #raise Exception("Expected exception, but got none")
        #full_exception = re.compile("(?:\\x1bs?\[0m)+(?:\n+)+{0}".format(
            #re.escape("\x1b[0;31m"))
        #).split(self.error)[-1]
        #exception_class_name, exception_text = full_exception.split("\x1b[0m: ")
        #if self.settings.get("overwrite"):
            #self.current_step.update(exception=str(exception_text))
        #else:
            #assert exception.strip() in exception_text, "UNEXPECTED:\n{0}".format(exception_text)
        #self.doc.step(
            #"exception",
            #command=command,
            #exception_class_name=exception_class_name,
            #exception=exception_text,
            #why=why,
        #)
    
    def raises_exception(self, exception):
        """
        Expect an exception.
        """
        class ExpectedExceptionDidNotHappen(Exception):
            pass

        error_path = self.path.state.joinpath("error.txt")
        runpy = self.path.state.joinpath("runmypy.py")
        if error_path.exists():
            error_path.remove()
        env = Environment()
        env.loader = DictLoader(load(self.path.key.joinpath("codetemplates.yml").bytes().decode('utf8')).data)
        runpy.write_text(env.get_template("raises_exception").render(
            setup=self.preconditions['setup'],
            code=self.preconditions['code'],
            variables=self.preconditions.get('variables', None),
            yaml_snippet=self.preconditions.get("yaml_snippet"),
            modified_yaml_snippet=self.preconditions.get("modified_yaml_snippet"),
            exception=exception,
            error_path=error_path,
        ))
        self.python(runpy).run()
        if not error_path.exists():
            raise ExpectedExceptionDidNotHappen()
        else:
            assert exception.strip() in error_path.bytes().decode('utf8'), "expected:\n{0}\nshould be:\n{1}".format(
                exception,
                error_path.bytes().decode('utf8'),
            )
        

    def should_be_equal_to(self, rhs):
        """
        Code should be equal to rhs
        """
        class UnexpectedException(Exception):
            pass

        error_path = self.path.state.joinpath("error.txt")
        runpy = self.path.state.joinpath("runmypy.py")
        if error_path.exists():
            error_path.remove()
        env = Environment()
        env.loader = DictLoader(load(self.path.key.joinpath("codetemplates.yml").bytes().decode('utf8')).data)
        runpy.write_text(env.get_template("shouldbeequal").render(
            setup=self.preconditions['setup'],
            code=self.preconditions['code'],
            variables=self.preconditions.get('variables', None),
            yaml_snippet=self.preconditions.get("yaml_snippet"),
            modified_yaml_snippet=self.preconditions.get("modified_yaml_snippet"),
            rhs=rhs,
            error_path=error_path,
        ))
        self.python(runpy).run()
        if error_path.exists():
            raise UnexpectedException(error_path.bytes().decode("utf8"))

    def run_analysis_code(self):
        self.path.state.joinpath("analysis.py").write_text(self.preconditions['analysis_code'])
        self.python(self.path.state.joinpath("analysis.py")).run()


    def returns_true(self, command, why=''):
        self.ipython_step_library.assert_true(command)
        self.doc.step("true", command=command, why=why)

    def should_be_equal(self, lhs='', rhs='', why=''):
        command = """({0}).should.be.equal({1})""".format(lhs, rhs)
        self.ipython_step_library.run(command)
        self.doc.step("true", command=command, why=why)
    
    

    def assert_true(self, command):
        self.ipython_step_library.assert_true(command)
        self.doc.step("true", command=command)

    def assert_exception(self, command, exception):
        error = self.ipython_step_library.run(
            command, swallow_exception=True
        ).error
        assert exception.strip() in error
        self.doc.step("exception", command=command, exception=exception)

    def on_failure(self, result):
        if self.settings.get("pause_on_failure", True):
            if self.preconditions.get("launch_shell", False):
                self.services.log(message=self.stacktrace.to_template())
                self.shell()

    def shell(self):
        if hasattr(self, 'services'):
            self.services.start_interactive_mode()
            import sys
            import time
            time.sleep(0.5)
            if path.exists(path.join(
                path.expanduser("~"), ".ipython/profile_default/security/",
                self.ipython_kernel_filename)
            ):
                call([
                        sys.executable, "-m", "IPython", "console",
                        "--existing", "--no-confirm-exit",
                        path.join(
                            path.expanduser("~"),
                            ".ipython/profile_default/security/",
                            self.ipython_kernel_filename
                        )
                    ])
            else:
                call([
                    sys.executable, "-m", "IPython", "console",
                    "--existing", self.ipython_kernel_filename
                ])
            self.services.stop_interactive_mode()

    def assert_file_contains(self, filename, contents):
        assert self.path.state.joinpath(filename).bytes().decode('utf8').strip() == contents.strip()
        self.doc.step("filename contains", filename=filename, contents=contents)

    def pause(self, message="Pause"):
        if hasattr(self, 'services'):
            self.services.start_interactive_mode()
        import IPython
        IPython.embed()
        if hasattr(self, 'services'):
            self.services.stop_interactive_mode()

    def on_success(self):
        if self.settings.get("overwrite"):
            self.new_story.save()

    def tear_down(self):
        try:
            self.shutdown_connection()
        except:
            pass
        if hasattr(self, 'services'):
            self.services.shutdown()


@expected(strictyaml.exceptions.YAMLValidationError)
@expected(exceptions.HitchStoryException)
def tdd(*words):
    """
    Run test with words.
    """
    print(
        StoryCollection(
            pathq(DIR.key.joinpath("story")).ext("story"), Engine(DIR, {})
        ).shortcut(*words).play().report()
    )


def regression():
    """
    Run regression testing - lint and then run all tests.
    """
    lint()
    print(
        StoryCollection(
            pathq(DIR.key.joinpath("story")).ext("story"), Engine(DIR, {})
        ).ordered_by_name().play().report()
    )


def lint():
    """
    Lint all code.
    """
    python("-m", "flake8")(
        DIR.project.joinpath("strictyaml"),
        "--max-line-length=100",
        "--exclude=__init__.py",
    ).run()
    python("-m", "flake8")(
        DIR.key.joinpath("key.py"),
        "--max-line-length=100",
        "--exclude=__init__.py",
    ).run()
    print("Lint success!")


def hitch(*args):
    """
    Use 'h hitch --help' to get help on these commands.
    """
    hitch_maintenance(*args)


def deploy(version):
    """
    Deploy to pypi as specified version.
    """
    NAME = "strictyaml"
    git = Command("git").in_dir(DIR.project)
    version_file = DIR.project.joinpath("VERSION")
    old_version = version_file.bytes().decode('utf8')
    if version_file.bytes().decode("utf8") != version:
        DIR.project.joinpath("VERSION").write_text(version)
        git("add", "VERSION").run()
        git("commit", "-m", "RELEASE: Version {0} -> {1}".format(
            old_version,
            version
        )).run()
        git("push").run()
        git("tag", "-a", version, "-m", "Version {0}".format(version)).run()
        git("push", "origin", version).run()
    else:
        git("push").run()

    # Set __version__ variable in __init__.py, build sdist and put it back
    initpy = DIR.project.joinpath(NAME, "__init__.py")
    original_initpy_contents = initpy.bytes().decode('utf8')
    initpy.write_text(
        original_initpy_contents.replace("DEVELOPMENT_VERSION", version)
    )
    python("setup.py", "sdist").in_dir(DIR.project).run()
    initpy.write_text(original_initpy_contents)

    # Upload to pypi
    python(
        "-m", "twine", "upload", "dist/{0}-{1}.tar.gz".format(NAME, version)
    ).in_dir(DIR.project).run()


def docgen():
    """
    Generate documentation.
    """
    docpath = DIR.project.joinpath("docs")

    if not docpath.exists():
        docpath.mkdir()

    documentation = hitchdoc.Documentation(
        DIR.gen.joinpath('storydb.sqlite'),
        'doctemplates.yml'
    )

    for story in documentation.stories:
        story.write(
            "rst",
            docpath.joinpath("{0}.rst".format(story.slug))
        )

@ignore_ctrlc
def ipy():
    """
    Run IPython in environment."
    """
    Command(DIR.gen.joinpath("py3.5.0", "bin", "ipython")).run()


def rot():
    """
    Test for code rot by upgrading dependency and running tests (ruamel.yaml).
    """
    print("Checking code rot for strictyaml project...")
    latest_version = requests.get(
        "https://pypi.python.org/pypi/ruamel.yaml/json"
    ).json()['info']['version']
    base_story = load(DIR.key.joinpath("strictyaml.story").bytes().decode("utf8"))
    latest_tested_version = str(base_story['strictyaml']['params']['ruamel version'])

    if latest_version != latest_tested_version:
        base_story['strictyaml']['params']['ruamel version'] = load(latest_version)
        DIR.key.joinpath("strictyaml.story").write_text(base_story.as_yaml())
        regression()
    else:
        print("No dependency changes")
