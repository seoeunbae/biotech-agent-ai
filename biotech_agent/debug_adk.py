import sys
import traceback

print("Starting debug script...")
try:
    print("Importing google.adk.cli.cli_tools_click...")
    from google.adk.cli import cli_tools_click
    print("Import successful.")
    print("Calling main with --help...")
    try:
        cli_tools_click.main(['--help'], standalone_mode=False)
    except SystemExit as e:
        print(f"SystemExit caught: {e}")
except Exception:
    print("Exception occurred:")
    traceback.print_exc()
except SystemExit:
    print("SystemExit during import?")
    traceback.print_exc()
