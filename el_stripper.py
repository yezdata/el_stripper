import argparse
from pathlib import Path
import sys
from typing import Union
import libcst as cst


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

        mode_str = "and docstrings" if strip_docstrings else ""
        print(f"[✓] Stripped comments {mode_str} in {file_path}")

    except cst.ParserSyntaxError as e:
        print(f"[X] Syntax error in {file_path}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"[X] Error while stripping {file_path}: {e}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str, help=".py to strip")
    parser.add_argument("--doc", action="store_true", help="strip docstrings")

    args = parser.parse_args()
    target_file = Path(args.file)

    if not target_file.is_file():
        print(f"Error: File '{target_file}' does not exist", file=sys.stderr)
        sys.exit(1)

    strip_file(target_file, strip_docstrings=args.doc)


if __name__ == "__main__":
    main()
