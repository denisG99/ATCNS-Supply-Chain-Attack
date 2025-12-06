import yara

if __name__ == "__main__":
    var1="prova"
    var2="prova"

    variable_rules = yara.compile("./rules/variables.yar", externals={'url1': var1, 'url2': var2})
    monkeypatching_rules = yara.compile("./rules/monkey-patching.yar")

    print(variable_rules.match("./test.py"))
    print(monkeypatching_rules.match("./test.py"))