#!/usr/bin/env python3

# build_packages.py
#
# This script has the purpose of building Officeboy packages for multiple
# distribution formats using UV.
#
# Author: Yorga Babuscan (yorgabr@gmail.com)


"""Build packages for multiple distribution formats using UV."""

import argparse
import subprocess
import sys
from pathlib import Path


# Script version
__version__ = "1.0.0"


#__________ Color helpers _________________________________________________
class Colors:
    """ANSI color codes for terminal output."""
    
    CYAN = "\033[36m"
    YELLOW = "\033[33m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    RESET = "\033[0m"


def log_info(message: str) -> None:
    """Log informational message with timestamp."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    print(f"{timestamp}\t{Colors.CYAN}[INFO]{Colors.RESET}\t{message}")


def log_warn(message: str) -> None:
    """Log warning message with timestamp."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    print(f"{timestamp}\t{Colors.YELLOW}[WARN]{Colors.RESET}\t{message}")


def log_success(message: str) -> None:
    """Log success message with timestamp."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    print(f"{timestamp}\t{Colors.GREEN}[SUCCESS]{Colors.RESET}\t{message}")


def log_error(message: str) -> None:
    """Log error message with timestamp."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    print(f"{timestamp}\t{Colors.RED}[ERROR]{Colors.RESET}\t{message}", file=sys.stderr)


#__________ UV command execution __________________________________________
def run_uv_command(args: list[str], cwd: Path | None = None) -> bool:
    """Execute UV command and return success status.
    
    Args:
        args: List of arguments to pass to UV.
        cwd: Working directory for command execution.
        
    Returns:
        True if command succeeded, False otherwise.
    """
    cmd = ["uv"] + args
    
    log_info(f"Executing: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        log_error(f"Command failed: {e}")
        if e.stdout:
            log_error(f"stdout: {e.stdout}")
        if e.stderr:
            log_error(f"stderr: {e.stderr}")
        return False


#__________ Package builders ______________________________________________
def build_wheel(dist_dir: Path) -> bool:
    """Build wheel package using UV.
    
    Args:
        dist_dir: Directory for distribution artifacts.
        
    Returns:
        True if build succeeded, False otherwise.
    """
    log_info("Building wheel package with UV...")
    return run_uv_command(["build", "--wheel", "--out-dir", str(dist_dir)])


def build_sdist(dist_dir: Path) -> bool:
    """Build source distribution using UV.
    
    Args:
        dist_dir: Directory for distribution artifacts.
        
    Returns:
        True if build succeeded, False otherwise.
    """
    log_info("Building source distribution with UV...")
    return run_uv_command(["build", "--sdist", "--out-dir", str(dist_dir)])


def build_portable(dist_dir: Path) -> bool:
    """Build portable executable using PyInstaller.
    
    Args:
        dist_dir: Directory for distribution artifacts.
        
    Returns:
        True if build succeeded, False otherwise.
    """
    log_warn("Portable build requires PyInstaller.")
    log_info("To build portable: uv run pyinstaller officeboy-portable.spec")
    
    # Check if PyInstaller is available
    try:
        result = subprocess.run(
            ["uv", "run", "pyinstaller", "--version"],
            capture_output=True,
            check=True,
        )
        log_success("PyInstaller is available.")
        return True
    except subprocess.CalledProcessError:
        log_error("PyInstaller not available. Install with: uv add --dev pyinstaller")
        return False


#__________ Main execution ________________________________________________
def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Build Officeboy packages using UV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Author: Yorga Babuscan (yorgabr@gmail.com)
        """
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    parser.add_argument(
        "command",
        choices=["wheel", "sdist", "portable", "all"],
        default="all",
        nargs="?",
        help="Package format to build (default: all)"
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dist"),
        help="Output directory for packages (default: dist)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    args = parse_arguments()
    
    #__________ Setup __________
    dist_dir = args.output
    dist_dir.mkdir(parents=True, exist_ok=True)
    
    log_info(f"Build output directory: {dist_dir.resolve()}")
    
    #__________ Build execution __________
    builders = {
        "wheel": lambda: build_wheel(dist_dir),
        "sdist": lambda: build_sdist(dist_dir),
        "portable": lambda: build_portable(dist_dir),
    }
    
    if args.command == "all":
        to_build = ["wheel", "sdist"]
    else:
        to_build = [args.command]
    
    results = {}
    for fmt in to_build:
        if fmt in builders:
            results[fmt] = builders[fmt]()
        else:
            log_warn(f"Unknown format: {fmt}")
            results[fmt] = False
    
    #__________ Summary __________
    print()  # Blank line for readability
    log_info("=== Build Summary ===")
    
    all_success = True
    for fmt, success in results.items():
        status = f"{Colors.GREEN}SUCCESS{Colors.RESET}" if success else f"{Colors.RED}FAILED{Colors.RESET}"
        print(f"  {fmt:12} {status}")
        if not success:
            all_success = False
    
    #__________ Completion __________
    if all_success:
        log_success("All builds completed successfully.")
        return 0
    else:
        log_error("Some builds failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())