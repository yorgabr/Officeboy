#!/usr/bin/env bash

# uv_build.sh
#
# This script has the purpose of building Officeboy packages using UV.
# It orchestrates linting, type checking, testing, and package building
# with proper error handling and retry logic where appropriate.


# shellcheck shell=bash

set -euo pipefail

VERSION="1.0.0"

# Defaults
COMMAND="all"
VERBOSE=0
DEBUG=0
RETRY_COUNT=1

# ------------------------------
# Logging (timestamp + tag)
# ------------------------------
timestamp() { date +%Y%m%d%H%M%S; }
log_error() { printf "%s\t[ERROR]\t%s\n" "$(timestamp)" "$*" >&2; }
log_info()  { (( VERBOSE == 1 || DEBUG == 1 )) && printf "%s\t[INFO]\t%s\n" "$(timestamp)" "$*"; }
log_debug() { (( DEBUG == 1 )) && printf "%s\t[DEBUG]\t%s\n" "$(timestamp)" "$*"; }
log_success() { printf "%s\t[SUCCESS]\t%s\n" "$(timestamp)" "$*"; }

script_name() { basename -- "$0"; }
print_version() { printf "%s version %s\n" "$(script_name)" "$VERSION"; }

print_usage() {
    cat <<'USAGE'
uv_build.sh — Build Officeboy packages using UV package manager.

Usage:
    uv_build.sh [command] [options]

Commands:
    lint        Run code linting with ruff.
    type        Run type checking with mypy.
    test        Run test suite with pytest.
    build       Build wheel and sdist packages.
    all         Run lint, type, test, and build in sequence (default).

Options:
    --retry N       Number of retries for failed steps (default: 1).
    --verbose       Echo each step and precondition.
    --debug         Print full commands and internal state.
    --version       Show script semantic version and exit.
    -h, --help      Show this help and exit.
USAGE
}

parse_args() {
    if [[ $# -eq 0 ]]; then
        COMMAND="all"
        return 0
    fi

    case "$1" in
        lint|type|test|build|all) COMMAND="$1"; shift ;;
        -h|--help) print_usage; exit 0 ;;
        --version) print_version; exit 0 ;;
        *) log_error "Unknown command: $1"; print_usage; exit 2 ;;
    esac

    while (("$#")); do
        case "$1" in
            --verbose)      VERBOSE=1; shift ;;
            --debug)        DEBUG=1; VERBOSE=1; shift ;;
            --retry)        shift; [[ $# -gt 0 ]] || { log_error "--retry requires a number."; exit 2; }; RETRY_COUNT="$1"; shift ;;
            --retry=*)      RETRY_COUNT="${1#--retry=}"; shift ;;
            *) log_error "Unknown option: $1"; print_usage; exit 2 ;;
        esac
    done
}

# ------------------------------
# Command execution with retry
# ------------------------------
run_with_retry() {
    local description="$1"
    shift
    local cmd=("$@")
    
    log_info "Executing: $description"
    log_debug "Command: ${cmd[*]}"
    
    for (( i=1; i<=RETRY_COUNT; i++ )); do
        if "${cmd[@]}"; then
            log_success "$description completed."
            return 0
        fi
        
        if (( i < RETRY_COUNT )); then
            log_error "$description failed (attempt $i/$RETRY_COUNT). Retrying..."
        else
            log_error "$description failed after $RETRY_COUNT attempts."
            return 1
        fi
    done
}

# ------------------------------
# Build steps
# ------------------------------
run_lint() {
    run_with_retry "Linting with ruff" uv run ruff check src tests
}

run_type() {
    run_with_retry "Type checking with mypy" uv run mypy src/officeboy
}

run_test() {
    run_with_retry "Testing with pytest" uv run pytest --cov=officeboy --cov-report=term
}

run_build() {
    local failed=0
    
    if ! run_with_retry "Building wheel" uv build --wheel; then
        failed=1
    fi
    
    if ! run_with_retry "Building sdist" uv build --sdist; then
        failed=1
    fi
    
    return $failed
}

# ------------------------------
# Main execution
# ------------------------------
main() {
    parse_args "$@"
    
    (( VERBOSE == 1 )) && log_info "Running $(script_name) version $VERSION"
    (( DEBUG == 1 )) && log_debug "Command: $COMMAND, Retries: $RETRY_COUNT"
    
    # Verify UV is available
    if ! command -v uv &> /dev/null; then
        log_error "UV not found in PATH. Please install UV first."
        exit 1
    fi
    
    local exit_code=0
    
    case "$COMMAND" in
        lint)
            run_lint || exit_code=1
            ;;
        type)
            run_type || exit_code=1
            ;;
        test)
            run_test || exit_code=1
            ;;
        build)
            run_build || exit_code=1
            ;;
        all)
            log_info "Running full build pipeline..."
            run_lint || exit_code=1
            run_type || exit_code=1
            run_test || exit_code=1
            run_build || exit_code=1
            ;;
    esac
    
    if (( exit_code == 0 )); then
        log_success "=== Build completed successfully ==="
    else
        log_error "=== Build completed with errors ==="
    fi
    
    exit $exit_code
}

main "$@"