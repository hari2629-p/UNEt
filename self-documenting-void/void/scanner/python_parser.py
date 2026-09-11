import ast
from pathlib import Path

class PythonParser:
    def __init__(self, root=None):
        self.root = Path(root) if root else Path.cwd()

    def parse_file(self, relative_path):
        result = {
            "file": str(relative_path),
            "functions": [],
            "classes": [],
            "imports": [],
            "docstring": None,
            "error": None
        }

        full_path = self.root / relative_path
        if not full_path.is_file():
            result["error"] = "File not found"
            return result

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                source = f.read()
            
            tree = ast.parse(source, filename=str(full_path))
            result["docstring"] = ast.get_docstring(tree)

            def extract_function_info(node):
                args = [a.arg for a in node.args.args]
                if getattr(node.args, "vararg", None):
                    args.append(f"*{node.args.vararg.arg}")
                if getattr(node.args, "kwarg", None):
                    args.append(f"**{node.args.kwarg.arg}")
                
                decorators = []
                for dec in node.decorator_list:
                    if hasattr(ast, "unparse"):
                        decorators.append(ast.unparse(dec))
                    elif isinstance(dec, ast.Name):
                        decorators.append(dec.id)
                    else:
                        decorators.append("decorator")
                        
                returns_none = False
                if getattr(node, "returns", None):
                    if isinstance(node.returns, ast.Constant) and node.returns.value is None:
                        returns_none = True
                    elif isinstance(node.returns, ast.Name) and node.returns.id == "None":
                        returns_none = True
                else:
                    has_non_none = False
                    for child in ast.walk(node):
                        # Don't check inside nested functions
                        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and child is not node:
                            continue
                        if isinstance(child, ast.Return):
                            if child.value is not None:
                                if not (isinstance(child.value, ast.Constant) and child.value.value is None):
                                    has_non_none = True
                                    break
                    returns_none = not has_non_none

                return {
                    "name": node.name,
                    "arguments": args,
                    "returns": ast.unparse(node.returns) if hasattr(ast, "unparse") and getattr(node, "returns", None) else None,
                    "returns_none": returns_none,
                    "docstring": ast.get_docstring(node),
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "lineno": getattr(node, "lineno", None),
                    "decorators": decorators
                }

            for node in tree.body:
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        result["imports"].append({
                            "type": "import",
                            "module": alias.name,
                            "alias": alias.asname
                        })
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        result["imports"].append({
                            "type": "import_from",
                            "module": node.module,
                            "name": alias.name,
                            "alias": alias.asname
                        })
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    result["functions"].append(extract_function_info(node))
                elif isinstance(node, ast.ClassDef):
                    methods = []
                    for child in node.body:
                        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            methods.append(extract_function_info(child))
                    
                    bases = []
                    for b in node.bases:
                        if hasattr(ast, "unparse"):
                            bases.append(ast.unparse(b))
                        elif isinstance(b, ast.Name):
                            bases.append(b.id)
                        else:
                            bases.append("base")

                    result["classes"].append({
                        "name": node.name,
                        "methods": methods,
                        "bases": bases,
                        "docstring": ast.get_docstring(node),
                        "lineno": getattr(node, "lineno", None)
                    })

        except Exception as e:
            result["error"] = str(e)

        return result
