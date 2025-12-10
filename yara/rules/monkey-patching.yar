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
        $open = /with\s+open\s*/
        $lock = /with\s+Lock\s*/
        $RLock = /with\s+RLock\s*/
        $temp_file = /with\s+TemporaryFile\s*/
        $named_temp_file = /with\s+NamedTemporaryFile\s*/
        $temp_dir = /with\s+TemporaryDirectory\s*/
        $closing = /with\s+closing\s*/
        $suppress = /with\s+suppress\s*/
        $redirect1 = /with\s+redirect_stdout\s*/
        $redirect2 = /with\s+redirect_stderr\s*/
        $exitstack = /with\s+ExitStack\s*/
        $nullcontext = /with\s+nullcontext\s*/
        $url_open = /with\s+urlopen\s*/
        $connect = /with\s+connect\s*/
        $cursor = /with\s+Cursor\s*/
        $session = /with\s+Session\s*/
        $scandir = /with\s+scandir\s*/
        $zip = /with\s+ZipFile\s*/
        $tar = /with\s+TarFile\s*/
        $requests = /with\s+requests\s*/
        $image = /with\s+Image\s*/
        $localcontext = /with\s+localcontext\s*/
        $condition = /with\s+Condition\s*/
        $no_grad = /with\s+no_grad\s*/
        $autocast = /with\s+autocast\s*/
        $errstate = /with\s+errstate\s*/
        $styler = /with\s+style\s*/
        $context = /with\s+context\s*/

    condition:
        0 of ($*)
}
