import ast

from classes.result import Result

class Heuristics(ast.NodeVisitor):
    def __init__(self, code_path: str) -> None:
        self.__FILTERED_FUNCTIONS: list[str] = ["open", "Lock", "RLock", "TemporaryFile", "NamedTemporaryFile",
                                                "TemporaryDirectory", "closing", "suppress", "redirect_stdout", "redirect_stderr",
                                                "ExitStack", "nullcontext", "urlopen", "connect", "Cursor", "Session", "scandir",
                                                "ZipFile", "TarFile", "requests", "Image", "localcontext", "Condition", "no_grad",
                                                "autocast", "errstate", "style", "context"]
        self.__results: dict[str, list[int]] = {
            "with_statement": [],
            "eval_call": [],
            "exec_call": []
        }
        tree = ast.parse(open(code_path, 'r').read())

        self.visit(tree)

    def get_results(self) -> list[Result]:
        return [Result(name, lines) for name, lines in self.__results.items()]

    # make detection of with statements
    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            if isinstance(item.context_expr.func, ast.Name):
                if item.context_expr.func.id not in self.__FILTERED_FUNCTIONS and len(item.context_expr.args) >= 3:
                    self.__results["with_statement"].append(node.lineno)
            elif isinstance(item.context_expr.func, ast.Attribute):
                if item.context_expr.func.attr not in self.__FILTERED_FUNCTIONS and len(item.context_expr.args) >= 3:
                    self.__results["with_statement"].append(node.lineno)

        self.generic_visit(node)

    # make detection of assignments that make a call of eval
    def visit_Assign(self, node: ast.Assign) -> None:
        if isinstance(node.value, ast.Call) and node.value.func.id == "eval":
            self.__results["eval_call"].append(node.lineno)

        self.generic_visit(node)

    # detect exec function calls
    def visit_Expr(self, node: ast.Expr) -> None:
        if isinstance(node.value, ast.Call) and node.value.func.id == "exec":
            self.__results["exec_call"].append(node.lineno)

        self.generic_visit(node)

if __name__ == "__main__":
    heuristics_engine = Heuristics("../../yara/test/code.py")

    print(heuristics_engine.get_results())