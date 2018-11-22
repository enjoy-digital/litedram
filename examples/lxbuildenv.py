#!/usr/bin/env python3

# This script enables easy, cross-platform building without the need
# to install third-party Python modules.

import sys
import os
import subprocess
import argparse


DEPS_DIR = "deps"

# Obtain the path to this script, plus a trailing separator.  This will
# be used later on to construct various environment variables for paths
# to a variety of support directories.
script_path = os.path.dirname(os.path.realpath(__file__)) + os.path.sep

# Look through the specified file for known variables to get the dependency list
def get_required_dependencies(filename):
    import ast

    # Always check the Python version
    dependencies = {
        'python': 1
    }
    main_src = ""

    try:
        with open(sys.argv[0], 'r') as f:
            main_src = f.read()
        main_ast = ast.parse(main_src, filename=filename)
    except:
        return list(dependencies.keys())

    # Iterate through the top-level nodes looking for variables named
    # LX_DEPENDENCIES or LX_DEPENDENCY and get the values that are
    # assigned to them.
    for node in ast.iter_child_nodes(main_ast):
        if isinstance(node, ast.Assign):
            value = node.value
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id == "LX_DEPENDENCIES" or target.id == "LX_DEPENDENCY":
                        if isinstance(value, (ast.List, ast.Tuple)):
                            for elt in value.elts:
                                if isinstance(elt, ast.Str):
                                    dependencies[elt.s] = 1
                        elif isinstance(value, ast.Str):
                            dependencies[value.s] = 1

    # Set up sub-dependencies
    if 'riscv' in dependencies:
        dependencies['make'] = 1
    return list(dependencies.keys())

def get_python_path(script_path, args):
    # Python has no concept of a local dependency path, such as the C `-I``
    # switch, or the nodejs `node_modules` path, or the rust cargo registry.
    # Instead, it relies on an environment variable to append to the search
    # path.
    # Construct this variable by adding each subdirectory under the `deps/`
    # directory to the PYTHONPATH environment variable.
    python_path = []
    if os.path.isdir(script_path + DEPS_DIR):
        for dep in os.listdir(script_path + DEPS_DIR):
            dep = script_path + DEPS_DIR + os.path.sep + dep
            if os.path.isdir(dep):
                python_path.append(dep)
    return python_path

def fixup_env(script_path, args):
    os.environ["PYTHONPATH"] = os.pathsep.join(get_python_path(script_path, 0))

    # Set the "LXBUILDENV_REEXEC" variable to prevent the script from continuously
    # reinvoking itself.
    os.environ["LXBUILDENV_REEXEC"] = "1"

    # Python randomizes the order in which it traverses hashes, and Migen uses
    # hashes an awful lot when bringing together modules.  As such, the order
    # in which Migen generates its output Verilog will change with every run,
    # and the addresses for various modules will change.
    # Make builds deterministic so that the generated Verilog code won't change
    # across runs.
    os.environ["PYTHONHASHSEED"] = "1"

    # Some Makefiles are invoked as part of the build process, and those Makefiles
    # occasionally have calls to Python.  Ensure those Makefiles use the same
    # interpreter that this script is using.
    os.environ["PYTHON"] = sys.executable

    # Set the environment variable "V" to 1.  This causes Makefiles to print
    # the commands they run, which makes them easier to debug.
    if args.lx_verbose:
        os.environ["V"] = "1"

    # If the user just wanted to print the environment variables, do that and quit.
    if args.lx_print_env:
        print("PYTHONPATH={}".format(os.environ["PYTHONPATH"]))
        print("PYTHONHASHSEED={}".format(os.environ["PYTHONHASHSEED"]))
        print("PYTHON={}".format(sys.executable))
        print("LXBUILDENV_REEXEC={}".format(os.environ["LXBUILDENV_REEXEC"]))

        sys.exit(0)

# Equivalent to the powershell Get-Command, and kinda like `which`
def get_command(cmd):
    if os.name == 'nt':
        path_ext = os.environ["PATHEXT"].split(os.pathsep)
    else:
        path_ext = [""]
    for ext in path_ext:
        for path in os.environ["PATH"].split(os.pathsep):

            if os.path.exists(path + os.path.sep + cmd + ext):
                return path + os.path.sep + cmd + ext
    return None

def check_python_version(args):
    import platform
    # Litex / Migen require Python 3.5 or newer.  Ensure we're running
    # under a compatible version of Python.
    if sys.version_info[:3] < (3, 5):
        return (False,
            "python: You need Python 3.5+ (version {} found)".format(sys.version_info[:3]))
    return (True, "python 3.5+: ok (Python {} found)".format(platform.python_version()))

