import subprocess
import os
import json
import boto3

def check_journalctl_and_export_logs():
    # Check if journalctl exists
    try:
        subprocess.run(["which", "journalctl"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("journalctl is not installed on this system.")
        return

    # Create the /tmp/analyzer directory if it doesn't exist
    os.makedirs("/tmp/analyzer", exist_ok=True)

    # Export SSH logs
    ssh_log_file = "/tmp/analyzer/ssh_logs.json"
    ssh_log_command = f"journalctl -u ssh -o json > {ssh_log_file}"
    subprocess.run(ssh_log_command, shell=True, check=True)

    # Export error logs (priority err, crit, alert, and emerg)
    error_log_file = "/tmp/analyzer/error_logs.json"
    error_log_command = f"journalctl -p err..emerg -o json > {error_log_file}"
    subprocess.run(error_log_command, shell=True, check=True)

    print("Logs exported successfully to /tmp/analyzer/")

    # Send logs to Claude Sonnet on Amazon Bedrock
    send_to_claude(ssh_log_file, "SSH Log")
    send_to_claude(error_log_file, "Error Log")

def send_to_claude(log_file, log_type):
    # Initialize Bedrock client
    bedrock = boto3.client('bedrock-runtime', "us-east-1")

    # Read the log file
    with open(log_file, 'r') as file:
        log_content = file.read()

    # Prepare the prompt
    prompt = f"The following is a linux {log_type}. Analyze this log and provide any helpful troubleshooting tips for any issues that are found:\n\n{log_content}"

    # Prepare the request body
    body = json.dumps({
        "prompt": prompt,
        "max_tokens_to_sample": 4096,
        "temperature": 0.5,
        "top_p": 0.9,
    })

    # Send request to Claude Sonnet
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        contentType='application/json',
        accept='application/json',
        body=body
    )

    # Parse and print the response
    response_body = json.loads(response['body'].read())
    print(f"\nClaude's analysis of {log_type}:")
    print(response_body['completion'])

if __name__ == "__main__":
    check_journalctl_and_export_logs()