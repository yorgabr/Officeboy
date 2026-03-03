#!/usr/bin/env bash

# init_repo.sh
#
# This script has the purpose of initializing a Github repository with proper
# tagging and release structure.
#
# Author: Yorga Babuscan (yorgabr@gmail.com)


# shellcheck shell=bash

set -euo pipefail

SCRIPT_VERSION="1.2.0"

#__________ Default values __________
GITHUB_USER=""
GITHUB_REPO=""

# Developer defaults: use git config if available, otherwise fallback
DEFAULT_GIT_NAME=$(git config user.name 2>/dev/null || echo "")
DEFAULT_GIT_EMAIL=$(git config user.email 2>/dev/null || echo "")

DEV_NAME=""      
DEV_EMAIL=""     
PACK_VERSION="0.1.0"
VERBOSE=0
SET_LOCAL_GIT_CONFIG=1  # Default: true (set local git config)

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
    printf "%s\t${Yellow}[WARN]${Reset}\t%s\n" "$(timestamp)" "$*"; 
}

log_info() { 
    (( VERBOSE == 1 )) && printf "%s\t${Cyan}[INFO]${Reset}\t%s\n" "$(timestamp)" "$*"; 
}

log_success() { 
    (( VERBOSE == 1 )) && printf "%s\t${Green}[SUCCESS]${Reset}\t%s\n" "$(timestamp)" "$*"; 
}

script_name() { basename -- "$0"; }

print_version() { 
    printf "%s version %s\n" "$(script_name)" "$SCRIPT_VERSION"; 
}

print_usage() {
    cat <<'USAGE'
init_repo.sh — Initialize a Git repository with proper tagging and release structure.

Usage:
    init_repo.sh --github-user <username> --github-repo <name> [options]

Required Arguments:
    --github-user USERNAME    GitHub username for remote URL.
    --github-repo NAME        GitHub repository name.

Options:
    --version                 Show script semantic version and exit.
    --help, -h                Show this help and exit.
    --dev-name NAME           Developer's full name (default: --github-user value,
                              or git config user.name if set).
    --dev-email EMAIL         Developer's e-mail (default: git config user.email
                              if set, otherwise empty).
    --pack-version SEMVER     Package version for tag (default: 0.1.0).
    --set-local-git-config    Set user.name and user.email in local git config
                              for this repository only (default: true).
    --no-set-local-git-config Disable setting local git config (use global).
    --verbose                 Echo each step.
    --generate-completion SCOPE
                              Generate and install bash completion.
                              SCOPE can be: TEMP, USER, or SYSTEM.
                              TEMP: sources completion for current session only.
                              USER: installs to ~/.local/share/bash-completion/completions/.
                              SYSTEM: installs to /etc/bash_completion.d/ (requires sudo).

Examples:
    # Basic usage (sets local git config by default)
    init_repo.sh --github-user john --github-repo myproject

    # Use global git config instead
    init_repo.sh --github-user john --github-repo myproject --no-set-local-git-config

    # Full specification
    init_repo.sh --github-user john --github-repo myproject \
        --dev-name "John Doe" --dev-email "john@example.com" \
        --pack-version 1.0.0

    # Generate and install autocomplete for current user
    init_repo.sh --generate-completion USER

    # Generate and install autocomplete system-wide (requires sudo)
    sudo init_repo.sh --generate-completion SYSTEM

Author: Yorga Babuscan (yorgabr@gmail.com)
USAGE
}

# ------------------------------
# Bash Completion Generator
# ------------------------------
generate_completion_script() {
    cat <<'COMPLETION'
# init_repo.sh bash completion script
# Generated automatically - do not edit manually

_init_repo.sh() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # Long options
    local long_opts="--github-user --github-repo --dev-name --dev-email 
                     --pack-version --set-local-git-config 
                     --no-set-local-git-config --verbose 
                     --version --help --generate-completion"
    
    case "$prev" in
        --github-user|--github-repo|--dev-name|--dev-email|--pack-version|--generate-completion)
            # These take arbitrary values, no completion
            return 0
            ;;
    esac
    
    # If current word starts with dash, complete options
    if [[ "$cur" == -* ]]; then
        COMPREPLY=( $(compgen -W "${long_opts}" -- "$cur") )
        return 0
    fi
    
    return 0
}

complete -F _init_repo.sh init_repo.sh
COMPLETION
}

