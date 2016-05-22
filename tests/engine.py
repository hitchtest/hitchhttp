from commandlib import run
import hitchpython
import hitchserve
import hitchtest
import hitchcli
import requests
import kaching
import time


class ExecutionEngine(hitchtest.ExecutionEngine):
    """Hitch bootstrap engine tester."""

    def set_up(self):
        self.path.project = self.path.engine.parent
        self.path.state = self.path.engine.parent.joinpath("state")
        self.path.samples = self.path.engine.joinpath("samples")

        if self.path.state.exists():
            self.path.state.rmtree()
        self.path.state.mkdir()

        if self.settings.get("kaching", False):
            kaching.start()

        self.python_package = hitchpython.PythonPackage(
            python_version=self.settings['python_version']
        )
        self.python_package.build()

        self.python = self.python_package.cmd.python
        self.pip = self.python_package.cmd.pip
        self.hitchhttpcmd = self.python("-u", "-m", "hitchhttp.commandline")

        self.cli_steps = hitchcli.CommandLineStepLibrary(
            default_timeout=int(self.settings.get("cli_timeout", 5))
        )

        self.cd = self.cli_steps.cd
        self.run = self.cli_steps.run
        self.expect = self.cli_steps.expect
        self.send_control = self.cli_steps.send_control
        self.send_line = self.cli_steps.send_line
        self.exit_with_any_code = self.cli_steps.exit_with_any_code
        self.exit = self.cli_steps.exit
        self.finish = self.cli_steps.finish

        #if "state" in self.preconditions:
            #self.path.state.rmtree(ignore_errors=True)
            #self.path.samples.joinpath(self.preconditions['state'])\
                             #.copytree(self.path.state)

        run(self.pip("uninstall", "hitchhttp", "-y").ignore_errors())
        run(self.pip("uninstall", "hitchtest", "-y").ignore_errors())
        run(self.pip("install", ".").in_dir(self.path.project.joinpath("..", "test")))
        run(self.pip("install", ".").in_dir(self.path.project))
        run(self.pip("install", "ipykernel"))
        run(self.pip("install", "pip"))
        run(self.pip("install", "q"))
        run(self.pip("install", "pudb"))

        for config_filename, config_filecontents in self.preconditions.get("config_files", {}).items():
            self.path.state.joinpath(config_filename).write_text(config_filecontents)


    def start_services(self, **services):
        """Start specified MockHTTP services."""
        self.services = hitchserve.ServiceBundle(
            self.path.project,
            startup_timeout=8.0,
            shutdown_timeout=1.0
        )

        for name, args in services.items():
            self.services[name] = hitchserve.Service(
                command=self.hitchhttpcmd(*args).in_dir(self.path.state),
                log_line_ready_checker=lambda line: "HitchHttp running" in line,
                directory=str(self.path.state),
            )

        self.services.startup(interactive=False)


    def lint(self, args=None):
        """Lint the source code."""
        run(self.pip("install", "flake8"))
        run(self.python_package.cmd.flake8(*args).in_dir(self.path.project))

    def assert_request_response_contains(self, url, contains, method="get", data=None, headers=None, timeout=3):
        response = getattr(requests, method)(
            url,
            data=data,
            headers=headers,
            timeout=timeout
        ).content.decode('utf8')
        try:
            assert contains in response
        except AssertionError:
            raise AssertionError("{0} not found in {1}".format(contains, response))

    def hitchhttp(self, args=None):
        """Run hitch in the state directory."""
        self.cd(self.path.state)
        if args is None:
            args = []
        self.run(self.hitchhttpcmd.arguments[0], self.hitchhttpcmd.arguments[1:] + args)

    def sleep(self, duration):
        """Sleep for specified duration."""
        time.sleep(int(duration))

    def pause(self, message=""):
        if hasattr(self, 'services') and self.services is not None:
            self.services.start_interactive_mode()
        self.ipython(message=message)
        if hasattr(self, 'services') and self.services is not None:
            self.services.stop_interactive_mode()

    def on_failure(self):
        """Stop and IPython."""
        if self.settings.get("kaching", False):
            kaching.fail()
        if self.settings.get("pause_on_failure", False):
            self.pause(message=self.stacktrace.to_template())

    def on_success(self):
        """Ka-ching!"""
        if self.settings.get("kaching", False):
            kaching.win()
        if self.settings.get("pause_on_success", False):
            self.pause(message="SUCCESS")

    def stop_services(self):
        if hasattr(self, 'services'):
            if self.services is not None:
                self.services.shutdown()

    def tear_down(self):
        """Clean out the state directory."""
        self.stop_services()