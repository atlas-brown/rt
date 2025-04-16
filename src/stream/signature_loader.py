import yaml
import os
from typing import List, Dict
from stream.command_signature import CommandSignature

from stream.special_signatures.xargs_stat import XargsStatSignature
from stream.special_signatures.sed import SedSignature
from stream.special_signatures.cut import CutSignature
from stream.special_signatures.grep import GrepSignature
from stream.special_signatures.tr import TrSignature
from stream.special_signatures.paste import PasteSignature
from stream.special_signatures.seq import SeqSignature
from stream.special_signatures.rev import RevSignature
from stream.special_signatures.sort import SortSignature
from stream.special_signatures.fmt import FmtSignature
from stream.special_signatures.awk import AwkSignature
from stream.special_signatures.find import FindSignature
from stream.special_signatures.head import HeadSignature
from stream.special_signatures.tail import TailSignature

class SignatureLoader:
    def __init__(self, signature_dir : str = "./src/stream/signatures") -> None:
        self.signature_dir = signature_dir
        self.special_signatures: Dict[str, CommandSignature] = {
            "xargs_stat": XargsStatSignature, 
            "sed": SedSignature,
            "cut": CutSignature,
            "grep": GrepSignature,
            "tr": TrSignature,
            "paste": PasteSignature,
            "seq": SeqSignature,
            "rev": RevSignature,
            "sort": SortSignature,
            "fmt": FmtSignature,
            "awk": AwkSignature,
            "find": FindSignature,
            "head": HeadSignature,
            "tail": TailSignature,
        }
        self.signatures = self.load_all_signatures()
        self.unknown_signature = CommandSignature(
                                    command_name="unknown",
                                    default_input_type=".*",
                                    default_output_type=".*",
                                    args=[],
                                    flags=[],
                                    rules=[],
                                    isInteresting=False,
                                    isTainted=True
                                )

    def load_signature(self, command_name: str) -> CommandSignature:
        yaml_path = os.path.join(self.signature_dir, f'{command_name}.yaml')
        
        if os.path.exists(yaml_path):
            with open(yaml_path, 'r') as f:
                data = yaml.safe_load(f)
        else:
            raise FileNotFoundError(f"No signature file found for {command_name}")
            
        signature_params = {
            'command_name': data['command_name'],
            'default_input_type': data['default_input_type'],
            'default_output_type': data['default_output_type'],
            'args': data.get('args', []),
            'flags': data.get('flags', []),
            'rules': data.get('rules', []),
            'isInteresting': data.get('isInteresting', False),
            'isTainted': data.get('isTainted', True)
        }
        
        if command_name in self.special_signatures:
            return self.special_signatures[command_name](**signature_params)
        return CommandSignature(**signature_params)

    def load_all_signatures(self) -> List[CommandSignature]:
        signatures: List[CommandSignature] = []
        command_names = set()
        
        # Collect all YAML signature files
        for file_name in os.listdir(self.signature_dir):
            if file_name.endswith('.yaml'):
                command_name = os.path.splitext(file_name)[0]
                if command_name not in command_names:
                    command_names.add(command_name)
                    signatures.append(self.load_signature(command_name))
        
        return signatures
    
    def get_unknown_sigature(self) -> CommandSignature:
        return self.unknown_signature
