#!/usr/bin/env bash

# uv_setup.sh
#
# This script has the purpose of setting up the Officeboy development environment
# using UV (the ultra-fast Python package manager written in Rust).


# shellcheck shell=bash

# 'set -euo pipefail' is a robustness trio in Bash:
#  - 'set -e' : makes the script exit immediately if ANY command returns
#               a non-zero status (failure), except in certain contexts such as
#               inside 'if', 'while', and after '||'.
#  - 'set -u' : treats the use of UNDEFINED variables as an error, terminating the script.
#               This prevents silent bugs caused by mistyped variable names.
#  - 'set -o pipefail' : in pipelines (cmd1 | cmd2 | cmd3), the exit code
#               becomes that of the FIRST command that fails (not just the last one).
#               This ensures failures at the start of the pipeline are not swallowed.
# Together, these options make the script much safer against unexpected states.
set -euo pipefail

VERSION="1.0.0"

# Defaults
PYTHON_VERSION="3.11"
VERBOSE=0
DEBUG=0

# ANSI color codes
ESC=$'\033'
Cyan="${ESC}[36m"
Yellow="${ESC}[33m"
Green="${ESC}[32m"
Red="${ESC}[31m"
Reset="${ESC}[0m"

# ------------------------------
# Logging with timestamp and colors
# ------------------------------
timestamp() { date +%Y%m%d%H%M%S; }

log_error() { 
    printf "%s\t${Red}[ERROR]${Reset}\t%s\n" "$(timestamp)" "$*" >&2; 
}

log_warn() { 
    (( VERBOSE == 1 || DEBUG == 1 )) && \
    printf "%s\t${Yellow}[WARN]${Reset}\t%s\n" "$(timestamp)" "$*"; 
}

log_info() { 
    (( VERBOSE == 1 || DEBUG == 1 )) && \
    printf "%s\t${Cyan}[INFO]${Reset}\t%s\n" "$(timestamp)" "$*"; 
}

log_success() { 
    (( VERBOSE == 1 || DEBUG == 1 )) && \
    printf "%s\t${Green}[SUCCESS]${Reset}\t%s\n" "$(timestamp)" "$*"; 
}

log_debug() { 
    (( DEBUG == 1 )) && \
    printf "%s\t${Cyan}[DEBUG]${Reset}\t%s\n" "$(timestamp)" "$*"; 
}

script_name() { basename -- "$0"; }
print_version() { printf "%s version %s\n" "$(script_name)" "$VERSION"; }

# The help uses a single-quoted here-doc intentionally (no variable expansion).
# shellcheck disable=SC2016
print_usage() {
    cat <<'USAGE'
uv_setup.sh — Setup Officeboy development environment using UV.

Usage:
    uv_setup.sh [options]

Options:
    --python VERSION      Python version to use (default: 3.11).
    --verbose             Echo each precondition and important step.
    --debug               Print full commands before executing.
                          (DEBUG implies VERBOSE)
    --version             Show script semantic version and exit.
    -h, --help            Show this help and exit.

Author: Yorga Babuscan (yorgabr@gmail.com)
USAGE
}

# ------------------------------
# Argument parsing
# ------------------------------
parse_args() {
    while (("$#")); do
        case "$1" in
            -h|--help)            print_usage; exit 0 ;;
            --version)            print_version; exit 0 ;;
            --verbose)            VERBOSE=1; shift ;;
            --debug)              DEBUG=1; VERBOSE=1; shift ;;  # debug implies verbose
            --python)
                shift; [[ $# -gt 0 ]] || { log_error "--python requires a version."; exit 2; }
                PYTHON_VERSION="$1"; shift ;;
            --python=*)
                PYTHON_VERSION="${1#--python=}"; shift ;;
            *) log_error "Unknown option: $1"; print_usage; exit 2 ;;
        esac
    done
}

# ------------------------------
# UV installation check
# ------------------------------
ensure_uv_installed() {
    if ! command -v uv &> /dev/null; then
        log_warn "UV not found. Installing..."
        
        # Install UV via official installer
        if ! curl -LsSf https://astral.sh/uv/install.sh | sh; then
            log_error "Failed to install UV."
            exit 1
        fi
        
        # Add to PATH for current session
        export PATH="$HOME/.cargo/bin:$PATH"
        
        log_success "UV installed successfully."
    else
        log_info "UV is already installed."
    fi
    
    local uv_version
    uv_version="$(uv --version)"
    log_info "UV version: $uv_version"
}

# ------------------------------
# Environment setup
# ------------------------------
setup_environment() {
    log_info "Creating virtual environment with Python $PYTHON_VERSION..."
    
    if ! uv python install "$PYTHON_VERSION"; then
        log_error "Failed to install Python $PYTHON_VERSION."
        exit 1
    fi
    
    if ! uv venv --python "$PYTHON_VERSION"; then
        log_error "Failed to create virtual environment."
        exit 1
    fi
    
    log_success "Virtual environment created."
}

# ------------------------------
# Dependency synchronization
# ------------------------------
sync_dependencies() {
    log_info "Synchronizing dependencies with uv.lock..."
    
    if ! uv sync --all-extras; then
        log_error "Failed to synchronize dependencies."
        exit 1
    fi
    
    log_success "Dependencies synchronized."
}

# ------------------------------
# Pre-commit hooks (optional)
# ------------------------------
install_precommit() {
    if command -v uv &> /dev/null && uv run pre-commit --version &> /dev/null; then
        log_info "Installing pre-commit hooks..."
        
        if uv run pre-commit install; then
            log_success "Pre-commit hooks installed."
        else
            log_warn "Failed to install pre-commit hooks."
        fi
    else
        log_info "Pre-commit not available, skipping."
    fi
}

# ------------------------------
# Main execution
# ------------------------------
main() {
    parse_args "$@"
    
    (( VERBOSE == 1 )) && log_info "Running $(script_name) version $VERSION"
    
    #__________ Check prerequisites __________
    if ! command -v curl &> /dev/null; then
        log_error "curl is required but not installed."
        exit 1
    fi
    
    #__________ Setup steps __________
    ensure_uv_installed
    setup_environment
    sync_dependencies
    install_precommit
    
    #__________ Completion __________
    log_success "=== Setup complete! ==="
    log_info "To activate environment: source .venv/bin/activate"
    log_info "Or use: uv run <command>"
    log_info "Example: uv run officeboy --help"
}

main "$@"