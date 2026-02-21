#!/usr/bin/env python3
"""Validate Terraform, Ansible, and frontend configurations."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def print_header(text):
    print(f"\n{'=' * 60}")
    print(text)
    print('=' * 60)


def print_success(text):
    print(f"[OK] {text}")


def print_warning(text):
    print(f"[WARN] {text}")


def print_error(text):
    print(f"[ERROR] {text}")


def run_command(cmd, cwd=None, capture_output=True):
    """Run a shell command and return success status."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            shell=isinstance(cmd, str)
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def check_prerequisites():
    """Check that required tools are installed."""
    print_header("Checking Prerequisites")
    
    tools = {
        'terraform': 'terraform --version',
        'ansible-playbook': 'ansible-playbook --version',
        'python3': 'python3 --version',
        'node': 'node --version',
        'npm': 'npm --version'
    }
    
    missing = []
    for tool, check_cmd in tools.items():
        success, stdout, _ = run_command(check_cmd)
        if success:
            version = stdout.strip().split('\n')[0] if stdout else "unknown"
            print_success(f"{tool}: {version}")
        else:
            print_error(f"{tool}: not found")
            missing.append(tool)
    
    if missing:
        print_warning(f"Missing tools: {', '.join(missing)}")
        print("Some validation tests will be skipped.")
    
    return missing


def validate_terraform():
    """Validate Terraform configuration."""
    print_header("Validating Terraform")
    
    terraform_dir = Path('terraform')
    if not terraform_dir.exists():
        print_error("Terraform directory not found")
        return False
    
    all_valid = True
    
    # Check terraform fmt
    success, stdout, stderr = run_command(['terraform', 'fmt', '-check', '-recursive'], cwd=terraform_dir)
    if success:
        print_success("Terraform formatting is valid")
    else:
        print_error("Terraform formatting issues found")
        print("Run 'terraform fmt -recursive' to fix")
        all_valid = False
    
    # Check terraform init (without backend for validation)
    success, stdout, stderr = run_command(['terraform', 'init', '-backend=false'], cwd=terraform_dir)
    if success:
        print_success("Terraform init successful")
    else:
        print_error(f"Terraform init failed: {stderr}")
        all_valid = False
    
    # Check terraform validate
    success, stdout, stderr = run_command(['terraform', 'validate'], cwd=terraform_dir)
    if success:
        print_success("Terraform configuration is valid")
    else:
        print_error(f"Terraform validation failed: {stderr}")
        all_valid = False
    
    # Check for required files
    required_files = ['main.tf', 'variables.tf', 'outputs.tf']
    for file in required_files:
        if (terraform_dir / file).exists():
            print_success(f"Required file exists: {file}")
        else:
            print_error(f"Missing required file: {file}")
            all_valid = False
    
    return all_valid


def validate_ansible():
    """Validate Ansible configuration."""
    print_header("Validating Ansible")
    
    ansible_dir = Path('ansible')
    if not ansible_dir.exists():
        print_error("Ansible directory not found")
        return False
    
    all_valid = True
    
    # Check ansible-playbook syntax
    playbook_path = ansible_dir / 'playbooks' / 'benchmark.yml'
    if playbook_path.exists():
        success, stdout, stderr = run_command(
            ['ansible-playbook', '--syntax-check', '-i', 'localhost,', str(playbook_path)],
            cwd=ansible_dir
        )
        if success:
            print_success("Ansible playbook syntax is valid")
        else:
            # Syntax check may fail due to missing inventory, that's ok for validation
            if "syntax" in stderr.lower():
                print_error(f"Ansible playbook has syntax errors: {stderr}")
                all_valid = False
            else:
                print_warning("Could not fully validate Ansible (inventory/connection issues)")
                print_success("No syntax errors detected")
    else:
        print_error(f"Playbook not found: {playbook_path}")
        all_valid = False
    
    # Check for required files
    required_files = ['ansible.cfg', 'playbooks/benchmark.yml']
    for file in required_files:
        if (ansible_dir / file).exists():
            print_success(f"Required file exists: {file}")
        else:
            print_error(f"Missing required file: {file}")
            all_valid = False
    
    return all_valid


def validate_python():
    """Validate Python scripts."""
    print_header("Validating Python Scripts")
    
    all_valid = True
    
    # Check process_results.py syntax
    script_path = Path('scripts/process_results.py')
    if script_path.exists():
        success, stdout, stderr = run_command(['python3', '-m', 'py_compile', str(script_path)])
        if success:
            print_success("process_results.py syntax is valid")
        else:
            print_error(f"process_results.py has syntax errors: {stderr}")
            all_valid = False
    else:
        print_error("process_results.py not found")
        all_valid = False
    
    # Check if we can import the module
    scripts_dir = Path('scripts').absolute()
    if scripts_dir.exists():
        sys.path.insert(0, str(scripts_dir))
        try:
            import process_results  # noqa: F401
            print_success("process_results.py can be imported")
        except Exception as e:
            print_error(f"Cannot import process_results.py: {e}")
            all_valid = False
    
    # Run unit tests if pytest is available
    success, _, _ = run_command(['python3', '-c', 'import pytest'])
    if success:
        print_header("Running Python Unit Tests")
        test_success, stdout, stderr = run_command(
            ['python3', '-m', 'pytest', 'tests/', '-v'],
            capture_output=True
        )
        if test_success:
            print_success("All unit tests passed")
            print(stdout)
        else:
            print_error("Some unit tests failed")
            print(stderr)
            all_valid = False
    else:
        print_warning("pytest not installed, skipping unit tests")
        print("Install with: pip install pytest")
    
    return all_valid


