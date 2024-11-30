#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

def extract_cookie_content(cookie_path):
    """
    Extract comments and content from a .cookie file
    Returns (comments, content) tuple where comments is a list of comment lines
    and content is a list of non-comment lines
    """
    comments = []
    content = []
    
    try:
        with open(cookie_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines:
            if line.strip().startswith('#'):
                comments.append(line.lstrip('#').strip())
            else:
                # remove color escape sequences
                re_escape = re.compile(r'[\x1b\^][^m]*m')
                line = re_escape.sub('', line)
                content.append(line)
                
        return comments, content
    except Exception as e:
        print(f"Error processing {cookie_path}: {str(e)}", file=sys.stderr)
        return [], []

def process_directory(source_path, target_base_path):
    """
    Process the source directory to find .cookie files and create corresponding structure
    """
    source_path = Path(source_path)
    target_base_path = Path(target_base_path)
    readme_path = target_base_path / "README.md"
    
    # Store all cookie files and their comments for README generation
    cookie_files = {}

    files = []
    files_pattern = ["*.cookie", "tang300", "song100"]
    for pattern in files_pattern:
        files.extend(source_path.rglob(pattern))
    # Find all directories containing .cookie files
    for cookie_file in files:
        cookie_dir = cookie_file.parent
        relative_dir = cookie_dir.relative_to(source_path)
        
        # Create target directory name (removing .d suffix if present)
        target_dir_name = str(relative_dir)
        if target_dir_name.endswith('.d'):
            target_dir_name = target_dir_name[:-2]
            
        target_dir = target_base_path / target_dir_name
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Process the cookie file
        comments, content = extract_cookie_content(cookie_file)
        
        if comments or content:
            # Store for README
            str_target_dir = str(target_dir_name).rstrip('.d')
            str_cookie_file = str(cookie_file.relative_to(cookie_dir)).rstrip('.cookie')
            if str_target_dir in cookie_files:
                cookie_files[str_target_dir].append((str_cookie_file, comments))
            else:
                cookie_files[str_target_dir] = [(str_cookie_file, comments)]
            
            # Write content to target file (without .cookie extension)
            target_file = target_dir / cookie_file.name.replace('.cookie', '')
            try:
                with open(target_file, 'w', encoding='utf-8') as f:
                    f.writelines(content)
            except Exception as e:
                print(f"Error writing to {target_file}: {str(e)}", file=sys.stderr)

    # Generate README with all collected comments

    try:
        with open(readme_path, 'w', encoding='utf-8') as f:
            for target_dir, cookie_files in cookie_files.items():
                f.write(f"\n## {target_dir}\n\n")
                for file_path, comments in cookie_files:
                    if comments:
                        f.write(f"\n### {file_path}\n\n")
                        for comment in comments:
                            f.write(f"{comment}\n")
    except Exception as e:
        print(f"Error writing README: {str(e)}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description='Process .cookie files from source directory')
    parser.add_argument('source_path', help='Source directory path containing .cookie files')
    parser.add_argument('target_path', help='Target directory path to store processed files')
    
    args = parser.parse_args()
        
    try:
        process_directory(args.source_path, args.target_path)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