# ------------------------------
# Completion Installation
# ------------------------------
install_completion_temp() {
    log_info "Installing bash completion for current session (TEMP)..."
    # Source directly in current shell if sourced, otherwise instruct user
    if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
        # Script is being sourced
        eval "$(generate_completion_script)"
        log_success "Bash completion activated for current session."
    else
        # Script is being executed
        generate_completion_script
        log_info "To activate in current session, run:"
        log_info "  source <(init_repo.sh --generate-completion TEMP)"
    fi
}

install_completion_user() {
    log_info "Installing bash completion for user (USER)..."
    
    local completion_dir="${HOME}/.local/share/bash-completion/completions"
    local completion_file="${completion_dir}/init_repo.sh"
    
    # Create directory if needed
    if [[ ! -d "$completion_dir" ]]; then
        log_info "Creating directory: $completion_dir"
        mkdir -p "$completion_dir" || {
            log_error "Failed to create directory: $completion_dir"
            exit 1
        }
    fi
    
    # Generate and install completion script
    generate_completion_script > "$completion_file" || {
        log_error "Failed to write completion file: $completion_file"
        exit 1
    }
    
    log_success "Bash completion installed to: $completion_file"
    log_info "To activate immediately, run: source '$completion_file'"
    log_info "Or restart your terminal."
}

install_completion_system() {
    log_info "Installing bash completion system-wide (SYSTEM)..."
    
    local completion_dir="/etc/bash_completion.d"
    local completion_file="${completion_dir}/init_repo.sh"
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        log_error "System-wide installation requires root privileges."
        log_info "Please run with sudo: sudo init_repo.sh --generate-completion SYSTEM"
        exit 1
    fi
    
    # Check if directory exists
    if [[ ! -d "$completion_dir" ]]; then
        log_error "Directory does not exist: $completion_dir"
        log_info "Your system may not have bash-completion installed."
        exit 1
    fi
    
    # Generate and install completion script
    generate_completion_script > "$completion_file" || {
        log_error "Failed to write completion file: $completion_file"
        exit 1
    }
    
    # Set appropriate permissions
    chmod 644 "$completion_file" || log_warn "Could not set permissions on $completion_file"
    
    log_success "Bash completion installed to: $completion_file"
    log_info "All users will have completion available after starting a new shell."
}

handle_generate_completion() {
    local scope="$1"
    
    case "$scope" in
        TEMP)
            install_completion_temp
            ;;
        USER)
            install_completion_user
            ;;
        SYSTEM)
            install_completion_system
            ;;
        *)
            log_error "Invalid scope for --generate-completion: $scope"
            log_info "Valid scopes are: TEMP, USER, SYSTEM"
            exit 1
            ;;
    esac
}

