import os
from typing import Tuple
from openai import OpenAI
from pathlib import Path
from tqdm import tqdm

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# class PipelineModifier:
#     def __init__(self, api_key):
#         self.client = OpenAI(api_key=api_key)
        
#     def extract_pipelines(self, content):
#         lines = content.split('\n')
#         pipelines = []
#         for i, line in enumerate(lines, 1):
#             if '|' in line and not line.strip().startswith('#'):
#                 pipelines.append((line.strip(), i))
#         return pipelines

#     def process_file(self, file_path):
#         with open(file_path, 'r') as f:
#             content = f.read()
            
#         pipelines = self.extract_pipelines(content)
#         modified_lines = []
#         for original_pipeline, _ in pipelines:
#             modified_pipeline, explanation = self.modify_pipeline(original_pipeline)
#             if modified_pipeline != "SKIP" and modified_pipeline != original_pipeline:
#                 print(f"\nOriginal: {original_pipeline}")
#                 print(f"Modified: {modified_pipeline}")
#                 print(f"Explanation: {explanation}")
#                 print("-" * 80)
#                 modified_lines.append(f"# Original: {original_pipeline}")
#                 modified_lines.append(f"# Error: {explanation}")
#                 modified_lines.append(modified_pipeline)
#                 modified_lines.append("")
#         return modified_lines if modified_lines else None

#     def process_directory(self, src_dir, dest_dir):
#         src_path = Path(src_dir)
#         dest_path = Path(dest_dir)
        
#         files = []
#         for root, _, filenames in os.walk(src_path):
#             for file in filenames:
#                 if file.endswith('.sh'):
#                     rel_path = Path(root).relative_to(src_path)
#                     files.append((rel_path / file, Path(file)))
        
#         for rel_path, file_name in tqdm(files, desc="Processing files"):
#             input_file = src_path / rel_path
#             output_dir = dest_path / rel_path.parent
#             output_dir.mkdir(parents=True, exist_ok=True)
            
#             modified_lines = self.process_file(input_file)
#             if modified_lines:
#                 output_file = output_dir / file_name
#                 with open(output_file, 'w') as f:
#                     f.write('\n'.join(modified_lines))

# def main():
#     OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
#     modifier = PipelineModifier(OPENAI_API_KEY)
    
#     script_dir = Path(__file__).parent
#     src_dir = script_dir / 'correct_pipelines'
#     dest_dir = script_dir / 'injected_pipelines'
    
#     modifier.process_directory(src_dir, dest_dir)


def generate_pipelines():
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
    #     The pipelines should contain the **commonly-made** mistakes where the output of one stage of the pipeline is not compatible with the format of the next stage.
    #     * The mistake of each pipeline should be unique.

    system_prompt = """
    ## Task
    Please give me 30 buggy Unix pipelines using any combinations of following commands: cat, grep, sort, cut, tr, uniq, wc, xargs, find, sed, seq, ls. Each command can be used multiple times in a single pipeline. Also provide a brief explanation of it. You need to strictly follow the requirements mentioned below.

    ## Requirements
    * No 'echo' or 'xargs echo'.
    * Each pipeline should contain at least 8 stages.
    * No simple mistakes like omitting patterns for 'grep' or commands for 'xargs'. 
    * No mistakes relared to file not found
    * No similar pipelines.
    * The mistakes should be diverse.
    * You may use multiple 'tr', 'sed', 'cut' and 'grep' commands in a single pipeline.

    ## Response format
    Respond in format (repeat for each pipeline):  
    ``sh
    # <number>.
    # EXPLAIN: <explanation>
    <pipeline>
    ``
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
        return result
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

def inject_pipelines(pipelines, explanations):
    system_prompt = """
    ## Task
    Your task is injecting the mistake mentioned in the explanation in the given pipeline. If the given pipeline already has the mistake, keep the pipeline as it is. You are not allowed to use 'awk' command when injecting the mistake. The changes should be as minimal as possible.

    ## Input format
    EXPLAIN: <explanation>
    ORIGINAL: <original_pipeline>

    ## Response format:  
    PIPELINE: <injected_pipeline> || <original_pipeline>
    """
    for pipeline, explanation in zip(pipelines, explanations):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"EXPLAIN: {explanation}\nORIGINAL: {pipeline}"}
                ],
                temperature=0,
                # max_tokens=100
            )
            result = response.choices[0].message.content.strip()
            print()
            print('EXPLAIN:', explanation)
            print('ORIGINAL:', pipeline)
            print(result)
            # return result
        except Exception as e:
            print(e)

def filter_pipelines_and_explanations(llm_output) -> Tuple[list, list]:
    pipelines = []
    explanations = []
    lines = llm_output.split('\n')
    for line in lines:
        if line.startswith("PIPELINE:"):
            pipelines.append(line.replace("PIPELINE:", "").strip())
        if line.startswith("EXPLAIN:"):
            explanations.append(line.replace("EXPLAIN:", "").strip())
    return pipelines, explanations


if __name__ == "__main__":
    llm_output = generate_pipelines()
    pipelines, explanations = filter_pipelines_and_explanations(llm_output)
    inject_pipelines(pipelines, explanations)
