"""
Advanced Git Operations Module for TinyCode
Provides comprehensive git integration beyond basic operations
"""

import subprocess
import json
import os
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
from enum import Enum
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()

class GitStatus(Enum):
    """Git file status types"""
    MODIFIED = "M"
    ADDED = "A"
    DELETED = "D"
    RENAMED = "R"
    COPIED = "C"
    UNMERGED = "U"
    UNTRACKED = "??"
    IGNORED = "!!"

@dataclass
class GitFileStatus:
    """Represents the status of a single file in git"""
    path: str
    status: GitStatus
    staged: bool
    unstaged: bool

@dataclass
class GitCommit:
    """Represents a git commit"""
    hash: str
    author: str
    email: str
    date: datetime
    message: str
    files_changed: int
    insertions: int
    deletions: int

@dataclass
class GitBranch:
    """Represents a git branch"""
    name: str
    is_current: bool
    is_remote: bool
    last_commit: str
    last_commit_date: datetime
    ahead: int = 0
    behind: int = 0

@dataclass
class GitRemote:
    """Represents a git remote"""
    name: str
    url: str
    fetch_url: str
    push_url: str

@dataclass
class GitStash:
    """Represents a git stash entry"""
    index: int
    message: str
    branch: str
    date: datetime

class GitOperations:
    """Advanced Git operations with safety features and rich output"""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self._ensure_git_repo()

    def _ensure_git_repo(self):
        """Ensure we're in a git repository"""
        try:
            self._run_git_command(["rev-parse", "--git-dir"])
        except subprocess.CalledProcessError:
            raise ValueError(f"Not a git repository: {self.repo_path}")

    def _run_git_command(self, args: List[str], capture_output: bool = True,
                        cwd: Optional[str] = None) -> subprocess.CompletedProcess:
        """Run a git command with error handling"""
        cmd = ["git"] + args
        cwd = cwd or str(self.repo_path)

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=capture_output,
                text=True,
                check=True
            )
            return result
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Git command failed: {' '.join(cmd)}[/red]")
            console.print(f"[red]Error: {e.stderr}[/red]")
            raise

    def get_status(self) -> List[GitFileStatus]:
        """Get detailed git status"""
        result = self._run_git_command(["status", "--porcelain=v1"])

        files = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue

            status_code = line[:2]
            file_path = line[3:]

            # Parse status codes
            staged = status_code[0] != ' ' and status_code[0] != '?'
            unstaged = status_code[1] != ' '

            # Map status code to enum
            if status_code.startswith('??'):
                status = GitStatus.UNTRACKED
            elif status_code.startswith('!!'):
                status = GitStatus.IGNORED
            else:
                status_char = status_code[0] if staged else status_code[1]
                status = GitStatus(status_char) if status_char in [e.value for e in GitStatus] else GitStatus.MODIFIED

            files.append(GitFileStatus(
                path=file_path,
                status=status,
                staged=staged,
                unstaged=unstaged
            ))

        return files

    def get_commits(self, limit: int = 20, branch: Optional[str] = None,
                   since: Optional[str] = None) -> List[GitCommit]:
        """Get commit history with detailed information"""
        args = ["log", f"--max-count={limit}", "--pretty=format:%H|%an|%ae|%at|%s", "--numstat"]

        if branch:
            args.append(branch)
        if since:
            args.extend(["--since", since])

        result = self._run_git_command(args)

        commits = []
        current_commit = None

        for line in result.stdout.split('\n'):
            if not line.strip():
                continue

            if '|' in line and len(line.split('|')) == 5:
                # Commit header line
                if current_commit:
                    commits.append(current_commit)

                parts = line.split('|')
                current_commit = GitCommit(
                    hash=parts[0],
                    author=parts[1],
                    email=parts[2],
                    date=datetime.fromtimestamp(int(parts[3])),
                    message=parts[4],
                    files_changed=0,
                    insertions=0,
                    deletions=0
                )
            elif current_commit and '\t' in line:
                # File change line (insertions, deletions, filename)
                parts = line.split('\t')
                if len(parts) >= 2:
                    try:
                        insertions = int(parts[0]) if parts[0] != '-' else 0
                        deletions = int(parts[1]) if parts[1] != '-' else 0
                        current_commit.insertions += insertions
                        current_commit.deletions += deletions
                        current_commit.files_changed += 1
                    except ValueError:
                        pass

        if current_commit:
            commits.append(current_commit)

        return commits

    def get_branches(self, include_remote: bool = True) -> List[GitBranch]:
        """Get all branches with tracking information"""
        args = ["branch", "-v"]
        if include_remote:
            args.append("-a")

        result = self._run_git_command(args)

        branches = []
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue

            is_current = line.startswith('*')
            line = line[2:] if is_current else line[2:]

            parts = line.split()
            if len(parts) < 2:
                continue

            name = parts[0]
            is_remote = name.startswith('remotes/')

            # Get last commit info
            last_commit = parts[1]

            # Try to get commit date
            try:
                if last_commit and last_commit != '->' and not last_commit.startswith('('):
                    commit_result = self._run_git_command(["show", "-s", "--format=%at", last_commit])
                    last_commit_date = datetime.fromtimestamp(int(commit_result.stdout.strip()))
                else:
                    last_commit_date = datetime.now()
            except:
                last_commit_date = datetime.now()

            # Get ahead/behind info for current branch
            ahead, behind = 0, 0
            if is_current and not is_remote:
                try:
                    tracking_result = self._run_git_command(["status", "-b", "--porcelain=v1"])
                    first_line = tracking_result.stdout.split('\n')[0]
                    if 'ahead' in first_line:
                        ahead = int(first_line.split('ahead ')[1].split(']')[0].split(',')[0])
                    if 'behind' in first_line:
                        behind = int(first_line.split('behind ')[1].split(']')[0].split(',')[0])
                except:
                    pass

            branches.append(GitBranch(
                name=name,
                is_current=is_current,
                is_remote=is_remote,
                last_commit=last_commit,
                last_commit_date=last_commit_date,
                ahead=ahead,
                behind=behind
            ))

        return branches

    def get_remotes(self) -> List[GitRemote]:
        """Get all remote repositories"""
        result = self._run_git_command(["remote", "-v"])

        remotes_dict = {}
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue

            parts = line.split()
            if len(parts) >= 3:
                name, url, operation = parts[0], parts[1], parts[2].strip('()')

                if name not in remotes_dict:
                    remotes_dict[name] = {
                        'name': name,
                        'url': url,
                        'fetch_url': url,
                        'push_url': url
                    }

                if operation == 'fetch':
                    remotes_dict[name]['fetch_url'] = url
                elif operation == 'push':
                    remotes_dict[name]['push_url'] = url

        return [GitRemote(**remote) for remote in remotes_dict.values()]

    def get_stashes(self) -> List[GitStash]:
        """Get all stash entries"""
        try:
            result = self._run_git_command(["stash", "list", "--format=%gd|%gs|%gD|%at"])
        except subprocess.CalledProcessError:
            return []  # No stashes

        stashes = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue

            parts = line.split('|')
            if len(parts) >= 4:
                index_str = parts[0].strip('stash@{}')
                try:
                    index = int(index_str)
                    message = parts[1]
                    branch = parts[2].split(': ')[1] if ': ' in parts[2] else 'unknown'
                    date = datetime.fromtimestamp(int(parts[3]))

                    stashes.append(GitStash(
                        index=index,
                        message=message,
                        branch=branch,
                        date=date
                    ))
                except (ValueError, IndexError):
                    continue

        return stashes

    def create_branch(self, name: str, from_branch: Optional[str] = None,
                     checkout: bool = True) -> bool:
        """Create a new branch"""
        try:
            args = ["branch", name]
            if from_branch:
                args.append(from_branch)

            self._run_git_command(args)

            if checkout:
                self._run_git_command(["checkout", name])

            console.print(f"[green]Created branch '{name}'[/green]")
            return True
        except subprocess.CalledProcessError:
            return False

    def switch_branch(self, name: str) -> bool:
        """Switch to a different branch"""
        try:
            self._run_git_command(["checkout", name])
            console.print(f"[green]Switched to branch '{name}'[/green]")
            return True
        except subprocess.CalledProcessError:
            return False

    def delete_branch(self, name: str, force: bool = False) -> bool:
        """Delete a branch"""
        try:
            args = ["branch", "-D" if force else "-d", name]
            self._run_git_command(args)
            console.print(f"[green]Deleted branch '{name}'[/green]")
            return True
        except subprocess.CalledProcessError:
            return False

    def stage_files(self, files: List[str]) -> bool:
        """Stage files for commit"""
        try:
            self._run_git_command(["add"] + files)
            console.print(f"[green]Staged {len(files)} files[/green]")
            return True
        except subprocess.CalledProcessError:
            return False

    def unstage_files(self, files: List[str]) -> bool:
        """Unstage files"""
        try:
            self._run_git_command(["reset", "HEAD"] + files)
            console.print(f"[green]Unstaged {len(files)} files[/green]")
            return True
        except subprocess.CalledProcessError:
            return False

    def commit(self, message: str, all_files: bool = False) -> bool:
        """Create a commit"""
        try:
            args = ["commit", "-m", message]
            if all_files:
                args.append("-a")

            result = self._run_git_command(args)
            console.print(f"[green]Created commit: {message}[/green]")
            return True
        except subprocess.CalledProcessError:
            return False

    def push(self, remote: str = "origin", branch: Optional[str] = None,
            set_upstream: bool = False) -> bool:
        """Push changes to remote"""
        try:
            args = ["push"]
            if set_upstream:
                args.extend(["-u", remote, branch or "HEAD"])
            else:
                args.extend([remote, branch or "HEAD"])

            self._run_git_command(args)
            console.print(f"[green]Pushed to {remote}[/green]")
            return True
        except subprocess.CalledProcessError:
            return False

    def pull(self, remote: str = "origin", branch: Optional[str] = None) -> bool:
        """Pull changes from remote"""
        try:
            args = ["pull", remote]
            if branch:
                args.append(branch)

            self._run_git_command(args)
            console.print(f"[green]Pulled from {remote}[/green]")
            return True
        except subprocess.CalledProcessError:
            return False

    def create_stash(self, message: Optional[str] = None, include_untracked: bool = False) -> bool:
        """Create a stash"""
        try:
            args = ["stash", "push"]
            if include_untracked:
                args.append("-u")
            if message:
                args.extend(["-m", message])

            self._run_git_command(args)
            console.print("[green]Created stash[/green]")
            return True
        except subprocess.CalledProcessError:
            return False

    def apply_stash(self, stash_index: int = 0) -> bool:
        """Apply a stash"""
        try:
            self._run_git_command(["stash", "apply", f"stash@{{{stash_index}}}"])
            console.print(f"[green]Applied stash@{{{stash_index}}}[/green]")
            return True
        except subprocess.CalledProcessError:
            return False

    def drop_stash(self, stash_index: int = 0) -> bool:
        """Drop a stash"""
        try:
            self._run_git_command(["stash", "drop", f"stash@{{{stash_index}}}"])
            console.print(f"[green]Dropped stash@{{{stash_index}}}[/green]")
            return True
        except subprocess.CalledProcessError:
            return False

    def get_diff(self, staged: bool = False, file_path: Optional[str] = None) -> str:
        """Get diff output"""
        try:
            args = ["diff"]
            if staged:
                args.append("--staged")
            if file_path:
                args.append(file_path)

            result = self._run_git_command(args)
            return result.stdout
        except subprocess.CalledProcessError:
            return ""

    def get_repository_info(self) -> Dict[str, Any]:
        """Get comprehensive repository information"""
        try:
            # Get basic info
            current_branch = self._run_git_command(["branch", "--show-current"]).stdout.strip()
            remote_url = ""
            try:
                remote_url = self._run_git_command(["remote", "get-url", "origin"]).stdout.strip()
            except:
                pass

            # Get commit count
            commit_count = 0
            try:
                commit_count = int(self._run_git_command(["rev-list", "--count", "HEAD"]).stdout.strip())
            except:
                pass

            # Get repository size
            repo_size = 0
            try:
                git_dir = self._run_git_command(["rev-parse", "--git-dir"]).stdout.strip()
                repo_size = sum(f.stat().st_size for f in Path(git_dir).rglob('*') if f.is_file())
            except:
                pass

            return {
                'path': str(self.repo_path),
                'current_branch': current_branch,
                'remote_url': remote_url,
                'commit_count': commit_count,
                'repo_size_bytes': repo_size,
                'branches': len(self.get_branches()),
                'remotes': len(self.get_remotes()),
                'stashes': len(self.get_stashes())
            }
        except:
            return {}

    def analyze_repository(self) -> Dict[str, Any]:
        """Perform comprehensive repository analysis"""
        analysis = {
            'info': self.get_repository_info(),
            'file_status': {},
            'commit_stats': {},
            'branch_analysis': {},
            'activity_metrics': {}
        }

        # Analyze file status
        status_files = self.get_status()
        analysis['file_status'] = {
            'total_files': len(status_files),
            'staged': sum(1 for f in status_files if f.staged),
            'unstaged': sum(1 for f in status_files if f.unstaged),
            'untracked': sum(1 for f in status_files if f.status == GitStatus.UNTRACKED),
            'by_status': {}
        }

        for status in GitStatus:
            count = sum(1 for f in status_files if f.status == status)
            if count > 0:
                analysis['file_status']['by_status'][status.value] = count

        # Analyze recent commits
        recent_commits = self.get_commits(limit=50)
        if recent_commits:
            total_insertions = sum(c.insertions for c in recent_commits)
            total_deletions = sum(c.deletions for c in recent_commits)
            total_files = sum(c.files_changed for c in recent_commits)

            analysis['commit_stats'] = {
                'recent_commits': len(recent_commits),
                'total_insertions': total_insertions,
                'total_deletions': total_deletions,
                'total_files_changed': total_files,
                'avg_files_per_commit': total_files / len(recent_commits) if recent_commits else 0,
                'most_active_author': max(recent_commits, key=lambda c: c.author).author if recent_commits else None
            }

        # Analyze branches
        branches = self.get_branches()
        local_branches = [b for b in branches if not b.is_remote]
        remote_branches = [b for b in branches if b.is_remote]

        analysis['branch_analysis'] = {
            'total_branches': len(branches),
            'local_branches': len(local_branches),
            'remote_branches': len(remote_branches),
            'current_branch': next((b.name for b in branches if b.is_current), 'unknown')
        }

        return analysis