# ------------------------------
# Argument parsing
# ------------------------------
parse_args() {
    if [[ $# -eq 0 ]]; then
        print_usage
        exit 0
    fi
    
    # Check for completion generation first (it runs standalone)
    local completion_scope=""
    local i=0
    for arg in "$@"; do
        ((i++))
        if [[ "$arg" == "--generate-completion" ]]; then
            # Get next argument as scope
            if [[ $i -lt $# ]]; then
                completion_scope="${@:$((i+1)):1}"
                if [[ "$completion_scope" == --* ]] || [[ -z "$completion_scope" ]]; then
                    log_error "--generate-completion requires a scope argument (TEMP|USER|SYSTEM)"
                    exit 1
                fi
                handle_generate_completion "$completion_scope"
                exit 0
            else
                log_error "--generate-completion requires a scope argument (TEMP|USER|SYSTEM)"
                exit 1
            fi
        fi
    done
    
    while (("$#")); do
        case "$1" in
            -h|--help)            
                print_usage; exit 0 ;;
            --version)            
                print_version; exit 0 ;;
            --verbose)            
                VERBOSE=1; shift ;;
            --set-local-git-config)
                SET_LOCAL_GIT_CONFIG=1; shift ;;
            --no-set-local-git-config)
                SET_LOCAL_GIT_CONFIG=0; shift ;;
            --github-user)
                shift; [[ $# -gt 0 ]] || { log_error "--github-user requires a username."; exit 2; }
                GITHUB_USER="$1"; shift ;;
            --github-repo)
                shift; [[ $# -gt 0 ]] || { log_error "--github-repo requires a repository name."; exit 2; }
                GITHUB_REPO="$1"; shift ;;
            --dev-name)
                shift; [[ $# -gt 0 ]] || { log_error "--dev-name requires a name."; exit 2; }
                DEV_NAME="$1"; shift ;;
            --dev-email)
                shift; [[ $# -gt 0 ]] || { log_error "--dev-email requires an e-mail."; exit 2; }
                DEV_EMAIL="$1"; shift ;;
            --pack-version)
                shift; [[ $# -gt 0 ]] || { log_error "--pack-version requires a semantic version."; exit 2; }
                PACK_VERSION="$1"; shift ;;
            --generate-completion)
                # This should have been handled above, but check anyway
                shift
                if [[ $# -gt 0 ]] && [[ ! "$1" == --* ]]; then
                    handle_generate_completion "$1"
                    exit 0
                else
                    log_error "--generate-completion requires a scope argument (TEMP|USER|SYSTEM)"
                    exit 1
                fi
                ;;
            *) 
                log_error "Unknown option: $1"; 
                print_usage; 
                exit 2 ;;
        esac
    done
    
    #__________ Validate required arguments __________
    if [[ -z "$GITHUB_USER" ]]; then
        log_error "Missing required argument: --github-user"
        print_usage
        exit 2
    fi
    
    if [[ -z "$GITHUB_REPO" ]]; then
        log_error "Missing required argument: --github-repo"
        print_usage
        exit 2
    fi
    
    #__________ Apply defaults for optional arguments __________
    
    # DEV_NAME: use provided value, or git config user.name, or fallback to GITHUB_USER
    if [[ -z "$DEV_NAME" ]]; then
        if [[ -n "$DEFAULT_GIT_NAME" ]]; then
            DEV_NAME="$DEFAULT_GIT_NAME"
            log_info "Using git config user.name for dev-name: $DEV_NAME"
        else
            DEV_NAME="$GITHUB_USER"
            log_info "Using github-user for dev-name: $DEV_NAME"
        fi
    fi
    
    # DEV_EMAIL: use provided value, or git config user.email, or leave empty
    if [[ -z "$DEV_EMAIL" ]]; then
        if [[ -n "$DEFAULT_GIT_EMAIL" ]]; then
            DEV_EMAIL="$DEFAULT_GIT_EMAIL"
            log_info "Using git config user.email for dev-email: $DEV_EMAIL"
        else
            DEV_EMAIL=""
            log_info "No dev-email provided and no git config user.email set. Leaving empty."
        fi
    fi
}

# ------------------------------
# Git initialization
# ------------------------------
init_git_repository() {
    if [ ! -d ".git" ]; then
        log_info "Initializing git repository..."
        
        if ! git init; then
            log_error "Failed to initialize git repository."
            exit 1
        fi
        
        if ! git checkout -b main; then
            log_error "Failed to create main branch."
            exit 1
        fi
        
        log_success "Git repository initialized."
    else
        log_info "Git repository already exists."
    fi
    
    #__________ Configure git identity locally if requested __________
    if [[ $SET_LOCAL_GIT_CONFIG -eq 1 ]]; then
        log_info "Setting local git config for this repository..."
        
        if [[ -n "$DEV_NAME" ]]; then
            if git config --local user.name "$DEV_NAME"; then
                log_success "Set local user.name: $DEV_NAME"
            else
                log_warn "Failed to set local user.name"
            fi
        fi
        
        if [[ -n "$DEV_EMAIL" ]]; then
            if git config --local user.email "$DEV_EMAIL"; then
                log_success "Set local user.email: $DEV_EMAIL"
            else
                log_warn "Failed to set local user.email"
            fi
        fi
        
        # Show current local config
        log_info "Local git config for this repository:"
        log_info "  user.name:  $(git config --local user.name 2>/dev/null || echo '(not set)')"
        log_info "  user.email: $(git config --local user.email 2>/dev/null || echo '(not set)')"
    else
        log_info "Using global git config (local config not set)"
        # Set git config for commit only if not setting locally
        # (will use global or already-set local values)
        if [[ -n "$DEV_NAME" ]]; then
            git config user.name "$DEV_NAME" 2>/dev/null || true
        fi
        if [[ -n "$DEV_EMAIL" ]]; then
            git config user.email "$DEV_EMAIL" 2>/dev/null || true
        fi
    fi
}

# ------------------------------
# Initial commit
# ------------------------------
create_initial_commit() {
    log_info "Adding files to git..."
    
    if ! git add .; then
        log_error "Failed to add files to git."
        exit 1
    fi
    
    log_info "Creating initial commit..."
    
    local commit_message
    commit_message="Initial commit: $GITHUB_REPO

- Project setup with proper structure
- Version $PACK_VERSION"
    
    # Add author line only if we have an email
    if [[ -n "$DEV_EMAIL" ]]; then
        commit_message="$commit_message
- Author: $DEV_NAME <$DEV_EMAIL>"
    else
        commit_message="$commit_message
- Author: $DEV_NAME"
    fi
    
    if ! git commit -m "$commit_message"; then
        log_warn "Nothing to commit or commit failed."
    else
        log_success "Initial commit created."
    fi
}

# ------------------------------
# Version tag creation
# ------------------------------
create_version_tag() {
    log_info "Creating tag v$PACK_VERSION..."
    
    local tag_message
    tag_message="Release v$PACK_VERSION

Initial release of $GITHUB_REPO."
    
    # Add author line only if we have an email
    if [[ -n "$DEV_EMAIL" ]]; then
        tag_message="$tag_message
Author: $DEV_NAME <$DEV_EMAIL>"
    else
        tag_message="$tag_message
Author: $DEV_NAME"
    fi
    
    if git tag -a "v$PACK_VERSION" -m "$tag_message" 2>/dev/null; then
        log_success "Tag v$PACK_VERSION created."
    else
        log_warn "Tag v$PACK_VERSION may already exist."
    fi
}

# ------------------------------
# Release notes generation
# ------------------------------
generate_release_notes() {
    log_info "Generating release notes..."
    
    local author_line
    if [[ -n "$DEV_EMAIL" ]]; then
        author_line="$DEV_NAME ($DEV_EMAIL)"
    else
        author_line="$DEV_NAME"
    fi
    
    cat > RELEASE_NOTES.md << EOF
# Release v$PACK_VERSION

## What's New
- First stable release of $GITHUB_REPO
- Project initialized and configured

## Installation

Download appropriate package for your platform from the releases section.

## Documentation
See README.md and CONTRIBUTING.md for details.

Author: $author_line
EOF
    
    log_success "Release notes created: RELEASE_NOTES.md"
}

# ------------------------------
# Remote setup instructions
# ------------------------------
show_remote_instructions() {
    log_info ""
    log_info "To connect to GitHub, run:"
    log_info "  git remote add origin https://github.com/$GITHUB_USER/$GITHUB_REPO.git"
    log_info "  git push -u origin main"
    log_info ""
    log_info "To push tag to GitHub:"
    log_info "  git push origin v$PACK_VERSION"
    log_info ""
    
    #__________ Show git identity info __________
    log_info "Git identity for this repository:"
    log_info "  Commit will use: $(git config user.name 2>/dev/null || echo '(not set)') <$(git config user.email 2>/dev/null || echo '(not set)')>"
    
    if [[ $SET_LOCAL_GIT_CONFIG -eq 1 ]]; then
        log_info ""
        log_info "Local git config was set. Future commits in this repo will use:"
        log_info "  user.name:  $(git config --local user.name 2>/dev/null || echo '(not set)')"
        log_info "  user.email: $(git config --local user.email 2>/dev/null || echo '(not set)')"
        log_info ""
        log_info "Your global git config remains unchanged:"
        log_info "  global user.name:  $(git config --global user.name 2>/dev/null || echo '(not set)')"
        log_info "  global user.email: $(git config --global user.email 2>/dev/null || echo '(not set)')"
    else
        log_info ""
        log_info "Using global git config (not modified for this repo)"
    fi
}

# ------------------------------
# Main execution
# ------------------------------
main() {
    parse_args "$@"
    
    (( VERBOSE == 1 )) && log_info "Running $(script_name) version $SCRIPT_VERSION"
    log_info "Initializing repository: $GITHUB_REPO"
    log_info "GitHub user: $GITHUB_USER"
    log_info "Developer: $DEV_NAME ${DEV_EMAIL:+<$DEV_EMAIL>}"
    log_info "Package version: $PACK_VERSION"
    [[ $SET_LOCAL_GIT_CONFIG -eq 1 ]] && log_info "Will set local git config: YES" || log_info "Will set local git config: NO (using global)"
    
    #__________ Execute steps __________
    init_git_repository
    create_initial_commit
    create_version_tag
    generate_release_notes
    
    #__________ Completion __________
    log_success "=== Initialization complete ==="
    show_remote_instructions
    log_info "Next steps:"
    log_info "1. Create repository on GitHub: https://github.com/new"
    log_info "2. Run: git remote add origin https://github.com/$GITHUB_USER/$GITHUB_REPO.git"
    log_info "3. Run: git push -u origin main"
    log_info "4. Run: git push origin v$PACK_VERSION"
    log_info "5. Upload release artifacts"
}

main "$@"