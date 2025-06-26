import os

def run_script(script_code, function_to_run):
    cmd = (
        "/usr/bin/gimp-3.0 -i --batch-interpreter=plug-in-script-fu-eval -b - << EOF"
        "" + script_code + " "
        "" + function_to_run + " "
        "(gimp-quit 0))"
        "EOF"
    )
    os.system(cmd)
