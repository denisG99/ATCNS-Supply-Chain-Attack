import ast
import tokenize

from classes.result import Result
from classes.scope_graphv2 import ScopeGraph

class ASTHeuristics(ast.NodeVisitor):
    def __init__(self, code_path: str, scope_graph: ScopeGraph) -> None:
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
        self.__scope_graph: dict = scope_graph.get_graph()
        self.__scope_stack: list[str] = ["s0__main__"]
        self.__next_id: int = 1

        try:
            with tokenize.open(code_path) as f:
                code = f.read()
        except (SyntaxError, UnicodeDecodeError, LookupError):
            # Fallback: attempt to read with UTF-8 and replace undecodable bytes.
            # This keeps the pipeline running; files with severe encoding issues may still fail to parse.
            with open(code_path, "r", encoding="utf-8", errors="replace") as f:
                code = f.read()

        tree = ast.parse(code)

        self.visit(tree)

    def get_results(self) -> list[Result]:
        return [Result(name, lines) for name, lines in self.__results.items() if len(lines) > 0]

    def __track_scope(self, node: ast.FunctionDef|ast.AsyncFunctionDef|ast.Lambda|ast.ClassDef|ast.ListComp|ast.ExceptHandler) -> None:
        def get_scope_id(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda | ast.ClassDef | ast.ListComp | ast.ExceptHandler) -> str:
            if isinstance(node, ast.FunctionDef):
                visit_type = "func"
                sid = f"s{self.__next_id}_{visit_type}_{node.name}"
            elif isinstance(node, ast.AsyncFunctionDef):
                visit_type = "afunc"
                sid = f"s{self.__next_id}_{visit_type}_{node.name}"
            elif isinstance(node, ast.Lambda):
                visit_type = "lambda"
                sid = f"s{self.__next_id}_{visit_type}"
            elif isinstance(node, ast.ClassDef):
                visit_type = "class"
                sid = f"s{self.__next_id}_{visit_type}_{node.name}"
            elif isinstance(node, ast.ListComp):
                visit_type = "lstComp"
                sid = f"s{self.__next_id}_{visit_type}"
            elif isinstance(node, ast.ExceptHandler):
                visit_type = "excHandler"
                sid = f"s{self.__next_id}_{visit_type}"

            return sid

        self.__scope_stack.append(get_scope_id(node))
        self.__next_id += 1

        self.generic_visit(node)
        self.__scope_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.__track_scope(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.__track_scope(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self.__track_scope(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.__track_scope(node)

    def visit_ListComp(self, node: ast.ListComp)-> None:
        self.__track_scope(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler)-> None:
        self.__track_scope(node)

    def __is_builtin(self, target: str, scope:str) -> bool:
        return any(f"func_{target}" in v for v in [decl[0] for decl in self.__scope_graph[scope]["decls"]]) or any(f"import_{target}" in v for v in [ref[0] for ref in self.__scope_graph[scope]["refs"]])

    # make detection of with statements 2 possible cases:
    # 1. function not in FILTERED_FUNCTIONS with at least >= 3 (needed for locally overwrite the target function, see PoC)
    # 2. function in FILTERED_FUNCTIONSn (all built-in), however, such a function is defined in the scope of the with statement
    def visit_With(self, node: ast.With) -> None:
        current_scope = self.__scope_stack[-1]

        for item in node.items:
            if isinstance(item.context_expr.func, ast.Name):
                func_name = item.context_expr.func.id

                if func_name not in self.__FILTERED_FUNCTIONS and len(item.context_expr.args) >= 3:
                    self.__results["with_statement"].append(node.lineno)
                elif func_name in self.__FILTERED_FUNCTIONS and self.__is_builtin(func_name, current_scope):
                    self.__results["with_statement"].append(node.lineno)

            elif isinstance(item.context_expr.func, ast.Attribute):
                func_name = item.context_expr.func.attr

                if item.context_expr.func.attr not in self.__FILTERED_FUNCTIONS and len(item.context_expr.args) >= 3:
                    self.__results["with_statement"].append(node.lineno)
                elif item.context_expr.func.attr in self.__FILTERED_FUNCTIONS and self.__is_builtin(func_name, current_scope):
                    self.__results["with_statement"].append(node.lineno)
        self.generic_visit(node)

    # make detection of assignments that make a call of eval
    def visit_Assign(self, node: ast.Assign) -> None:
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == "eval":
            self.__results["eval_call"].append(node.lineno)

        self.generic_visit(node)

    # detect exec function calls
    def visit_Expr(self, node: ast.Expr) -> None:
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == "exec":
            self.__results["exec_call"].append(node.lineno)

        self.generic_visit(node)
