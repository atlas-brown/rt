import os
from openai import OpenAI
from pathlib import Path
from tqdm import tqdm

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

class PipelineModifier:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        
    def extract_pipelines(self, content):
        lines = content.split('\n')
        pipelines = []
        for i, line in enumerate(lines, 1):
            if '|' in line and not line.strip().startswith('#'):
                pipelines.append((line.strip(), i))
        return pipelines

    def process_file(self, file_path):
        with open(file_path, 'r') as f:
            content = f.read()
            
        pipelines = self.extract_pipelines(content)
        modified_lines = []
        for original_pipeline, _ in pipelines:
            modified_pipeline, explanation = self.modify_pipeline(original_pipeline)
            if modified_pipeline != "SKIP" and modified_pipeline != original_pipeline:
                print(f"\nOriginal: {original_pipeline}")
                print(f"Modified: {modified_pipeline}")
                print(f"Explanation: {explanation}")
                print("-" * 80)
                modified_lines.append(f"# Original: {original_pipeline}")
                modified_lines.append(f"# Error: {explanation}")
                modified_lines.append(modified_pipeline)
                modified_lines.append("")
        return modified_lines if modified_lines else None

    def process_directory(self, src_dir, dest_dir):
        src_path = Path(src_dir)
        dest_path = Path(dest_dir)
        
        files = []
        for root, _, filenames in os.walk(src_path):
            for file in filenames:
                if file.endswith('.sh'):
                    rel_path = Path(root).relative_to(src_path)
                    files.append((rel_path / file, Path(file)))
        
        for rel_path, file_name in tqdm(files, desc="Processing files"):
            input_file = src_path / rel_path
            output_dir = dest_path / rel_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            modified_lines = self.process_file(input_file)
            if modified_lines:
                output_file = output_dir / file_name
                with open(output_file, 'w') as f:
                    f.write('\n'.join(modified_lines))

def main():
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    modifier = PipelineModifier(OPENAI_API_KEY)
    
    script_dir = Path(__file__).parent
    src_dir = script_dir / 'correct_pipelines'
    dest_dir = script_dir / 'injected_pipelines'
    
    modifier.process_directory(src_dir, dest_dir)


def modify_pipeline():
    # system_prompt = """
    #     Please give me 10 buggy Unix pipelines, each using combinations of these commands: 'cat', 'grep', 'sort', 'cut', 'tr', 'uniq', 'wc', 'xargs', 'find', 'sed', 'seq'.
    #     Requirements:

    #     1. Each pipeline must contain 5-10 commands.
    #     2. The pipelines should execute without generating standard error messages, but produce incorrect results.
    #     3. Focus on data flow incompatibility between pipeline stages, not simple mistakes like omitting patterns for 'grep' or commands for 'xargs'.
    #     4. You may start pipelines with 'cat file.txt' (you can assume the file format), but this is not required.

    #     Response format:
    #     EXPLAIN: <explanation>
    #     PIPELINE: <pipeline>
    # """
    #     The buggy pipelines should not generate any errors in standard error, but the behavior of the pipelines should be incorrect.
    #     The mistakes should be deterministic, i.e., the explanations should not contain 'may' or 'might'.
    #     Ensure the diversity, i.e., the pipelines and the mistakes should not be similar to each other.
    #     You are encouraged to try any combinations of flags and options for these commands, especially for grep.
    #     Remember a single number is suitable for text substitution, e.g., 'tr' and 'sed'.
    #     Remember 'tr' is used to substitude text in lines of text.
    #     Please **Do not focus on** the incompatible betweem a single number output and the expected input of the next stage.

    system_prompt = """Please give me 20 buggy Unix pipelines using any combinations of following commands: cat, grep, sort, cut, tr, uniq, wc, xargs, find, sed.
    Also provide a brief explanation of it.
    The pipelines should contain the commonly-made mistakes where the output of one stage of the pipeline is not compatible with the input of the next stage.
    Ensure no simple mistakes in a single stage like omitting patterns for 'grep' or commands for 'xargs', or meaningless combinations of 'xargs' and other commands.
    The mistakes should be deterministic, i.e., the explanations should not contain 'may' or 'might'.
    Ensure the diversity, i.e., the pipelines and the mistakes should not be similar to each other.
    Each pipeline should contain at least 6 stages.
    
    Respond in format (repeat for each pipeline):
    <number>.
    EXPLAIN: <explanation>
    PIPELINE: <pipeline>
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt}
                # {"role": "user", "content": f"Original pipeline: {pipeline}"}
            ],
            temperature=0,
            # max_tokens=100
        )
        result = response.choices[0].message.content.strip()
        print(system_prompt)
        print("-" * 80)
        print(result)
        # if result == "SKIP":
        #     return "SKIP", ""
        
        # lines = result.split('\n')
        # if len(lines) >= 2:
        #     pipeline = lines[0].replace('PIPELINE:', '').strip()
        #     explanation = lines[1].replace('EXPLAIN:', '').strip()
        #     return pipeline, explanation
        # return "SKIP", ""
    except Exception as e:
        # return "SKIP", ""
        print(e)


if __name__ == "__main__":
    # main()
    modify_pipeline()
