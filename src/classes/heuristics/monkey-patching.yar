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

rule with_statement {
    meta:
        description = "Detection of usage of with statement"

    strings:
        $with_statement = /with\s+/

        $func_open = /with\s+open\s*/
        $func_lock = /with\s+Lock\s*/
        $func_RLock = /with\s+RLock\s*/
        $func_temp_file = /with\s+TemporaryFile\s*/
        $func_named_temp_file = /with\s+NamedTemporaryFile\s*/
        $func_temp_dir = /with\s+TemporaryDirectory\s*/
        $func_closing = /with\s+closing\s*/
        $func_suppress = /with\s+suppress\s*/
        $func_redirect1 = /with\s+redirect_stdout\s*/
        $func_redirect2 = /with\s+redirect_stderr\s*/
        $func_exitstack = /with\s+ExitStack\s*/
        $func_nullcontext = /with\s+nullcontext\s*/
        $func_url_open = /with\s+urlopen\s*/
        $func_connect = /with\s+connect\s*/
        $func_cursor = /with\s+Cursor\s*/
        $func_session = /with\s+Session\s*/
        $func_scandir = /with\s+scandir\s*/
        $func_zip = /with\s+ZipFile\s*/
        $func_tar = /with\s+TarFile\s*/
        $func_requests = /with\s+requests\s*/
        $func_image = /with\s+Image\s*/
        $func_localcontext = /with\s+localcontext\s*/
        $func_condition = /with\s+Condition\s*/
        $func_no_grad = /with\s+no_grad\s*/
        $func_autocast = /with\s+autocast\s*/
        $func_errstate = /with\s+errstate\s*/
        $func_styler = /with\s+style\s*/
        $func_context = /with\s+context\s*/

    condition:
        $with_statement and 0 of ($func_*)
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