import itertools
import ast
import re
import tokenize

from scope_graph import ScopeGraph

class Detector:
    """
    This class goal is to perform some detection on the scope graph.
    The detector performs the following detection:
        * classifying a scope;
        * function and method shadowing;
        * import shadowing.
    """
    def __init__(self, code_path: str, scope_graph_name: str="") -> None:
        """
        Construct the detector based on the scope graph built from a code.

        :param code_path: path to the code on which we build the scope graph
        :param scope_graph_name: name of the scope graph to save. If the string is empty, we don't save the graph and ignore the argument.
        """
        # Use tokenize.open to respect PEP 263 encoding declaration and handle non-UTF-8 files robustly.
        try:
            with tokenize.open(code_path) as f:
                code = f.read()
        except (SyntaxError, UnicodeDecodeError, LookupError):
            # Fallback: attempt to read with UTF-8 and replace undecodable bytes.
            # This keeps the pipeline running; files with severe encoding issues may still fail to parse.
            with open(code_path, "r", encoding="utf-8", errors="replace") as f:
                code = f.read()

        # creating AST
        try:
            tree = ast.parse(code)

            # building scope graph
            self.__builder = ScopeGraph()
            self.__builder.visit(tree)

            if not scope_graph_name == "":
                self.__builder.draw(scope_graph_name)
        except Exception as e:
            print(f"Error parsing the code: {e}")
            self.__builder = None

    def get_builder(self) -> ScopeGraph:
        return self.__builder

    def __is_local_scope(self, scope: str) -> bool:
        """
        A scope is local if it has a parent.

        :param scope: scope's name
        :return: True if the scope is local, False otherwise
        """

        return self.__builder.get_graph()[scope]["parent"] is not None

    def __is_global_scope(self, scope: str) -> bool:
        """
        A scope is global if it has no parent.

        :param scope: scope's name
        :return: True if the scope is global, False otherwise
        """

        return self.__builder.get_graph()[scope]["parent"] is None

    def classify_scope(self, decl_var: str) -> None:
        """
        Classify the scope of a declaraed variable.

        :param decl_var: declared variable name
        """
        lst_scopes = self.__builder.get_declaration_scopes(decl_var)

        if len(lst_scopes) == 0:
            print(f"Variable {decl_var} is not declared")
            return

        for scope in lst_scopes:
            if self.__is_local_scope(scope):
                print(f"Variable {decl_var} is declared in local scope ({scope})")
            elif self.__is_global_scope(scope):
                print(f"Variable {decl_var} is declared in global scope ({scope})")

    def shadowing_detection(self) -> list[str]:
        """
        Detect the presence of shadowing in the program.
        Shadowing is where a variable or function is redeclared in a subscope, so to check it is necessary to walk up
        the scope graph up to the global scope.

        ALGORITHM:
            * start from a scope with any child, we called 'leaf'
            * check if during the walk up in the scope graph, check if the scope has a declaration of the same name.
            Working with sets, it is enough to check if there is some intersection between the scope's declaration and the scopes' declaration.

        :return: list of shadowed elements
        """
        leafs_scopes = self.__builder.get_leaf_scopes()
        duplication = []

        for leaf in leafs_scopes:
            scope = leaf
            decls = []
            refs = []

            while scope is not None:
                decls.append(self.__builder.get_graph()[scope]["decls"])
                refs.append(self.__builder.get_graph()[scope]["refs"])

                scope = self.__builder.get_graph()[scope]["parent"]

            decls_combinations = list(itertools.combinations(decls, 2))
            refs_combinations = list(itertools.combinations(refs, 2))

            for comb in decls_combinations:
                if len(intersections := comb[0] & comb[1]) > 0: # & operator performs the intersection between sets
                    print(f"Shadowing detected: {list(intersections)}")

                    duplication.append(*intersections)

            for comb in refs_combinations:
                if len(intersections := comb[0] & comb[1]) > 0: # & operator performs the intersection between sets
                    print(f"Shadowing detected: {list(intersections)}")

                    duplication.append(*intersections)

        return duplication

    def local_import_detection(self) -> list[str]:
        """
        This detector aims to detect the presence of local imports. To do so, we check if a scope has references to
        import statements assigned a prefix "import_" to the element added to the scope graph.

        :return: list of scopes with local imports
        """
        scope_with_local_imports = []
        import_regex = re.compile("^import_")

        for scope in self.__builder.get_graph().keys():
            matches = [import_regex.match(ref) for ref in self.__builder.get_graph()[scope]["refs"]]

            if not scope == "s0__main__" and len(matches) > 0 and not all(match is None for match in matches):
                scope_with_local_imports.append(scope)

        return scope_with_local_imports

    def __check_inner_functions(self, scopes_chain: list) -> list|None:
        regex_func = re.compile("^s\\d+_(func|afunc)_.*")
        re_matches = [regex_func.match(scope) for scope in scopes_chain ]

        return re_matches if not all(re_match is None for re_match in re_matches) else None

    def inner_function_detection(self) -> tuple[list, int]:
        """
        This detector aims to detect the presence of inner functions. To do so, we check if there are two local scopes defined by functions.
        The best way is to do so by walking up to the global scope from the leaf scopes (scopes with no children).

        :return: list contains the chain of inner functions. The element in a list is not None if the local scope has been generated by a function.
                 NOTE: the list is ordered from the innermost to the outermost scopes
        """
        def match_filter(lst_matches: list) -> list:
            """
            This function removes the None elements from lists of matches and removes the lists with 2 elements with only one match.

            :param lst_matches: list containing matches
            :return: filtered list of matches
            """
            output = []

            for matches in lst_matches:
                if len(matches) == 2 and all(isinstance(match, re.Match) for match in matches):
                    output.append(matches)
                elif len(matches) > 2:
                    filtered_match = [match for match in matches if match is not None]

                    if len(filtered_match) >=2:
                        output.append(filtered_match)
            return output

        leafs_scopes = self.__builder.get_leaf_scopes()
        inner_functions = []
        total_scopes = 0 # contains the total number of scopes take into account

        for leaf in leafs_scopes:
            scope = leaf
            scopes_branch = []

            while not self.__is_global_scope(scope):
                scopes_branch.append(scope)
                scope = self.__builder.get_graph()[scope]["parent"]

            if len(scopes_branch) >= 2 and (matches := self.__check_inner_functions(scopes_branch)) is not None:
                inner_functions.append(matches)

                total_scopes += len(scopes_branch)

        return match_filter(inner_functions), total_scopes

if __name__ == "__main__":
    detector = Detector("./test/example.py", "test")

    print(detector.shadowing_detection())
    print(detector.local_import_detection())
    print(detector.inner_function_detection())