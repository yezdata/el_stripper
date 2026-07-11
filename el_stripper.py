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
    ) -> Union[cst.EmptyLine, cst.RemovalSentinel]:
        if original_node.comment is not None:
            return cst.RemoveFromParent()
        return updated_node

    def leave_SimpleStatementLine(
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ) -> Union[cst.SimpleStatementLine, cst.RemovalSentinel]:
        if self.strip_docstrings:
            if len(updated_node.body) == 1 and isinstance(
                updated_node.body[0], cst.Expr
            ):
                expr = updated_node.body[0]
                if isinstance(expr.value, cst.SimpleString):
                    return cst.RemoveFromParent()
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


def load_gitignore(root_dir: Path) -> pathspec.PathSpec:
    gitignore_path = root_dir / ".gitignore"
    if gitignore_path.is_file():
        with open(gitignore_path, "r", encoding="utf-8") as f:
            return pathspec.PathSpec.from_lines("gitwildmatch", f.readlines())
    return pathspec.PathSpec.from_lines("gitwildmatch", [])


def get_files_from_dir(
    target_dir: Path, root_dir: Path, spec: pathspec.PathSpec
) -> list[Path]:
    files_to_process = []

    for root, dirs, files in os.walk(target_dir):
        current_dir = Path(root)

        valid_dirs = []
        for d in dirs:
            if d in DEFAULT_IGNORE:
                continue

            dir_path = current_dir / d
            try:
                rel_dir_path = dir_path.relative_to(root_dir)
                if spec.match_file(f"{rel_dir_path}/"):
                    continue
            except ValueError:
                pass
            valid_dirs.append(d)

        dirs[:] = valid_dirs

        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = current_dir / file
            try:
                rel_file_path = file_path.relative_to(root_dir)
                if spec.match_file(str(rel_file_path)):
                    continue
            except ValueError:
                pass

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

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    target_path = Path(args.path).resolve()
    root_dir = Path.cwd()
    spec = load_gitignore(root_dir)

    files_to_process = []
    if target_path.is_file():
        if target_path.suffix == ".py":
            try:
                rel_file_path = target_path.relative_to(root_dir)
                if not spec.match_file(str(rel_file_path)):
                    files_to_process.append(target_path)
            except ValueError:
                files_to_process.append(target_path)
        else:
            logging.error(f"File {target_path} is not a Python file.")
            return
    elif target_path.is_dir():
        files_to_process = get_files_from_dir(target_path, root_dir, spec)
    else:
        logging.error(f"Path {target_path} does not exist.")
        return

    if not files_to_process:
        logging.info("No Python files found to process.")
        return

    for file in files_to_process:
        strip_file(file, strip_docstrings=args.doc)


if __name__ == "__main__":
    main()
