import itertools

import ast

from pandas.core.computation.expr import intersection

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
        with open(code_path, 'r') as f:
            code = f.read()

        # creating AST
        tree = ast.parse(code)

        # building scope graph
        self.__builder = ScopeGraph()
        self.__builder.visit(tree)

        if not scope_graph_name == "":
            self.__builder.draw(scope_graph_name)

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
        """
        leafs_scopes = self.__builder.get_leaf_scopes()
        duplication = []

        for leaf in leafs_scopes:
            scope = leaf
            decls = []

            while scope is not None:
                decls.append(self.__builder.get_graph()[scope]["decls"])
                scope = self.__builder.get_graph()[scope]["parent"]

            combinations = list(itertools.combinations(decls, 2))

            for comb in combinations:
                if len(intersections := comb[0] & comb[1]) > 0:
                    print(f"Shadowing detected: {list(intersections)}")

                    duplication.append(*intersections)

        return duplication

if __name__ == "__main__":
    detector = Detector("./test/example.py", "test")

    print(detector.shadowing_detection())

