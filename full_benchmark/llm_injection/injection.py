import os
from openai import OpenAI
from pathlib import Path
from tqdm import tqdm

class PipelineModifier:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
    def extract_pipelines(self, content):
        lines = content.split('\n')
        pipelines = []
        for i, line in enumerate(lines, 1):
            if '|' in line and not line.strip().startswith('#'):
                pipelines.append((line.strip(), i))
        return pipelines

    def modify_pipeline(self, pipeline):
        system_prompt = """Given a shell pipeline, introduce a composition mistake that can be detected through syntactic analysis by modifying flags, options, or arguments. Also provide a brief explanation of why this modification causes a type/format mismatch. Respond in format:
        PIPELINE: <modified_pipeline>
        EXPLAIN: <explanation>
        
        If you cannot introduce a syntactically detectable composition error, return "SKIP".

        Examples:
        Input: grep -oE [0-9A-Z]+ file.txt | sort
        Output: 
        PIPELINE: grep -oE [A-Z]+ file.txt | sort -n
        EXPLAIN: grep now only outputs letters but sort -n expects numbers, causing type mismatch

        Input: cat file.txt | sort | uniq -c | sort -n
        Output: 
        PIPELINE: cat file.txt | sort | uniq | sort -n
        EXPLAIN: Removed -c flag from uniq means output will not start with counts, making sort -n expect numeric prefix that doesn't exist

        Input: cat file.txt | wc -l
        Output: SKIP"""
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Original pipeline: {pipeline}"}
                ],
                temperature=0,
                max_tokens=100
            )
            result = response.choices[0].message.content.strip()
            if result == "SKIP":
                return "SKIP", ""
            
            lines = result.split('\n')
            if len(lines) >= 2:
                pipeline = lines[0].replace('PIPELINE:', '').strip()
                explanation = lines[1].replace('EXPLAIN:', '').strip()
                return pipeline, explanation
            return "SKIP", ""
        except Exception as e:
            return "SKIP", ""

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

if __name__ == "__main__":
    main()