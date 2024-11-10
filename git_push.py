import os
import subprocess

def run_git_command(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            env={**os.environ, "GIT_ASKPASS": "echo", "GIT_TERMINAL_PROMPT": "0"},
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False

# Configure Git
run_git_command('git config --global user.name "GitHub Actions"')
run_git_command('git config --global user.email "actions@github.com"')

# Setup credentials with token
github_token = os.environ.get('GITHUB_TOKEN')
if github_token:
    remote_url = f"https://{github_token}@github.com/RichardTheuws/business-club-management.git"
    run_git_command(f'git remote set-url origin "{remote_url}"')
    
# Add and commit changes
run_git_command('git add .')
run_git_command('git commit -m "Update: GitHub authentication and environment configuration"')

# Push changes
run_git_command('git push origin main')
