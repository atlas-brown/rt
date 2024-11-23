import os
import subprocess
import logging

logging.basicConfig(filename='full_benchmark/pash_benchmark/error.log', level=logging.INFO)

def run_parser_on_scripts(directories):
    for directory in directories:
        for root, _, files in os.walk(directory):
            for filename in files:
                if filename.endswith(".sh"):
                    filepath = os.path.join(root, filename)
                    try:
                        logging.info(f"Processing {filepath}")
                        subprocess.run(['python3', 'full_benchmark/pash_benchmark/parser.py', filepath], check=True, env={**os.environ, 'PYTHONPATH': 'src'})
                    except subprocess.CalledProcessError as e:
                        logging.error(f"Error processing {filepath}: {e}")
                        os.remove(filepath)
                        logging.info(f"Deleted {filepath}")

if __name__ == "__main__":
    directories = [
        'full_benchmark/pash_benchmark/benchmarks',
    ]
    run_parser_on_scripts(directories)