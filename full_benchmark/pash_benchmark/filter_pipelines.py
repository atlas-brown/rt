import os
import git
from tqdm import tqdm
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY, base_url="https://api.deepseek.com")
delimiter = " || "

def contains_pipe(text):
    return '|' in text

def clone_repo(github_url: str, local_path: str):
    try:
        if not os.path.exists(local_path):
            print(f"Cloning repository from {github_url} to {local_path}...")
            git.Repo.clone_from(github_url, local_path)
        else:
            print(f"Repository already exists at {local_path}.")
    except git.exc.GitCommandError as e:
        print(f"Error cloning repo {github_url}: {e}")

def find_pipelines_llm(content: str):
    system_prompt = f"""Identify all shell pipelines (commands connected by '|') in the given shell script content.
    Return each pipeline separated by '{delimiter}' if there are multiple pipelines, without any extra text."""
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
        max_tokens=1000,
        temperature=0,
        stream=False,
    )
    return response.choices[0].message.content.strip()

def locate_pipeline_in_file(pipeline: str, content: list[str]):
    # TODO: fix it
    for line_number, line in enumerate(content, start=1):
        if pipeline in line:
            return line_number
    return None

def process_repo_pipelines(local_path: str):
    pipeline_matches = []
    
    shell_files = []
    for root, dirs, files in os.walk(local_path):
        for file in files:
            if file.endswith(('.sh', '.bash', '.zsh')):
                shell_files.append(os.path.join(root, file))

    for file_path in tqdm(shell_files, desc="LLM Filtering Progress"):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.readlines()
            shell_script = ''.join(content)
            
            pipelines = find_pipelines_llm(shell_script)
            
            if pipelines:
                pipeline_list = pipelines.split(delimiter)
                for pipeline in pipeline_list:
                    if contains_pipe(pipeline):
                        line_number = locate_pipeline_in_file(pipeline, content)
                        if line_number:
                            pipeline_matches.append({
                                "file": file_path,
                                "line_number": line_number,
                                "line": pipeline.strip()
                            })

    return pipeline_matches

def main():
    repo_url = "https://github.com/binpash/benchmarks"
    local_path = os.path.dirname(os.path.abspath(__file__))

    clone_repo(repo_url, local_path)

    print("\nSearching for pipelines...")
    pipelines = process_repo_pipelines(local_path)

    output_dir = os.path.join(local_path, "pipelines")
    os.makedirs(output_dir, exist_ok=True)

    if pipelines:
        print(f"Found {len(pipelines)} pipeline(s):")
        for i, match in enumerate(pipelines):
            print(f"{match['file']} (Line {match['line_number']}): {match['line']}")
            
            filename = f"pash_{i + 1}.sh"
            filepath = os.path.join(output_dir, filename)
            
            try:
                with open(filepath, 'w') as f:
                    f.write(f"# Source: {match['file']}\n")
                    f.write(f"# Line: {match['line_number']}\n\n")
                    f.write(f"{match['line']}\n")
                print(f"Saved to {filepath}")
            except IOError as e:
                print(f"Error saving pipeline to {filepath}: {e}")
    else:
        print("No pipelines found.")

if __name__ == "__main__":
    main()