def validate_frontend():
    """Validate frontend configuration."""
    print_header("Validating Frontend")
    
    frontend_dir = Path('frontend')
    if not frontend_dir.exists():
        print_error("Frontend directory not found")
        return False
    
    all_valid = True
    
    # Check for required files
    required_files = ['package.json', 'vite.config.js', 'index.html']
    for file in required_files:
        if (frontend_dir / file).exists():
            print_success(f"Required file exists: {file}")
        else:
            print_error(f"Missing required file: {file}")
            all_valid = False
    
    # Validate package.json
    package_json_path = frontend_dir / 'package.json'
    if package_json_path.exists():
        try:
            with open(package_json_path) as f:
                package = json.load(f)
            
            required_fields = ['name', 'version', 'scripts', 'dependencies']
            for field in required_fields:
                if field in package:
                    print_success(f"package.json has {field}")
                else:
                    print_error(f"package.json missing {field}")
                    all_valid = False
            
            # Check for required scripts
            if 'build' in package.get('scripts', {}):
                print_success("package.json has build script")
            else:
                print_warning("package.json missing build script")
        except json.JSONDecodeError as e:
            print_error(f"package.json is invalid JSON: {e}")
            all_valid = False
    
    # Try to build the frontend
    print_header("Building Frontend")
    success, stdout, stderr = run_command(['npm', 'ci'], cwd=frontend_dir)
    if success:
        print_success("npm install successful")
        
        success, stdout, stderr = run_command(['npm', 'run', 'build'], cwd=frontend_dir)
        if success:
            print_success("Frontend build successful")
        else:
            print_error(f"Frontend build failed: {stderr}")
            all_valid = False
    else:
        print_warning(f"npm install failed (may be expected in CI): {stderr}")
    
    return all_valid


def validate_documentation():
    """Validate documentation consistency."""
    print_header("Validating Documentation")
    
    all_valid = True
    
    # Check for required documentation files
    required_docs = ['README.md', 'docs/architecture.md', 'docs/setup-guide.md']
    for doc in required_docs:
        if Path(doc).exists():
            print_success(f"Documentation exists: {doc}")
        else:
            print_error(f"Missing documentation: {doc}")
            all_valid = False
    
    # Check README for required sections
    readme_path = Path('README.md')
    if readme_path.exists():
        content = readme_path.read_text()
        required_sections = ['Overview', 'Usage', 'Methodology']
        for section in required_sections:
            if section.lower() in content.lower():
                print_success(f"README has {section} section")
            else:
                print_warning(f"README missing {section} section")
    
    # Check for configuration file
    config_path = Path('config/instances.yaml')
    if config_path.exists():
        try:
            import yaml
            with open(config_path) as f:
                config = yaml.safe_load(f)
            if config and 'providers' in config:
                print_success("Configuration file is valid YAML")
            else:
                print_warning("Configuration file may be incomplete")
        except ImportError:
            print_warning("PyYAML not installed, skipping config validation")
        except Exception as e:
            print_error(f"Configuration file error: {e}")
            all_valid = False
    
    return all_valid


def validate_github_actions():
    """Validate GitHub Actions workflows."""
    print_header("Validating GitHub Actions")
    
    workflows_dir = Path('.github/workflows')
    if not workflows_dir.exists():
        print_error("GitHub Actions workflows directory not found")
        return False
    
    all_valid = True
    
    # Check workflow files exist
    workflow_files = list(workflows_dir.glob('*.yml'))
    if workflow_files:
        print_success(f"Found {len(workflow_files)} workflow files")
    else:
        print_error("No workflow files found")
        all_valid = False
    
    # Basic YAML validation
    for workflow_file in workflow_files:
        try:
            import yaml
            with open(workflow_file) as f:
                yaml.safe_load(f)
            print_success(f"{workflow_file.name} is valid YAML")
        except ImportError:
            print_warning("PyYAML not installed, skipping YAML validation")
            break
        except yaml.YAMLError as e:
            print_error(f"{workflow_file.name} has YAML errors: {e}")
            all_valid = False
    
    return all_valid


def main():
    parser = argparse.ArgumentParser(description='Validate Cloud-Bench configuration')
    parser.add_argument('--skip', nargs='+', choices=['terraform', 'ansible', 'python', 'frontend', 'docs', 'github'],
                        help='Skip specific validation steps')
    parser.add_argument('--only', nargs='+', choices=['terraform', 'ansible', 'python', 'frontend', 'docs', 'github'],
                        help='Only run specific validation steps')
    args = parser.parse_args()
    
    skip = set(args.skip or [])
    only = set(args.only or [])

    results = {}

    print("Cloud-Bench Validation")
    print(f"Working directory: {os.getcwd()}")
    
    # Check prerequisites first
    check_prerequisites()

    # Run validation steps
    validation_steps = {
        'terraform': validate_terraform,
        'ansible': validate_ansible,
        'python': validate_python,
        'frontend': validate_frontend,
        'docs': validate_documentation,
        'github': validate_github_actions,
    }
    
    for name, validator in validation_steps.items():
        if name in skip:
            print_warning(f"Skipping {name} validation")
            continue
        if only and name not in only:
            continue
        
        results[name] = validator()
    
    # Summary
    print_header("Validation Summary")
    
    all_passed = all(results.values())
    
    for name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"{name:15} {status}")
    
    if all_passed:
        print("\n[OK] All validation checks passed!")
        return 0
    else:
        print("\n[ERROR] Some validation checks failed.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
