# @file RustEnvironmentCheck.py
# Plugin to confirm Rust tools are present needed to compile Rust code during
# firmare build.
#
# This provides faster, direct feedback to a developer about the changes they
# may need to make to successfully build Rust code. Otherwise, the build will
# fail much later during firmware code compilation when Rust tools are invoked
# with messages that are ambiguous or difficult to find.
#
# Note:
#   - The entire plugin is enabled/disabled by scope.
#   - Individual tools can be opted out by setting the environment variable
#     `RUST_ENV_CHECK_TOOL_EXCLUSIONS` with a comma separated list of the tools
#     to exclude. For example, "rustup, cargo tarpaulin" would not require that
#     those tools be installed.
#
# Copyright (c) Microsoft Corporation.
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
import logging
import re
from collections import namedtuple
from edk2toolext.environment import shell_environment
from edk2toolext.environment.plugintypes.uefi_build_plugin import IUefiBuildPlugin
from edk2toolext.environment.uefi_build import UefiBuilder
from edk2toollib.utility_functions import RunCmd
from io import StringIO

WORKSPACE_TOOLCHAIN_FILE = "rust-toolchain.toml"

RustToolInfo = namedtuple("RustToolInfo", ["presence_cmd", "install_help"])
RustToolChainInfo = namedtuple("RustToolChainInfo", ["error", "toolchain"])


