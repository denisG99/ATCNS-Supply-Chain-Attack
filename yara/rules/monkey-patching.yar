rule patch_decorator {
    meta:
        description = "Monkey patching through patch decorator"

    strings:
        $decorator = "from unittest.mock import patch"

    condition:
        $decorator
}