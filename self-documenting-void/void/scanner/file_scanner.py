import os
import fnmatch
from pathlib import Path
import yaml

DEFAULT_IGNORE = [
    ".git", ".venv", "venv", "__pycache__", "node_modules", 
    ".void", ".pytest_cache", ".mypy_cache", "*.pyc", ".DS_Store"
]

class FileScanner:
    def __init__(self, root=None, ignore=None):
        self.root = Path(root) if root else Path.cwd()
        self.ignore = set(ignore) if ignore else set(DEFAULT_IGNORE)
        
        # Try to load extra ignores from config.yaml
        config_path = self.root / "config.yaml"
        if config_path.is_file():
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    if config and "ignore" in config:
                        self.ignore.update(config["ignore"])
            except Exception:
                pass

    def _should_ignore(self, path: Path) -> bool:
        name = path.name
        for pattern in self.ignore:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False

    def scan(self):
        files_data = []
        directories_data = []
        
        python_files = []
        markdown_files = []
        json_files = []
        yaml_files = []
        
        total_files = 0
        python_count = 0
        markdown_count = 0
        json_count = 0
        yaml_count = 0
        other_count = 0
        dir_count = 0

        for current_root, dirs, files in os.walk(self.root):
            current_path = Path(current_root)
            
            # Filter directories in-place to prevent os.walk from descending
            dirs[:] = [d for d in dirs if not self._should_ignore(current_path / d)]
            
            if current_path != self.root:
                dir_count += 1
                directories_data.append(str(current_path.relative_to(self.root).as_posix()))

            for file_name in files:
                file_path = current_path / file_name
                if self._should_ignore(file_path):
                    continue
                
                try:
                    size = file_path.stat().st_size
                except Exception:
                    size = 0
                
                suffix = file_path.suffix.lower()
                is_python = suffix == ".py"
                is_markdown = suffix == ".md"
                is_json = suffix == ".json"
                is_yaml = suffix in [".yaml", ".yml"]
                
                rel_path = str(file_path.relative_to(self.root).as_posix())
                
                files_data.append({
                    "path": rel_path,
                    "name": file_name,
                    "suffix": suffix,
                    "size": size,
                    "is_python": is_python,
                    "is_markdown": is_markdown,
                    "is_json": is_json,
                    "is_yaml": is_yaml
                })
                
                total_files += 1
                if is_python:
                    python_count += 1
                    python_files.append(rel_path)
                elif is_markdown:
                    markdown_count += 1
                    markdown_files.append(rel_path)
                elif is_json:
                    json_count += 1
                    json_files.append(rel_path)
                elif is_yaml:
                    yaml_count += 1
                    yaml_files.append(rel_path)
                else:
                    other_count += 1

        return {
            "root": str(self.root.absolute()),
            "files": files_data,
            "directories": directories_data,
            "counts": {
                "total_files": total_files,
                "python_files": python_count,
                "markdown_files": markdown_count,
                "json_files": json_count,
                "yaml_files": yaml_count,
                "other_files": other_count,
                "directories": dir_count
            },
            "python_files": python_files,
            "markdown_files": markdown_files,
            "json_files": json_files,
            "yaml_files": yaml_files
        }
