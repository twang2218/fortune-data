
# 递归便利给定源目录，将其中所有无后缀的文件，使用strfile命令编译成.dat文件存储于同结构的目标目录下，并将源文件复制到目标目录下

import os
import shutil
import subprocess
import sys

def compile(src, dest):
    for root, dirs, files in os.walk(src):
        for file in files:
            print(f'Compiling {file}...')
            if '.' not in file:
                print(f'Compiling {file}...')
                src_file = os.path.join(root, file)
                dat_dest_file = os.path.join(dest, os.path.relpath(src_file, src) + '.dat')
                os.makedirs(os.path.dirname(dat_dest_file), exist_ok=True)
                subprocess.run(['strfile', src_file, dat_dest_file])
                dest_file = os.path.join(dest, os.path.relpath(src_file, src))
                if os.path.exists(dest_file):
                    os.remove(dest_file)
                shutil.copyfile(src_file, dest_file)

if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) != 2:
        print('Usage: compile.py <source> <destination>')
        sys.exit(1)
    compile(args[0], args[1])
