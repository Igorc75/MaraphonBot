#!/usr/bin/env python3
import sys
from pathlib import Path
from datetime import datetime

def export_py_files(root_dir=".", output_file="codebase_export.txt"):
    EXCLUDE_DIRS = {
        '__pycache__', '.git', '.venv', 'venv', 'env', 'ENV',
        '.vscode', '.idea', 'node_modules', 'dist', 'build',
        '.mypy_cache', '.pytest_cache', '.ruff_cache', '.tox',
        'site-packages', '.eggs', '.pytest_cache', '.DS_Store'
    }
    EXCLUDE_FILES = {'export_codebase.py', 'get-pip.py'}
    
    root = Path(root_dir).resolve()
    output_path = root / output_file
    
    py_files = []
    for path in root.rglob("*.py"):
        # Исключаем по директориям
        if any(part in EXCLUDE_DIRS for part in path.relative_to(root).parts[:-1]):
            continue
        # Исключаем по имени файла
        if path.name in EXCLUDE_FILES:
            continue
        py_files.append(path)
    
    py_files.sort()
    
    with open(output_path, 'w', encoding='utf-8') as f_out:
        f_out.write(f"{'='*80}\n")
        f_out.write(f"Python Code Export\n")
        f_out.write(f"Root: {root}\n")
        f_out.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f_out.write(f"Files: {len(py_files)}\n")
        f_out.write(f"{'='*80}\n\n")
        
        for i, filepath in enumerate(py_files, 1):
            rel_path = filepath.relative_to(root)
            f_out.write(f"\n{'#'*80}\n")
            f_out.write(f"# {i}/{len(py_files)}: {rel_path}\n")
            f_out.write(f"{'#'*80}\n\n")
            try:
                content = filepath.read_text(encoding='utf-8')
                f_out.write(content)
                if not content.endswith('\n'):
                    f_out.write('\n')
            except Exception as e:
                f_out.write(f"# ERROR: {type(e).__name__} - {e}\n")
            f_out.write('\n')
    
    print(f"✅ Экспортировано {len(py_files)} .py файлов → {output_path}")
    print(f"📊 Размер: {output_path.stat().st_size / 1024:.1f} КБ")

if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    out_file = sys.argv[2] if len(sys.argv) > 2 else "code_export.txt"
    export_py_files(root, out_file)