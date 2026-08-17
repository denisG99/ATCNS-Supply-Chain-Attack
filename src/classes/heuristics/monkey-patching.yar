rule patch_decorator_import {
    meta:
        description = "Detection of import of patch decorator"

    strings:
        $import = "from unittest.mock import patch"

    condition:
        $import
}

rule patch_decorator_usage {
    meta:
        description = "Detection of usage of patch decorator"

    strings:
        $decorator = "@patch"

    condition:
        $decorator
}

rule contextmanager_import {
    meta:
        description = "Detection of import of contextmanager decorator"

    strings:
        $import1 = "from contextlib import contextmanager"
        $import2 = "import contextlib"

    condition:
        $import1 or $import2
}

rule contextmanager_usage {
    meta:
        description = "Detection of usage of contextmanager decorator"

    strings:
        $decorator1 = "@contextmanager"
        $decorator2 = "@contextlib.contextmanager"

    condition:
        $decorator1 or $decorator2
}

rule overwrite_method_class{
    meta:
        description = "Detection variables swap inside a class. This way allow attacker to evade detector"

     strings:
        $save    = /\b[_a-zA-Z][_a-zA-Z0-9]*\s*=\s*self\.[_a-zA-Z][_a-zA-Z0-9]*/
        $nested  = /\bdef\s+[_a-zA-Z][_a-zA-Z0-9]*\s*\([^)]*\)\s*:/
        $patch   = /\bself\.[_a-zA-Z][_a-zA-Z0-9]*\s*=\s*[_a-zA-Z][_a-zA-Z0-9]*/
        $call    = /\bself\.[_a-zA-Z][_a-zA-Z0-9]*\s*\(/
        $restore = /\bself\.[_a-zA-Z][_a-zA-Z0-9]*\s*=\s*original[_a-zA-Z0-9]*/

    condition:
        $save and $nested and $patch and $call and $restore
        and for any j in (1..#nested) : (
            for any k in (1..#patch) : (
                for any l in (1..#call) : (
                    for any m in (1..#restore) : (
                        @save[1] < @nested[j] and
                        @nested[j] < @patch[k] and
                        @patch[k] < @call[l] and
                        @call[l] < @restore[m]
                    )
                )
            )
        )
}