import subprocess
import os
import json
import boto3
import shutil

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
    # ssh_log_file = "/tmp/analyzer/ssh_logs.json"
    # ssh_log_command = f"journalctl -u ssh -o json > {ssh_log_file}"
    # subprocess.run(ssh_log_command, shell=True, check=True)

    # Export error logs (priority err, crit, alert, and emerg)
    error_log_file = "/tmp/analyzer/error_logs.json"
    error_log_command = f"journalctl -p err > {error_log_file}"
    subprocess.run(error_log_command, shell=True, check=True)

    print("Logs exported successfully to /tmp/analyzer/")

    # Send logs to Claude Sonnet on Amazon Bedrock
    # send_to_claude(ssh_log_file, "SSH Log")
    send_to_claude(error_log_file, "Error Log")

def remove_tmp_dir():
    tmp_dir = "/tmp/analyzer"
    if os.path.exists(tmp_dir):
        try:
            shutil.rmtree(tmp_dir)
            print(f"Removed {tmp_dir} directory.")
        except Exception as e:
            print(f"Error removing {tmp_dir} directory: {e}")
    else:
        print(f"{tmp_dir} directory does not exist.")


def send_to_claude(log_file, log_type):
    # Initialize Bedrock client
    bedrock = boto3.client('bedrock-runtime', "us-east-1")

    # Read the log file
    with open(log_file, 'r') as file:
        log_content = file.read()

    # Prepare the prompt    
    #prompt = f"Human: The following is a linux {log_type}. Analyze this log and provide any helpful troubleshooting tips for any issues that are found:\n\n{log_content}\n Assistant: "
    messages = [
        {
            "role": "user",
            "content": f"Human: Analyze this log and provide any helpful troubleshooting tips for any issues that are found. Dont report on anything that is harmless and can be ignored. Only report on actionable items that are a priority for troubleshooting.:\n\n{log_content}\n Assistant: "
        }
    ]

    # Prepare the request body
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "messages": messages,
        "temperature": 0.0,
        "top_p": 0.5,
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
    print(f"\n===== {log_type} Analysis =====")
    if 'content' in response_body and len(response_body['content']) > 0:
        print(response_body['content'][0]['text'])
    else:
        print("No content found in the response.")

if __name__ == "__main__":
    check_journalctl_and_export_logs()
    remove_tmp_dir()