import subprocess
import sys

def print_colored(text, color):
    """Print text in the specified color."""
    colors = {
        'red': '\033[91m',
        'blue': '\033[94m',
        'reset': '\033[0m'
    }
    print(f"{colors[color]}{text}{colors['reset']}")


def run_process(path, args=[]):
    """Run a Python script and return the process object."""
    command = ['python', '-u', path] + args
    return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

if __name__ == "__main__":
    flask_webapp_args = []
    if len(sys.argv) > 1:
        flask_webapp_args = sys.argv[1:]
            
    # Define the paths to your Flask app and server.py
    flask_webapp_path = './webapp/webapp_coffee.py'
    coffeepot_server_path = './server/server_pot.py'

    # Start both processes
    flask_webapp_process = run_process(flask_webapp_path, flask_webapp_args)
    coffeepot_server_process = run_process(coffeepot_server_path)

    try:
        # Continuously check the output of each process
        while True:
            # Read a line of output from each process
            flask_output = flask_webapp_process.stdout.readline()
            server_output = coffeepot_server_process.stdout.readline()

            if flask_output:
                print_colored(f"Flask Webapp: {flask_output.strip()}", 'blue')
            if server_output:
                print_colored(f"Coffeepot Server: {server_output.strip()}", 'red')

            # Break the loop if both processes have terminated
            if flask_output == '' and server_output == '' and flask_webapp_process.poll() is not None and coffeepot_server_process.poll() is not None:
                break
    except KeyboardInterrupt:
        # Terminate the processes if the script is interrupted
        flask_webapp_process.terminate()
        coffeepot_server_process.terminate()
        print("Processes terminated by user.")
