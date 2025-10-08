#!/usr/bin/env python3
"""
Deploy OmicsOracle to all GitHub remotes
"""

import subprocess
import sys
from typing import Optional, Tuple

# Account mapping for different remotes with SSH key configuration
REMOTE_ACCOUNTS = {
    "origin": {"username": "sdodlapati3", "ssh_host": "github.com"},
    "backup": {"username": "sdodlapa", "ssh_host": "github-sdodlapa"},
    "sanjeeva": {
        "username": "SanjeevaRDodlapati",
        "ssh_host": "github-sanjeeva",
    },
}


def run_command(command: str) -> Tuple[bool, str]:
    """Execute shell command and return success status and output"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
        return result.returncode == 0, result.stdout + result.stderr
    except (subprocess.SubprocessError, OSError) as e:
        return False, str(e)


def switch_github_account(account: str) -> bool:
    """Switch to the specified GitHub account using gh CLI"""
    print(f"  [AUTH] Switching to GitHub account: {account}")
    success, output = run_command(f"gh auth switch --user {account}")
    if not success:
        print(f"  [ERROR] Failed to switch to account {account}: {output}")
    return success


def get_current_branch() -> str:
    """Get the current git branch name"""
    success, output = run_command("git rev-parse --abbrev-ref HEAD")
    if success:
        return output.strip()
    return "main"


def update_remote_url(remote_name: str) -> bool:
    """Update the remote URL to use the correct SSH host for the account"""
    if remote_name not in REMOTE_ACCOUNTS:
        return True  # Use default if not configured

    ssh_host = REMOTE_ACCOUNTS[remote_name]["ssh_host"]
    username = REMOTE_ACCOUNTS[remote_name]["username"]

    # Get current remote URL
    success, current_url = run_command(f"git remote get-url {remote_name}")
    if not success:
        print(f"[ERROR] Failed to get URL for remote {remote_name}")
        return False

    current_url = current_url.strip()

    # Extract repository name from current URL
    if "github.com" in current_url:
        if current_url.startswith("git@"):
            # SSH format: git@github.com:owner/repo.git
            repo_part = current_url.split(":")[-1]
        else:
            # HTTPS format: https://github.com/owner/repo.git
            repo_part = "/".join(current_url.split("/")[-2:])

        # Construct new SSH URL with correct host
        new_url = f"git@{ssh_host}:{username}/{repo_part.split('/')[-1]}"

        # Update the remote URL
        success, output = run_command(f"git remote set-url {remote_name} {new_url}")
        if success:
            print(f"  [SSH] Updated {remote_name} URL to use {ssh_host}")
            return True
        else:
            print(f"  [ERROR] Failed to update {remote_name} URL: {output}")
            return False

    return True


def push_to_remote(remote_name: str, branch: Optional[str] = None) -> bool:
    """Push current branch to specified remote with proper SSH configuration"""
    if branch is None:
        branch = get_current_branch()

    print(f"[PUSH] Pushing to remote '{remote_name}' (branch: {branch})...")

    # Update remote URL to use correct SSH host
    if not update_remote_url(remote_name):
        return False

    # Switch to the appropriate GitHub account for this remote
    if remote_name in REMOTE_ACCOUNTS:
        account = REMOTE_ACCOUNTS[remote_name]["username"]
        if not switch_github_account(account):
            print(f"[WARN] Failed to switch account for " f"{remote_name}")
            # Continue anyway, SSH keys should handle authentication

    success, output = run_command(f"git push {remote_name} {branch}")

    if success:
        print(f"[SUCCESS] Successfully pushed to {remote_name}")
        return True
    else:
        # Check for authentication/permission errors
        if "Permission denied" in output or "403" in output:
            print(f"[SKIP] Skipping {remote_name}: Authentication required")
        else:
            print(f"[FAIL] Failed to push to {remote_name}: " f"{output}")
        return False


def push_to_all_remotes(branch: Optional[str] = None) -> None:
    """Push to all configured remotes"""
    # Get list of remotes
    success, output = run_command("git remote")
    if not success:
        print("[ERROR] Failed to get git remotes")
        sys.exit(1)

    remotes = [remote.strip() for remote in output.split("\n") if remote.strip()]

    if not remotes:
        print("[ERROR] No git remotes configured")
        sys.exit(1)

    print(f"[DEPLOY] Deploying OmicsOracle to " f"{len(remotes)} GitHub repositories...")
    print(f"[INFO] Configured remotes: {', '.join(remotes)}")

    current_branch = branch or get_current_branch()
    print(f"[INFO] Current branch: {current_branch}")

    # Check for uncommitted changes
    success, output = run_command("git status --porcelain")
    if success and output.strip():
        print("[WARN] Warning: You have uncommitted changes:")
        print(output)
        response = input("Continue anyway? (y/N): ")
        if response.lower() != "y":
            print("Deployment cancelled")
            return

    # Push to each remote
    results = []
    for remote in remotes:
        success = push_to_remote(remote, current_branch)
        results.append((remote, success))

    # Summary
    print("\n[DEPLOY] Deployment Summary:")
    print("=" * 50)

    successful = 0
    for remote, success in results:
        status = "[SUCCESS] SUCCESS" if success else "[FAIL] FAILED"
        print(f"{remote:12} | {status}")
        if success:
            successful += 1

    print("=" * 50)
    print(f"Total: {successful}/{len(remotes)} repositories updated successfully")

    if successful == len(remotes):
        print("[SUCCESS] All repositories updated successfully!")
        print("\n[INFO] Repository URLs:")
        for remote in remotes:
            success, url = run_command(f"git remote get-url {remote}")
            if success:
                print(f"  [URL] {remote}: {url.strip()}")
    else:
        print("[WARN] Some deployments failed. " "Check the output above for details.")


def main() -> None:
    """Main deployment function"""
    if len(sys.argv) > 1:
        branch = sys.argv[1]
        print(f"Deploying branch: {branch}")
        push_to_all_remotes(branch)
    else:
        push_to_all_remotes()


if __name__ == "__main__":
    main()
