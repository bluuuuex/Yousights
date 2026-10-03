"""Deploy legacy services using a preinstalled IBM Cloud CLI."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import shutil
import subprocess


def execute_command(arguments, cwd=None):
    # Login arguments and output can contain secrets; do not log them.
    result = subprocess.run(arguments, cwd=cwd, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError("IBM Cloud command failed with exit code %d" % result.returncode)


def main():
    parser = argparse.ArgumentParser(description="IBM Cloud application deployment")
    parser.add_argument("-apiKey", default=os.environ.get("IBM_CLOUD_API_KEY"))
    args = parser.parse_args()
    if not args.apiKey:
        parser.error("Set IBM_CLOUD_API_KEY or supply -apiKey")
    organization = os.environ.get("IBM_CLOUD_ORG")
    if not organization:
        parser.error("Set IBM_CLOUD_ORG")
    if not shutil.which("ibmcloud"):
        parser.error("Install the IBM Cloud CLI before deploying")
    execute_command(["ibmcloud", "api", "https://api.eu-gb.bluemix.net"])
    execute_command(["ibmcloud", "login", "--apikey", args.apiKey, "-o", organization,
                     "-s", os.environ.get("IBM_CLOUD_SPACE", "dev")])
    root = Path(__file__).resolve().parent
    def deploy(service):
        command = ["ibmcloud", "app", "push"]
        if service == "analyticsAI":
            command += ["-k", "2GB"]
        execute_command(command, cwd=str(root / service))
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(deploy, ["yousights-fe", "eventsAPI", "youtubeData", "analyticsAI"]))


if __name__ == "__main__" and os.environ.get("MERGE_PULL_REQUEST", "").lower() == "true":
    main()
