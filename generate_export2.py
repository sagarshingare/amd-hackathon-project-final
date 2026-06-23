import os
from pathlib import Path
import re

output_file = "Google_Doc_Code_Export.md"
exclude_dirs = {'.git', '__pycache__', 'temp_sessions', 'appScreenshots'}
exclude_exts = {'.DS_Store', '.zip', '.pkl', '.png', '.pdf', '.pyc'}

def is_text_file(filepath):
    if filepath.suffix in exclude_exts or filepath.name in exclude_exts:
        return False
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            f.read(1024)
        return True
    except UnicodeDecodeError:
        return False

valid_files = []
for p in Path('.').rglob('*'):
    if p.is_file():
        if any(part in exclude_dirs for part in p.parts):
            continue
        if p.name == 'generate_export2.py' or p.name == output_file:
            continue
        if is_text_file(p):
            valid_files.append(p)

def make_anchor(path_str):
    s = str(path_str).lower()
    return re.sub(r'[^a-z0-9]', '', s)

def generate_md_list(dir_path, indent=0):
    try:
        contents = sorted(os.listdir(dir_path))
    except PermissionError:
        return ""
    
    contents = [c for c in contents if c not in exclude_dirs and c not in exclude_exts and c not in ['generate_export2.py', output_file]]
    
    # Sort directories first, then files
    dirs = [c for c in contents if os.path.isdir(os.path.join(dir_path, c))]
    files = [c for c in contents if not os.path.isdir(os.path.join(dir_path, c))]
    
    list_str = ""
    prefix = "  " * indent
    for d in dirs:
        list_str += f"{prefix}* 📁 **{d}/**\n"
        list_str += generate_md_list(os.path.join(dir_path, d), indent + 1)
    
    for f in files:
        p_obj = Path(os.path.join(dir_path, f)).relative_to('.')
        if p_obj in valid_files:
            anchor = make_anchor(p_obj)
            list_str += f"{prefix}* 📄 [{f}](#{anchor})\n"
        else:
            list_str += f"{prefix}* 📄 {f} *(binary/excluded)*\n"
    return list_str

with open(output_file, "w", encoding="utf-8") as out:
    out.write("# Project Folder Structure and Code\n\n")
    
    out.write("## Folder Structure\n\n")
    out.write("Click on any file name to jump to its contents.\n\n")
    out.write(generate_md_list("."))
    out.write("\n---\n\n")
    out.write("## File Contents\n\n")
    
    for pf in sorted(valid_files):
        anchor = make_anchor(pf)
        # Using an HTML anchor before the heading to guarantee the link works if the markdown parser supports it
        out.write(f'<a id="{anchor}"></a>\n')
        out.write(f"### 📄 {pf}\n\n")
        
        ext = pf.suffix.lower()
        lang = "text"
        if ext == '.py': lang = "python"
        elif ext == '.md': lang = "markdown"
        elif ext == '.csv': lang = "csv"
        elif ext == '.txt': lang = "text"
        elif ext == '.json': lang = "json"
        elif ext in ['.html', '.htm']: lang = "html"
        elif ext in ['.js', '.jsx']: lang = "javascript"
        elif ext in ['.css']: lang = "css"
        
        out.write(f"```{lang}\n")
        try:
            with open(pf, "r", encoding="utf-8") as f:
                content = f.read()
                # Truncate very large CSVs to avoid crashing Google Docs with a single massive file
                if ext == '.csv' and len(content) > 100000:
                    lines = content.split('\n')
                    if len(lines) > 200:
                        out.write('\n'.join(lines[:200]))
                        out.write("\n\n... (File truncated for export due to length, showing first 200 lines) ...\n")
                    else:
                        out.write(content if content.strip() else "# (Empty file)\n")
                else:
                    out.write(content if content.strip() else "# (Empty file)\n")
        except Exception as e:
            out.write(f"# Error reading file: {e}\n")
        out.write("\n```\n\n")
        out.write("[⬆ Back to Folder Structure](#folder-structure)\n\n")
        out.write("---\n\n")

print(f"Successfully generated {output_file}")