def check_vivado(args):
    vivado_path = get_command("vivado")
    if vivado_path == None:
        # Look for the default Vivado install directory
        if os.name == 'nt':
            base_dir = r"C:\Xilinx\Vivado"
        else:
            base_dir = "/opt/Xilinx/Vivado"
        if os.path.exists(base_dir):
            for file in os.listdir(base_dir):
                bin_dir = base_dir + os.path.sep + file + os.path.sep + "bin"
                if os.path.exists(bin_dir + os.path.sep + "vivado"):
                    os.environ["PATH"] += os.pathsep + bin_dir
                    vivado_path = bin_dir
                    break
    if vivado_path == None:
        return (False, "toolchain not found in your PATH", "download it from https://www.xilinx.com/support/download.html")
    return (True, "found at {}".format(vivado_path))

def check_cmd(args, cmd, name=None, fix=None):
    if name is None:
        name = cmd
    path = get_command(cmd)
    if path == None:
        return (False, name + " not found in your PATH", fix)
    return (True, "found at {}".format(path))

def check_make(args):
    return check_cmd(args, "make", "GNU Make")

def check_riscv(args):
    return check_cmd(args, "riscv64-unknown-elf-gcc", "riscv toolchain", "download it from https://www.sifive.com/products/tools/")

def check_yosys(args):
    return check_cmd(args, "yosys")

def check_arachne(args):
    return check_cmd(args, "arachne-pnr")

dependency_checkers = {
    'python': check_python_version,
    'vivado': check_vivado,
    'make': check_make,
    'riscv': check_riscv,
    'yosys': check_yosys,
    'arachne-pnr': check_arachne,
}

# Validate that the required dependencies (Vivado, compilers, etc.)
# have been installed.
def check_dependencies(args, dependency_list):

    dependency_errors = 0
    for dependency_name in dependency_list:
        if not dependency_name in dependency_checkers:
            print('WARNING: Unrecognized dependency "{}"'.format(dependency_name))
            continue
        result = dependency_checkers[dependency_name](args)
        if result[0] == False:
            if len(result) > 2:
                print('{}: {} -- {}'.format(dependency_name, result[1], result[2]))
            else:
                print('{}: {}'.format(dependency_name, result[1]))
            dependency_errors = dependency_errors + 1

        elif args.lx_check_deps or args.lx_verbose:
            print('dependency: {}: {}'.format(dependency_name, result[1]))
    if dependency_errors > 0:
        if args.lx_ignore_deps:
            print('{} missing dependencies were found but continuing anyway'.format(dependency_errors))
        else:
            raise SystemExit(str(dependency_errors) +
                             " missing dependencies were found")

    if args.lx_check_deps:
        sys.exit(0)

# Return True if the given tree needs to be initialized
def check_module_recursive(root_path, depth, verbose=False):
    if verbose:
        print('git-dep: checking if "{}" requires updating...'.format(root_path))
    # If the directory isn't a valid git repo, initialization is required
    if not os.path.exists(root_path + os.path.sep + '.git'):
        return True

    # If there are no submodules, no initialization needs to be done
    if not os.path.isfile(root_path + os.path.sep + '.gitmodules'):
        return False

    # Loop through the gitmodules to check all submodules
    gitmodules = open(root_path + os.path.sep + '.gitmodules', 'r')
    for line in gitmodules:
        parts = line.split("=", 2)
        if parts[0].strip() == "path":
            path = parts[1].strip()
            if check_module_recursive(root_path + os.path.sep + path, depth + 1, verbose=verbose):
                return True
    return False

# Determine whether we need to invoke "git submodules init --recurse"
def check_submodules(script_path, args):
    if check_module_recursive(script_path, 0, verbose=args.lx_verbose):
        print("Missing submodules -- updating")
        subprocess.Popen(["git", "submodule", "update",
                          "--init", "--recursive"], cwd=script_path).wait()
    elif args.lx_verbose:
        print("Submodule check: Submodules found")


