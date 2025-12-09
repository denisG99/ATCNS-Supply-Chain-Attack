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
        $import = "from contextlib import contextmanager"

    condition:
        $import
}

rule contextmanager_usage {
    meta:
        description = "Detection of usage of contextmanager decorator"

    strings:
        $decorator = "@contextmanager"

    condition:
        $decorator
}

rule with_statement {
    meta:
        description = "Detection of usage of with statement"

    strings:
        $with_regex = /with\s+[A-Za-z_][A-Za-z0-9_\.]*\s*(\(|as\b)/

        $open = "open"
        $lock = "Lock"
        $RLock = "RLock"
        $temp_file = "TemporaryFile"
        $named_temp_file = "NamedTemporaryFile"
        $temp_dir = "TemporaryDirectory"
        $closing = "closing"
        $suppress = "suppress"
        $redirect1 = "redirect_stdout"
        $redirect2 = "redirect_stderr"
        $exitstack = "ExitStack"
        $nullcontext = "nullcontext"
        $url_open = "urlopen"
        $connect = "connect"
        $cursor = "Cursor"
        $session = "Session"
        $scandir = "scandir"
        $zip = "ZipFile"
        $tar = "TarFile"
        $requests = "requests"
        $image = "Image"
        $localcontext = "localcontext"
        $condition = "Condition"
        $no_grad = "no_grad"
        $autocast = "autocast"
        $errstate = "errstate"
        $styler = "style"
        $context = "context"

    condition:
        $with_regex and not any of ($*)
}
