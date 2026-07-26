# state.py

def initial_state():
    return {
        # ---- Core flow control ----
        "Status": "Collecting_Intent",

        # ---- Intent classification ----
        "currentIntent": None,
        "currentIntentType": None,

        # ---- Function selection ----
        "selected_function": None,
        "provided_arguments": {},
        "missing_arguments": [],

        # ---- Error handling ----
        "error_message": "",
        "error_code": None,

        # ---- Conversation memory ----
        "conversation_stack": [],
        "lastResponse": ""
    }