def main(args):
    if args.init:
        main_name = os.getcwd().split(os.path.sep)[-1] + '.py'
        new_main_name = input('What would you like your main program to be called? [' + main_name + '] ')
        if new_main_name is not None and new_main_name != "":
            main_name = new_main_name

        print("Initializing git repository")
        if not os.path.exists(DEPS_DIR):
            os.mkdir(DEPS_DIR)

        os.system("git init")
        os.system("git add " + str(__file__))

        os.system("git submodule add https://github.com/m-labs/migen.git deps/migen")
        os.system("git add deps/migen")

        os.system("git submodule add https://github.com/enjoy-digital/litex.git deps/litex")
        os.system("git add deps/litex")

        os.system("git submodule add https://github.com/enjoy-digital/litescope deps/litescope")
        os.system("git add deps/litescope")

        os.system("git submodule add https://github.com/pyserial/pyserial.git deps/pyserial")
        os.system("git add deps/pyserial")

        os.system("git submodule update --init --recursive")

        bin_tools = {
            'litex_server': 'litex.soc.tools.remote.litex_server',
            'litex_term': 'litex.soc.tools.litex_term',
            'mkmscimg': 'litex.soc.tools.mkmscimg',
        }
        bin_template = """
#!/usr/bin/env python3

import sys
import os

# This script lives in the "bin" directory, but uses a helper script in the parent
# directory.  Obtain the current path so we can get the absolute parent path.
script_path = os.path.dirname(os.path.realpath(
    __file__)) + os.path.sep + os.path.pardir + os.path.sep
sys.path.insert(0, script_path)it
import lxbuildenv

from litex.soc.tools.mkmscimg import main
main()"""
        # Create binary programs under bin/
        if not os.path.exists("bin"):
            print("Creating binaries")
            os.mkdir("bin")
            for bin_name, python_module in bin_tools.items():
                with open('bin' + os.path.sep + bin_name, 'w') as new_bin:
                    new_bin.write(bin_template)
                    new_bin.write('from ' + python_module + ' import main\n')
                    new_bin.write('main()\n')
                os.system('git add --chmod=+x bin' + os.path.sep + bin_name)

        with open(main_name, 'w') as m:
            program_template = """#!/usr/bin/env python3
# This variable defines all the external programs that this module
# relies on.  lxbuildenv reads this variable in order to ensure
# the build will finish without exiting due to missing third-party
# programs.
LX_DEPENDENCIES = ["riscv", "vivado"]

# Import lxbuildenv to integrate the deps/ directory
import lxbuildenv

from migen import *
from litex.build.generic_platform import *

_io = [
    ("clk50", 0, Pins("J19"), IOStandard("LVCMOS33")),
]

class Platform(XilinxPlatform):
    def __init__(self, toolchain="vivado", programmer="vivado", part="35"):
        part = "xc7a" + part + "t-fgg484-2"
    def create_programmer(self):
        if self.programmer == "vivado":
            return VivadoProgrammer(flash_part="n25q128-3.3v-spi-x1_x2_x4")
        else:
            raise ValueError("{} programmer is not supported"
                             .format(self.programmer))

    def do_finalize(self, fragment):
        XilinxPlatform.do_finalize(self, fragment)

class BaseSoC(SoCSDRAM):
    csr_peripherals = [
        "ddrphy",
#        "dna",
        "xadc",
        "cpu_or_bridge",
    ]
    csr_map_update(SoCSDRAM.csr_map, csr_peripherals)

    def __init__(self, platform, **kwargs):
        clk_freq = int(100e6)

def main():
    platform = Platform()
    soc = BaseSoC(platform)
    builder = Builder(soc, output_dir="build", csr_csv="test/csr.csv")
    vns = builder.build()
    soc.do_exit(vns)

if __name__ == "__main__":
    main()
"""
            m.write(program_template)
        return

# For the main command, parse args and hand it off to main()
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Wrap Python code to enable quickstart",
        add_help=False)
    parser.add_argument(
        "-h", "--help", help="show this help message and exit", action="help"
    )
    parser.add_argument(
        '-i', '--init', help='initialize a new project', action="store_true"
    )
    args = parser.parse_args()

    main(args)

elif not os.path.isfile(sys.argv[0]):
    print("lxbuildenv doesn't operate while in interactive mode")

elif "LXBUILDENV_REEXEC" not in os.environ:
    parser = argparse.ArgumentParser(
        description="Wrap Python code to enable quickstart",
        add_help=False)
    parser.add_argument(
        "--lx-verbose", help="increase verboseness of some processes", action="store_true"
    )
    parser.add_argument(
        "--lx-print-env", help="print environment variable listing for pycharm, vscode, or bash", action="store_true"
    )
    parser.add_argument(
        "--lx-check-deps", help="check build environment for dependencies such as compiler and fpga tools and then exit", action="store_true"
    )
    parser.add_argument(
        "--lx-all-deps", help="print all possible dependencies and then exit", action="store_true"
    )
    parser.add_argument(
        "--lx-help", action="help"
    )
    parser.add_argument(
        "--lx-ignore-deps", help="try building even if dependencies are missing", action="store_true"
    )
    (args, rest) = parser.parse_known_args()

    if args.lx_all_deps:
        print('Known dependencies:')
        for dep in dependency_checkers.keys():
            print('    {}'.format(dep))
        print('To define a dependency, add a variable inside {} at the top level called LX_DEPENDENCIES and assign it a list or tuple.'.format(sys.argv[0]))
        print('For example:')
        print('LX_DEPENDENCIES = ("riscv", "vivado")')
        sys.exit(0)

    deps = get_required_dependencies(sys.argv[0])

    fixup_env(script_path, args)
    check_dependencies(args, deps)
    check_submodules(script_path, args)

    try:
        sys.exit(subprocess.Popen(
            [sys.executable] + [sys.argv[0]] + rest).wait())
    except:
        sys.exit(1)
else:
    # Overwrite the deps directory.
    # Because we're running with a predefined PYTHONPATH, you'd think that
    # the DEPS_DIR would be first.
    # Unfortunately, setuptools causes the sitewide packages to take precedence
    # over the PYTHONPATH variable.
    # Work around this bug by inserting paths into the first index.
    for path in get_python_path(script_path, None):
        sys.path.insert(0, path)
