import json
import os
from classifier_agent import IntentClassifierINIT
from function_selector import FunctionSelectorINIT
from retriever import retrievalINIT

_SYSTEM_INITIALIZED = False

# Mapping of categories to their function files
FUNCTION_FILES = {
    "JARS": "jars_functions.txt",
    "ACCOUNT": "account_functions.txt",
    "TRANSFER": "transfer_functions.txt",
    "CALENDAR": "calendar_functions.txt",
    "EXCHANGE": "exchange_functions.txt",
    "LOAN": "loan_functions.txt",
    "GENERAL_EXCHANGE": "general_exchange_functions.txt",
}

# Global map to store function name -> function JSON
FUNCTION_MAP = {}
def _load_functions():
    """
    Loads all function definitions from files and maps them by function name.
    """
    global FUNCTION_MAP
    for category, filepath in FUNCTION_FILES.items():
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found!")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()

            # Wrap content in a list if it's not a proper JSON array
            if not content.startswith("["):
                content = f"[{content}]"

            # Remove trailing commas that break JSON parsing
            content = content.replace(",\n\n]", "]").replace(",\n]", "]")
            
            try:
                functions = json.loads(content)
                for func in functions:
                    name = func.get("name")
                    if name:
                        FUNCTION_MAP[name] = func
            except json.JSONDecodeError as e:
                print(f"Error parsing {filepath}: {e}")
def get_function_by_name(name: str):
    """
    Returns the full function JSON for a given function name, or None if not found.
    """
    return FUNCTION_MAP.get(name)

def get_enum_arguments(name: str):
    """
    Returns the ENUM_Arguments dict for a given function name, or None if not present.
    """
    func = FUNCTION_MAP.get(name)
    if func:
        return func.get("ENUM_Arguments")
    return None

def system_init():
    global _SYSTEM_INITIALIZED
    if _SYSTEM_INITIALIZED:
        return
    
    # Initialize modules
    FunctionSelectorINIT()
    IntentClassifierINIT()
    retrievalINIT()

    # Load function definitions
    _load_functions()

    _SYSTEM_INITIALIZED = True

# Example usage
if __name__ == "__main__":
    system_init()
    
    fn_name = "create_calendar_payment"
    fn = get_function_by_name(fn_name)
    enums = get_enum_arguments(fn_name)
    
    print(f"Function {fn_name}:")
    print(json.dumps(fn, indent=2))
    print("\nENUM_Arguments:")
    print(json.dumps(enums, indent=2))