class RustEnvironmentCheck(IUefiBuildPlugin):
    """Checks that the system environment is ready to build Rust code."""

    def do_pre_build(self, _: UefiBuilder) -> int:
        """Rust environment checks during pre-build.

        Args:
            builder (UefiBuilder): A UEFI builder object for this build.

        Returns:
            int: The number of environment issues found. Zero indicates no
            action is needed.
        """
        def verify_cmd(name: str, params: str = "--version") -> bool:
            """Indicates if a command can successfully be executed.

            Args:
                name (str): Tool name.
                params (str, optional): Tool params. Defaults to "--version".

            Returns:
                bool: True on success. False on failure to run the command.
            """
            cmd_output = StringIO()
            ret = RunCmd(name, params, outstream=cmd_output,
                         logging_level=logging.DEBUG)
            return ret == 0

        def get_workspace_toolchain_version() -> RustToolChainInfo:
            """Returns the rust toolchain version specified in the workspace
            toolchain file.

            Returns:
                RustToolChainInfo: The rust toolchain information. If an error
                occurs, the error field will be True with no toolchain info.
            """
            toolchain_version = None
            try:
                with open(WORKSPACE_TOOLCHAIN_FILE, 'r') as toml_file:
                    content = toml_file.read()
                    match = re.search(r'channel\s*=\s*"([^"]+)"', content)
                    if match:
                        toolchain_version = match.group(1)
                return RustToolChainInfo(error=False, toolchain=toolchain_version)
            except FileNotFoundError:
                # If a file is not found. Do not check any further.
                return RustToolChainInfo(error=True, toolchain=None)

        def verify_workspace_rust_toolchain_is_installed() -> RustToolChainInfo:
            """Verifies the rust toolchain used in the workspace is available.

            Note: This function does not use the toml library to parse the toml
            file since the file is very simple and its not desirable to add the
            toml module as a dependency.

            Returns:
                RustToolChainInfo: A tuple that indicates if the toolchain is
                available and any the toolchain version if found.
            """
            toolchain_version = get_workspace_toolchain_version()
            if toolchain_version.error or not toolchain_version:
                # If the file is not in an expected format, let that be handled
                # elsewhere and do not look further.
                return RustToolChainInfo(error=False, toolchain=None)

            toolchain_version = toolchain_version.toolchain

            installed_toolchains = StringIO()
            ret = RunCmd("rustup", "toolchain list",
                         outstream=installed_toolchains,
                         logging_level=logging.DEBUG)

            # The ability to call "rustup" is checked separately. Here do not
            # continue if the command is not successful.
            if ret != 0:
                return RustToolChainInfo(error=False, toolchain=None)

            installed_toolchains = installed_toolchains.getvalue().splitlines()
            return RustToolChainInfo(
                error=not any(toolchain_version in toolchain
                              for toolchain in installed_toolchains),
                toolchain=toolchain_version)

        def verify_rust_src_component_is_installed() -> bool:
            """Verifies the rust-src component is installed.

            Returns:
                bool: True if the rust-src component is installed for the default
                toolchain or the status could not be determined, otherwise, False.
            """
            toolchain_version = get_workspace_toolchain_version()
            if toolchain_version.error or not toolchain_version:
                # If the file is not in an expected format, let that be handled
                # elsewhere and do not look further.
                return True

            toolchain_version = toolchain_version.toolchain

            rustup_output = StringIO()
            ret = RunCmd("rustc", "--version --verbose",
                         outstream=rustup_output,
                         logging_level=logging.DEBUG)
            if ret != 0:
                # rustc installation is checked elsewhere. Exit here on failure.
                return True

            for line in rustup_output.getvalue().splitlines():
                start_index = line.lower().strip().find("host: ")
                if start_index != -1:
                    target_triple = line[start_index + len("host: "):]
                    break
            else:
                logging.error("Failed to get host target triple information.")
                return False

            rustup_output = StringIO()
            ret = RunCmd("rustup", f"component list --toolchain {toolchain_version}",
                         outstream=rustup_output,
                         logging_level=logging.DEBUG)
            if ret != 0:
                # rustup installation and the toolchain are checked elsewhere.
                # Exit here on failure.
                return True

            for component in rustup_output.getvalue().splitlines():
                if "rust-src (installed)" in component:
                    return True

            logging.error("The Rust toolchain is installed but the rust-src component "
                          "needs to be installed:\n\n"
                          f"  rustup component add --toolchain {toolchain_version}-"
                          f"{target_triple} rust-src")

            return False

        generic_rust_install_instructions = \
            "Visit https://rustup.rs/ to install Rust and cargo."

        tools = {
            "rustup": RustToolInfo(
                presence_cmd=("rustup",),
                install_help=generic_rust_install_instructions
                ),
            "rustc": RustToolInfo(
                presence_cmd=("rustc",),
                install_help=generic_rust_install_instructions
                ),
            "cargo": RustToolInfo(
                presence_cmd=("cargo",),
                install_help=generic_rust_install_instructions
                ),
            "cargo build": RustToolInfo(
                presence_cmd=("cargo", "build --help"),
                install_help=generic_rust_install_instructions
                ),
            "cargo check": RustToolInfo(
                presence_cmd=("cargo", "check --help"),
                install_help=generic_rust_install_instructions
                ),
            "cargo fmt": RustToolInfo(
                presence_cmd=("cargo", "fmt --help"),
                install_help=generic_rust_install_instructions
                ),
            "cargo test": RustToolInfo(
                presence_cmd=("cargo", "test --help"),
                install_help=generic_rust_install_instructions
                ),
            "cargo make": RustToolInfo(
                presence_cmd=("cargo", "make --version"),
                install_help="Read installation instructions at "
                "https://github.com/sagiegurari/cargo-make#installation "
                "to install Cargo make."
                ),
            "cargo tarpaulin": RustToolInfo(
                presence_cmd=("cargo", "tarpaulin --version"),
                install_help="View the installation instructions at "
                "https://crates.io/crates/cargo-tarpaulin to install Cargo "
                "tarpaulin. A tool used for Rust code coverage."
                ),
        }

        excluded_tools_in_shell = shell_environment.GetEnvironment().get_shell_var(
            "RUST_ENV_CHECK_TOOL_EXCLUSIONS")
        excluded_tools = ([t.strip() for t in
                           excluded_tools_in_shell.split(",")] if
                          excluded_tools_in_shell else [])

        errors = 0
        for tool_name, tool_info in tools.items():
            if tool_name not in excluded_tools and not verify_cmd(*tool_info.presence_cmd):
                logging.error(
                    f"Rust Environment Failure: {tool_name} is not installed "
                    "or not on the system path.\n\n"
                    f"Instructions:\n{tool_info.install_help}\n\n"
                    f"Ensure \"{' '.join(tool_info.presence_cmd)}\" can "
                    "successfully be run from a terminal before trying again.")
                errors += 1

        rust_toolchain_info = verify_workspace_rust_toolchain_is_installed()
        if rust_toolchain_info.error:
            # The "rustc -Vv" command could be run in the script with the
            # output given to the user. This is approach is also meant to show
            # the user how to use the tools since getting the target triple is
            # important.
            logging.error(
                f"This workspace requires the {rust_toolchain_info.toolchain} "
                "toolchain.\n\n"
                "Run \"rustc -Vv\" and use the \"host\" value to install the "
                "toolchain needed:\n"
                f"  \"rustup toolchain install {rust_toolchain_info.toolchain}-"
                "<host>\"\n\n"
                "  \"rustup component add rust-src "
                f"{rust_toolchain_info.toolchain}-<host>\"")
            errors += 1

        if not verify_rust_src_component_is_installed():
            errors += 1

        return errors
