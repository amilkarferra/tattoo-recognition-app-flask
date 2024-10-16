import os
import subprocess
import shutil

def recreate_github_repo():
    try:
        # Get the GitHub token from environment variables
        github_token = os.environ.get('GITHUB_TOKEN')
        if not github_token:
            raise ValueError("GitHub token not found in environment variables")

        # Set up the repository information
        repo_name = "tattoo-recognition-app-flask"
        remote_url = f"https://{github_token}@github.com/amilkarferra/{repo_name}.git"

        # Create a temporary directory for the new repository
        temp_dir = "temp_repo"
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        os.chdir(temp_dir)

        # Initialize a new Git repository
        subprocess.run(["git", "init"], check=True)

        # Copy all files except the sensitive ones to the new repository
        excluded_files = [".git", "macro-plate-355517-55057e047a57.json", "sensitive-data.txt", ".cache"]
        for item in os.listdir(".."):
            if item not in excluded_files:
                if os.path.isdir(os.path.join("..", item)):
                    shutil.copytree(os.path.join("..", item), item, ignore=shutil.ignore_patterns(*excluded_files))
                else:
                    shutil.copy2(os.path.join("..", item), ".")

        # Add all files to the new repository
        subprocess.run(["git", "add", "."], check=True)

        # Commit the changes
        subprocess.run(["git", "commit", "-m", "Initial commit: Recreate Tattoo Recognition App"], check=True)

        # Add the remote origin
        subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)

        # Force push to the main branch
        subprocess.run(["git", "push", "-f", "origin", "main"], check=True)

        print("Repository recreated and pushed to GitHub successfully")

        # Clean up: remove the temporary directory
        os.chdir("..")
        shutil.rmtree(temp_dir)

    except subprocess.CalledProcessError as e:
        print(f"Error during Git operations: {e}")
    except ValueError as e:
        print(f"Error: {e}")
    except OSError as e:
        print(f"OS error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Ensure we're back in the original directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    recreate_github_repo()
