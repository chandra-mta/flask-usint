from pathlib import Path
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