from pathlib import Path
import subprocess

def subproccess_wrapper(command_list, capture_output = True, text = True, check = True):

    try:
        result = subprocess.run(
            command_list,
            capture_output=capture_output,
            text=text,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code: {e.returncode}")
        print(f"Error message:\n{e.stderr}")

class FileWriter:
    """Write text contents out to text files in configured directory"""
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
    def write(self, filename, content):
        with open(self.directory / filename, "w") as f:
            f.write(content)

class StdoutWriter:
    """Write text contents to stdout, typically for a test run of the script"""
    def write(self, filename, content):
        print(f"===== {filename} =====")
        print(content, end="")