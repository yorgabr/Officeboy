#!/usr/bin/env pwsh

# uv_setup.ps1
#
# This script has the purpose of setting up the Officeboy development environment
# using UV (the ultra-fast Python package manager written in Rust) on Windows.


#Requires -Version 6.0

<#
.SYNOPSIS
    Setup Officeboy development environment using UV.

.DESCRIPTION
    This script checks for UV installation, creates a virtual environment,
    synchronizes dependencies, and installs pre-commit hooks.
    Compatible with Windows PowerShell 5.1 and PowerShell 6/7+.

.EXAMPLE
    .\uv_setup.ps1 -PythonVersion "3.11"

.NOTES
    Author: Yorga Babuscan (yorgabr@gmail.com)
#>

[CmdletBinding()]
param(
    [string]$PythonVersion = "3.11",
    [switch]$Verbose,
    [switch]$Debug
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$SCRIPT_VERSION = "1.0.0"

#__________ Color helpers _________________________________________________
$ESC = "`e"
$Cyan   = "${ESC}[36m"
$Yellow = "${ESC}[33m"
$Green  = "${ESC}[32m"
$Red    = "${ESC}[31m"
$Reset  = "${ESC}[0m"

function Out-Info    { param([string]$m) if ($Verbose -or $Debug) { [Console]::Out.WriteLine("$Cyan[INFO]$Reset $m") } }
function Out-Warn    { param([string]$m) if ($Verbose -or $Debug) { [Console]::Out.WriteLine("$Yellow[WARN]$Reset $m") } }
function Out-Success { param([string]$m) if ($Verbose -or $Debug) { [Console]::Out.WriteLine("$Green[SUCCESS]$Reset $m") } }
function Out-Error   { param([string]$m) [Console]::Error.WriteLine("$Red[ERROR]$Reset $m") }
function Out-Debug   { param([string]$m) if ($Debug) { [Console]::Out.WriteLine("$Cyan[DEBUG]$Reset $m") } }

#__________ Version and usage _____________________________________________
function Get-ScriptName { $MyInvocation.MyCommand.Name }
function Show-Version { Write-Host "$(Get-ScriptName) version $SCRIPT_VERSION" }

function Show-Usage {
    @"
uv_setup.ps1 - Setup Officeboy development environment using UV.

Usage:
    .\uv_setup.ps1 [options]

Options:
    -PythonVersion VERSION    Python version to use (default: 3.11).
    -Verbose                  Echo each precondition and important step.
    -Debug                    Print full commands before executing.
                              (Debug implies Verbose)
    -Version                  Show script semantic version and exit.
    -Help                     Show this help and exit.

Author: Yorga Babuscan (yorgabr@gmail.com)
"@
}

#__________ Argument parsing ______________________________________________
if ($args -contains '-Version') { Show-Version; exit 0 }
if ($args -contains '-Help' -or $args -contains '-h') { Show-Usage; exit 0 }

Out-Info "Running $(Get-ScriptName) version $SCRIPT_VERSION"

#__________ UV installation check _________________________________________
function Test-UvInstalled {
    try {
        $null = Get-Command uv -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

function Install-Uv {
    Out-Warn "UV not found. Installing..."
    
    try {
        # Install UV via PowerShell
        $installScript = "irm https://astral.sh/uv/install.ps1 | iex"
        powershell -ExecutionPolicy ByPass -c $installScript
        
        # Reload PATH
        $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + 
                    [Environment]::GetEnvironmentVariable("Path", "User")
        
        Out-Success "UV installed successfully."
    } catch {
        Out-Error "Failed to install UV: $($_.Exception.Message)"
        exit 1
    }
}

function Get-UvVersion {
    try {
        return (uv --version)
    } catch {
        return "unknown"
    }
}

#__________ Environment setup _____________________________________________
function Install-PythonVersion {
    param([string]$Version)
    
    Out-Info "Installing Python $Version..."
    
    try {
        uv python install $Version | Out-Null
        Out-Success "Python $Version installed."
    } catch {
        Out-Error "Failed to install Python $Version : $($_.Exception.Message)"
        exit 1
    }
}

function New-VirtualEnvironment {
    param([string]$Version)
    
    Out-Info "Creating virtual environment with Python $Version..."
    
    try {
        uv venv --python $Version | Out-Null
        Out-Success "Virtual environment created."
    } catch {
        Out-Error "Failed to create virtual environment: $($_.Exception.Message)"
        exit 1
    }
}

#__________ Dependency synchronization ____________________________________
function Sync-Dependencies {
    Out-Info "Synchronizing dependencies with uv.lock..."
    
    try {
        uv sync --all-extras | Out-Null
        Out-Success "Dependencies synchronized."
    } catch {
        Out-Error "Failed to synchronize dependencies: $($_.Exception.Message)"
        exit 1
    }
}

#__________ Pre-commit hooks ______________________________________________
function Install-PreCommitHooks {
    Out-Info "Installing pre-commit hooks..."
    
    try {
        $null = uv run pre-commit --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            uv run pre-commit install | Out-Null
            Out-Success "Pre-commit hooks installed."
        } else {
            Out-Warn "Pre-commit not available, skipping."
        }
    } catch {
        Out-Warn "Failed to install pre-commit hooks: $($_.Exception.Message)"
    }
}

#__________ Main execution ________________________________________________
#__________ Check prerequisites __________
if (-not (Get-Command curl -ErrorAction SilentlyContinue)) {
    Out-Error "curl is required but not available."
    exit 1
}

#__________ Setup steps __________
if (-not (Test-UvInstalled)) {
    Install-Uv
} else {
    Out-Info "UV is already installed."
}

$uvVersion = Get-UvVersion
Out-Info "UV version: $uvVersion"

Install-PythonVersion -Version $PythonVersion
New-VirtualEnvironment -Version $PythonVersion
Sync-Dependencies
Install-PreCommitHooks

#__________ Completion __________
Out-Success "=== Setup complete! ==="
Out-Info "To activate environment: .venv\Scripts\activate"
Out-Info "Or use: uv run <command>"
Out-Info "Example: uv run officeboy --help"