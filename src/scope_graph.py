import ast
import graphviz # package that allows to draw a graph using a DOT notation


class ScopeGraph(ast.NodeVisitor):
    """
    The class goal is to build a scope graph from the Abstract Syntax Tree (AST). To do so, we use a NodeVisitor to visit
    the AST defining a specific visitor for each node type we want to take into account to build the correspondent
    ScopeGraph: local scope, declaration, references (including even the import statements) [see below]

    The following classes generate local scope:
        * FunctionDef;
        * Lambda;
        * ClassDef;
        * ListComp;
        * ExceptHandler;
        * AsyncFunctionDef

    Other important aspects:
        * declarations -> Assign, FunctionDef.args.args
        * import statements -> Import.names.alias and ImportFrom.names.alias
        * reference -> Name class
    """

    def __init__(self) -> None:
        self.__scope_stack: list[str] = ["s0__main__"] # global scope
        self.__graph: dict = {"s0__main__": {"decls": set(), "refs": set(), "parent": None, "have-children": False}}
        self.__next_id: int = 1

    def get_graph(self) -> dict:
        """
        :return: data structure containing the representation of the scope graph
        """
        return self.__graph

    def __current_scope(self) -> str:
        """
        :return: current scope name
        """
        return self.__scope_stack[-1]

    def __get_parent_scope(self) -> str | None:
        return self.__scope_stack[-2] if len(self.__scope_stack) > 1 else None

    def get_declaration_scopes(self, decl_name: str) -> list[str]:
        """
        Get the list of scopes in which the declaration occurred

        :param decl_name: declaration name to search
        :return: list of scopes
        """
        scopes = []

        for scope in self.__graph.keys():
            if decl_name in self.__graph[scope]["decls"]:
                scopes.append(scope)

        return scopes

    def get_leaf_scopes(self) -> list:
        """
        Get a list of scopes that have no children
        :return: list of scopes with no children
        """
        return list([scope for scope in self.__graph.keys() if not self.__graph[scope]["have-children"]])

    def visit_FunctionDef(self, node:ast.FunctionDef) -> None:
        sid = f"s{self.__next_id}_func_{node.name}"

        self.__next_id += 1
        self.__graph[sid] = {"decls": set(), "refs": set(), "parent": None, "have-children": False}

        self.__graph[self.__current_scope()]["decls"].add(f"func_{node.name}")
        self.__graph[self.__current_scope()]["have-children"] = True

        self.__scope_stack.append(sid)

        if (parent := self.__get_parent_scope())is not None:
            self.__graph[self.__current_scope()]["parent"] = parent

        for arg in node.args.args:
            self.__graph[sid]["decls"].add(f"var_{arg.arg}")

        self.generic_visit(node)
        self.__scope_stack.pop()

    def visit_Lambda(self, node: ast.Lambda) -> None:
        sid = f"s{self.__next_id}_lambda"

        self.__next_id += 1
        self.__graph[sid] = {"decls": set(), "refs": set(), "parent": None, "have-children": False}
        self.__graph[self.__current_scope()]["have-children"] = True

        self.__scope_stack.append(sid)

        if (parent := self.__get_parent_scope())is not None:
            self.__graph[sid]["parent"] = parent

        for arg in node.args.args:
            self.__graph[sid]["decls"].add(f"var_{arg.arg}")

        self.generic_visit(node)
        self.__scope_stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        sid = f"s{self.__next_id}_class_{node.name}"

        self.__next_id += 1
        self.__graph[sid] = {"decls": set(), "refs": set(), "parent": None, "have-children": False}

        self.__graph[self.__current_scope()]["have-children"] = True
        self.__graph[self.__current_scope()]["decls"].add(f"class_{node.name}")

        self.__scope_stack.append(sid)

        if (parent := self.__get_parent_scope())is not None:
            self.__graph[self.__current_scope()]["parent"] = parent

        self.generic_visit(node)
        self.__scope_stack.pop()

    def visit_ListComp(self, node: ast.ListComp) -> None:
        sid = f"s{self.__next_id}_lstComp"

        self.__next_id += 1
        self.__graph[sid] = {"decls": set(), "refs": set(), "parent": None, "have-children": False}
        self.__graph[self.__current_scope()]["have-children"] = True

        self.__scope_stack.append(sid)

        if (parent := self.__get_parent_scope())is not None:
            self.__graph[sid]["parent"] = parent

        self.generic_visit(node)
        self.__scope_stack.pop()

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        sid = f"s{self.__next_id}_excHandler"

        self.__next_id += 1
        self.__graph[sid] = {"decls": set(), "refs": set(), "parent": None, "have-children": False}
        self.__graph[self.__current_scope()]["have-children"] = True

        self.__scope_stack.append(sid)

        if (parent := self.__get_parent_scope())is not None:
            self.__graph[self.__current_scope()]["parent"] = parent

        if node.name is not None:
            self.__graph[sid]["decls"].add(f"exp_{node.name}")

        self.generic_visit(node)
        self.__scope_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        sid = f"s{self.__next_id}_asyncFunc_{node.name}"

        self.__next_id += 1
        self.__graph[sid] = {"decls": set(), "refs": set(), "parent": None, "have-children": False}

        self.__graph[self.__current_scope()]["decls"].add(f"afunc_{node.name}")
        self.__graph[self.__current_scope()]["have-children"] = True

        self.__scope_stack.append(sid)

        if (parent := self.__get_parent_scope())is not None:
            self.__graph[self.__current_scope()]["parent"] = parent

        for arg in node.args.args:
            self.__graph[sid]["decls"].add(f"var_{arg.arg}")

        self.generic_visit(node)
        self.__scope_stack.pop()

    def visit_Assign(self, node: ast.Assign) -> None:
        for t in node.targets:
            if isinstance(t, ast.Name):
                self.__graph[self.__current_scope()]["decls"].add(f"var_{t.id}")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.__graph[self.__current_scope()]["refs"].add(f"var_{node.id}")

    def visit_Import(self, node: ast.Import) -> None:
        for pkg in node.names:
            if isinstance(pkg, ast.alias):
                if pkg.asname is None:
                    self.__graph[self.__current_scope()]["refs"].add(f"import_{pkg.name}")
                else:
                    self.__graph[self.__current_scope()]["refs"].add(f"import_{pkg.asname}")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for pkg in node.names:
            if isinstance(pkg, ast.alias):
                if pkg.asname is None:
                    self.__graph[self.__current_scope()]["refs"].add(f"import_{pkg.name}")
                else:
                    self.__graph[self.__current_scope()]["refs"].add(f"import_{pkg.asname}")

    def draw(self, name: str) -> None:
        """
        Draw the scope graph using the DOT notation.
        The function saves graph in 'gv' and 'pdf' format in a folder called 'scope-graphs'.

        LEGEND
        --------------------------
            * ELLIPSE: local scope
            * BOX: variable
            * BOX -> ELLIPSE: declaration
            * ELLIPSE -> BOX: reference
            * ELLIPSE -> ELLIPSE: parent

        :param name: file's name to which saves the graph
        """

        graph = graphviz.Digraph()
        scopes = self.__graph.keys()

        # adding nodes to the graph
        for scope in scopes:
            graph.node(scope)

        # add parent edges
        for scope in scopes:
            parent = self.__graph[scope]["parent"]

            if parent is not None:
                graph.edge(scope, parent)

        # adding declaration edges
        for scope in scopes:
            decls = self.__graph[scope]["decls"]
            scope_prefix = scope.split("_")[0]

            for decl in decls:
                graph.node(f"{scope_prefix}_decl_{decl}", shape="box")
                graph.edge(f"{scope_prefix}_decl_{decl}", scope)

        # adding reference edges
        for scope in scopes:
            refs = self.__graph[scope]["refs"]
            scope_prefix = scope.split("_")[0]

            for ref in refs:
                graph.node(f"{scope_prefix}_ref_{ref}", shape="box")
                graph.edge(scope, f"{scope_prefix}_ref_{ref}")

        graph.render(f"scope-graphs/{name}.gv").replace('\\', '/')