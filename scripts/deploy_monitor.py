#!/usr/bin/env python3
import re
import subprocess
import sys
from collections import Counter


class DeploymentMonitor:
    def __init__(self):
        self.error_count = Counter()
        self.max_retries = 3

    def analyze_line(self, line):
        triggers = {
            "missing_dep": r"(command not found|No such file|not found|unable to locate package)",
            "permission": r"(Permission denied|Operation not permitted)",
            "network": r"(Connection refused|Could not resolve|Temporary failure)",
            "python_error": r"(Traceback|Exception|Error:)",
        }
        for error_type, pattern in triggers.items():
            if re.search(pattern, line, re.IGNORECASE):
                return error_type, line
        return None, None

    def remediate(self, error_type, context, ssh_cmd):
        if error_type == "missing_dep":
            return f'{ssh_cmd} "sudo apt-get update && sudo apt-get install -y build-essential"'
        elif error_type == "permission":
            return f'{ssh_cmd} "sudo chmod -R 755 ~/deployment"'
        return None

    def monitor(self, cmd):
        proc = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        for line in proc.stdout:
            print(line, end="")
            error_type, context = self.analyze_line(line)
            if error_type:
                self.error_count[error_type] += 1
                if self.error_count[error_type] >= self.max_retries:
                    print(f"\nCRITICAL: {error_type} occurred {self.max_retries} times. Aborting.")
                    proc.kill()
                    return False
        proc.wait()
        return proc.returncode == 0


if __name__ == "__main__":
    monitor = DeploymentMonitor()
    success = monitor.monitor("./autonomous_deploy.sh")
    sys.exit(0 if success else 1)
