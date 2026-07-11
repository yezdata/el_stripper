import argparse
from pathlib import Path
from typing import Union
import libcst as cst
import logging
import pathspec
import os

DEFAULT_IGNORE = {
    ".venv",
    "venv",
    ".egg-info",
    "__pycache__",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
}


class CommentStripper(cst.CSTTransformer):
    def __init__(self, strip_docstrings: bool = False):
        super().__init__()
        self.strip_docstrings = strip_docstrings

    def leave_Comment(
        self, original_node: cst.Comment, updated_node: cst.Comment
    ) -> Union[cst.Comment, cst.RemovalSentinel]:
        
        return cst.RemoveFromParent()

    def leave_EmptyLine(
        self, original_node: cst.EmptyLine, updated_node: cst.EmptyLine
    ) -> cst.EmptyLine:
        
        
        if updated_node.comment is not None:
            return updated_node.with_changes(comment=None)
        return updated_node

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        if not self.strip_docstrings:
            return updated_node

        
        if updated_node.get_docstring() is not None:
            
            new_body = updated_node.body.body[1:]
            return updated_node.with_changes(
                body=updated_node.body.with_changes(body=new_body)
            )
        return updated_node

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        if not self.strip_docstrings:
            return updated_node

        
        if updated_node.get_docstring() is not None:
            new_body = updated_node.body.body[1:]
            return updated_node.with_changes(
                body=updated_node.body.with_changes(body=new_body)
            )
        return updated_node

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        if not self.strip_docstrings:
            return updated_node

        
        if updated_node.get_docstring() is not None:
            new_body = updated_node.body[1:]
            return updated_node.with_changes(body=new_body)
        return updated_node


def strip_file(file_path: Path, strip_docstrings: bool) -> None:
    try:
        source_code = file_path.read_text(encoding="utf-8")
        cst_tree = cst.parse_module(source_code)

        transformer = CommentStripper(strip_docstrings=strip_docstrings)
        final_ast = cst_tree.visit(transformer)

        file_path.write_text(final_ast.code, encoding="utf-8")

        try:
            relative_path = file_path.relative_to(Path.cwd())
        except ValueError:
            relative_path = file_path

        mode_str = " and docstrings " if strip_docstrings else " "
        logging.info(f"[✓] Stripped comments{mode_str}in {relative_path}")

    except cst.ParserSyntaxError as e:
        logging.error(f"[X] Syntax error in {file_path}: {e}")
    except Exception:
        logging.exception(f"[X] Error while stripping {file_path}")


def load_gitignore(target_path: Path) -> pathspec.PathSpec:
    root_dir = target_path.parent if target_path.is_file() else target_path
    gitignore_path = root_dir / ".gitignore"

    if gitignore_path.is_file():
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                return pathspec.PathSpec.from_lines("gitwildmatch", f.readlines())
        except OSError:
            pass
    return pathspec.PathSpec.from_lines("gitwildmatch", [])


def get_files_to_process(target_path: Path, spec: pathspec.PathSpec) -> list[Path]:
    root_dir = target_path.parent if target_path.is_file() else target_path

    if target_path.is_file():
        if target_path.suffix != ".py":
            logging.error(f"File {target_path} is not a Python file.")
            return []
        try:
            rel_path = target_path.relative_to(root_dir)
            if spec.match_file(str(rel_path)):
                return []
        except ValueError:
            pass
        return [target_path]

    files_to_process = []

    for root, dirs, files in os.walk(target_path):
        dirs[:] = [d for d in dirs if d not in DEFAULT_IGNORE]

        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = Path(root) / file
            try:
                rel_path = file_path.relative_to(root_dir)
                if not spec.match_file(str(rel_path)):
                    files_to_process.append(file_path)
            except ValueError:
                files_to_process.append(file_path)

    return files_to_process


def main() -> None:
    parser = argparse.ArgumentParser(
        "Strip comments and optionally docstrings from Python files."
    )
    parser.add_argument(
        "path",
        type=str,
        help="Python file or directory containing Python files to strip.",
    )
    parser.add_argument("--doc", action="store_true", help="Also strip docstrings")

    args = parser.parse_args()

    
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)

    target_path = Path(args.path).resolve()

    if not target_path.exists():
        logging.error(f"Path {target_path} does not exist.")
        return

    spec = load_gitignore(target_path)
    files_to_process = get_files_to_process(target_path, spec)

    if not files_to_process:
        logging.info("No Python files found to process.")
        return

    for file in files_to_process:
        strip_file(file, strip_docstrings=args.doc)


if __name__ == "__main__":
    main()
