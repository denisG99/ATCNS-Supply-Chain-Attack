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