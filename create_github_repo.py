import subprocess
import os

def push_to_github():
    try:
        # Initialize git if not already initialized
        if not os.path.exists('.git'):
            subprocess.run(["git", "init"], check=True)

        # Add all files
        subprocess.run(["git", "add", "."], check=True)

        # Commit the changes
        subprocess.run(["git", "commit", "-m", "Update: Tattoo Recognition App"], check=True)

        # Set the remote origin to the existing repository
        github_token = os.environ.get('GITHUB_TOKEN')
        if not github_token:
            raise ValueError("GitHub token not found in environment variables")

        remote_url = f"https://{github_token}@github.com/amilkarferra/tattoo-recognition-app-flask.git"
        subprocess.run(["git", "remote", "remove", "origin"], check=False)  # Remove existing origin if it exists
        subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)

        # Push the code to the main branch
        subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
        print("Code pushed to GitHub successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error during Git operations: {e}")
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    push_to_github()
