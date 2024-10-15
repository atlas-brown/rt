import json
import os
from typing import List
from stream.command_signature import CommandSignature

class SignatureLoader:
    def __init__(self, signature_dir : str = "./src/stream/signatures") -> None:
        self.signature_dir = signature_dir
        self.signatures = self.load_all_signatures()

    def load_signature(self, command_name: str) -> CommandSignature:
        file_path = os.path.join(self.signature_dir, f'{command_name}.json')
        with open(file_path, 'r') as f:
            data = json.load(f)
        return CommandSignature(
            command_name=data['command_name'],
            default_input_type=data['default_input_type'],
            default_output_type=data['default_output_type'],
            args=data.get('args', []),
            flags=data.get('flags', []),
            rules=data.get('rules', [])
        )

    def load_all_signatures(self) -> List[CommandSignature]:
        signatures: List[CommandSignature] = []
        for file_name in os.listdir(self.signature_dir):
            if file_name.endswith('.json'):
                command_name = os.path.splitext(file_name)[0]
                signatures.append(self.load_signature(command_name))
        return signatures
