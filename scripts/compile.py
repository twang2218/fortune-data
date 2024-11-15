# 递归便利给定源目录，将其中所有无后缀的文件，使用strfile命令编译成.dat文件存储于同结构的目标目录下，并将源文件复制到目标目录下

import shutil
import subprocess
import sys
from pathlib import Path

def compile(src, dest):
    src_path = Path(src)
    dest_path = Path(dest)
    
    for src_file in src_path.rglob('*'):
        if src_file.is_file():
            print(f'Compiling {src_file.name}...')
            if '.' not in src_file.name:
                print(f'Compiling {src_file.name}...')
                # Calculate relative path from src to maintain directory structure
                rel_dir = src_file.parent.relative_to(src_path)
                if len(rel_dir.parts) > 1:
                    # only keep the first part of the path as `fortune` cannot recursively search directories
                    rel_dir = Path(rel_dir.parts[0])
                rel_path = rel_dir / src_file.name
                dest_file = dest_path / rel_path
                dat_dest_file = dest_path / rel_path.with_suffix('.dat')
                
                # Create parent directories if they don't exist
                dat_dest_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Run strfile command
                subprocess.run(['strfile', str(src_file), str(dat_dest_file)])
                
                # Copy source file
                if dest_file.exists():
                    dest_file.unlink()
                shutil.copyfile(src_file, dest_file)

if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) != 2:
        print('Usage: compile.py <source> <destination>')
        sys.exit(1)
    compile(args[0], args[1])
