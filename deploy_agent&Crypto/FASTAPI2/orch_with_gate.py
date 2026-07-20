# orchestrator.py

import json
from typing import Tuple
from Classifier_agnet import IntentClassifierCALL
from function_selector import functionSelectorCALL
from Global_Resolver import ResolverCall
from Rephraser import RephraserCALL
from system_init import get_enum_arguments
from temp_info_agent import answer_user_question
from state import initial_state
from llmGate import MessageValidatorCALL

class ConversationOrchestrator:

    # ---------- VALIDATOR ----------
    def LLM_VALIDATOR(self, llm_name: int, llm_response: str):
        print(f"[DEBUG][VALIDATOR] LLM {llm_name} raw response: {llm_response}")

        try:
            data = json.loads(llm_response)
        except json.JSONDecodeError:
            print(f"[DEBUG][VALIDATOR] JSON decode failed for LLM {llm_name}")
            return False
        print("===========debug==============================")
        print(data)
        if llm_name == 1:
            valid = (
                "type" in data
                and "intent" in data
               and data["intent"] in {
                "ACCOUNT",
                "TRANSFER",
                "JARS",
                "CALENDAR",
                "EXCHANGE",
                "LOAN",
                "General_Exchange",
                "OTHER",
                "UNSUPPORTED",
                " ",
            }
            )
            
            
            print(f"[DEBUG][VALIDATOR] Intent validator result: {valid}")
            return valid

        if llm_name == 2:
            valid = (
                "chosen_function" in data
                and "provided_arguments" in data
                and "missing_arguments" in data
            )
            print(f"[DEBUG][VALIDATOR] Function selector validator result: {valid}")
            return valid

        if llm_name == 3:
            valid = (
                "action" in data
                and "updated_arguments" in data
                and "remaining_missing_arguments" in data
            )
            print(f"[DEBUG][VALIDATOR] Resolver validator result: {valid}")
            return valid

        return False
    def Gate_validated(self,message: str) -> Tuple[int, str]:
        """
        Calls the validator agent and extracts:
        - isForward: int (0 or 1)
        - validatorOutput: str (response to user, may be empty)

        Raises ValueError if output is invalid.
        """

        raw_response = MessageValidatorCALL(message)

        try:
            # In case the model returns a string
            if isinstance(raw_response, str):
                parsed = json.loads(raw_response)
            else:
                parsed = raw_response

            isForward = int(parsed.get("isForward", 0))
            validatorOutput = parsed.get("response", "")

            if isForward not in (0, 1):
                raise ValueError("Invalid isForward value")

            if not isinstance(validatorOutput, str):
                raise ValueError("Invalid response value")

            return isForward, validatorOutput

        except (json.JSONDecodeError, TypeError, ValueError) as e:
            # Fail closed: do NOT forward on malformed output
            return 0, "I can only help with banking-related requests."
    # ---------- INTENT ----------
    def intent_classify(self, state: dict, user_message: str) -> dict:
        print(f"[DEBUG][INTENT] User message: {user_message}")

        response = IntentClassifierCALL(user_message)
        print(f"[DEBUG][INTENT] Initial classifier response: {response}")

        for attempt in range(3):
            if self.LLM_VALIDATOR(1, response):
                break
            print(f"[DEBUG][INTENT] Retry {attempt + 1}")
            response = IntentClassifierCALL(user_message)
        else:
            state["error_message"] = "INTERNAL LLM FAILURE  : intent classifier llm could not return valid output  "
            response = '{"type": "UNCERTAIN", "intent": null}'
            print(f"[DEBUG][INTENT] Fallback triggered")
            return False

        parsed = json.loads(response)
        print(f"[DEBUG][INTENT] Parsed intent: {parsed}")

        state["currentIntentType"] = parsed.get("type")
        state["currentIntent"] = parsed.get("intent")

        if state["currentIntent"] == "UNSUPPORTED":
            state["Status"] = "UNSUPPORTED_ACTION"
            state["error_code"] = 0
            state["error_message"] = "Unsupported Action Requested"

        elif (
            state["currentIntent"] == "UNCERTAIN"
            or state["currentIntent"] == "null"
            or state["currentIntent"] is None
            or state["currentIntent"] == " "
        ):
            state["Status"] = "UNCERTAIN_ACTION"
            state["error_code"] = 0.1
            state["error_message"] = " The intent classifier Could not understand the user intent"

        else:
            state["Status"] = "INTENT_COLLECTED"

        print(f"[DEBUG][INTENT] Updated state: {state}")
        return state

    # ---------- FUNCTION SELECTOR (validated) ----------
    def validated_function_selector(self, user_message: str, intent: str, state: dict):
        print(f"[DEBUG][FUNC_SELECTOR] Intent: {intent}")
        print(f"[DEBUG][FUNC_SELECTOR] User message: {user_message}")

        raw = functionSelectorCALL(user_message, intent)
        print(f"[DEBUG][FUNC_SELECTOR] Initial response: {raw}")

        for attempt in range(3):
            if self.LLM_VALIDATOR(2, raw):
                break
            print(f"[DEBUG][FUNC_SELECTOR] Retry {attempt + 1}")
            raw = functionSelectorCALL(user_message, intent)
        else:
            state["error_message"] = "INTERNAL LLM FAILURE  : function_selector llm could not return valid output  "
            print(f"[DEBUG][FUNC_SELECTOR] Fallback triggered")
            return {
                "chosen_function": None,
                "provided_arguments": {},
                "missing_arguments": []
            }

        parsed = json.loads(raw)
        print(f"[DEBUG][FUNC_SELECTOR] Parsed result: {parsed}")
        return parsed

    # ---------- RESOLVER (validated) ----------
    def validated_resolver(self, state: dict, user_message: str):
        print(f"[DEBUG][RESOLVER] Current state: {state}")
        print(f"[DEBUG][RESOLVER] User message: {user_message}")

        raw = ResolverCall(
            state=state,
            user_message=user_message,
            last_question=state.get("lastResponse")
        )
        print(f"[DEBUG][RESOLVER] Initial response: {raw}")

        parsed = json.loads(raw)

        for attempt in range(3):
            if self.LLM_VALIDATOR(3, raw):
                break
            print(f"[DEBUG][RESOLVER] Retry {attempt + 1}")
            raw = ResolverCall(
                state=state,
                user_message=user_message,
                last_question=state.get("lastResponse")
            )
            parsed = json.loads(raw)
        else:
            state["error_message"] = "INTERNAL LLM FAILURE  : Resolver llm could not return valid output  "
            print(f"[DEBUG][RESOLVER] Fallback triggered")
            return {
                "action": None,
                "updated_arguments": {},
                "remaining_missing_arguments": state.get("missing_arguments", [])
            }

        print(f"[DEBUG][RESOLVER] Parsed result: {parsed}")

        if parsed.get("action") == "REJECT":
            state["error_message"] = " Resolver Rejected , there are still missing arguments "
            state["error_code"] = 2.1

        elif parsed.get("action") == "AMBIGUOUS":
            state["error_message"] = " Resolver Could not identify an argument clearly "
            state["error_code"] = 2.2

        elif parsed.get("action") == "ABORT":
            state["Status"]="ABORT"
            state["error_message"] = "Resolver detected an intent or flow change  "
            state["error_code"] = 2.3
            return "ABORT"

        return parsed

    # ---------- MAIN ENTRY ----------
    def respond(self, state: dict, user_message: str):
        print(f"\n[DEBUG][RESPOND] Incoming user message: {user_message}")
        print(f"[DEBUG][RESPOND] Initial state: {state}")

        state["conversation_stack"].append({
            "sender": "user",
            "message": user_message
        })
        
        if state["Status"] == "Collecting_Intent":
            print("==============DEBUG=============")
            print(user_message)
            isForward,GateResponse=self.Gate_validated(user_message)
            if isForward==0:
                state["currentIntentType"]="Chatting"
                return state,GateResponse
            print("==============Forwarded=============")
            
            print("[DEBUG][RESPOND] Collecting intent")
            state = self.intent_classify(state, user_message)

        if state["Status"] == "INTENT_COLLECTED":
            print("[DEBUG][RESPOND] Intent collected")

            if state["currentIntentType"] == "General":
                print("[DEBUG][RESPOND] General intent detected")
                answer = answer_user_question(user_message)
                return initial_state(), answer

            if (
                state["currentIntentType"] == "Personal"
                and state["currentIntent"] not in ["OTHER", "MULTI_INTENT", None, ""]
            ) or state["currentIntent"] == "General_Exchange":

                print("[DEBUG][RESPOND] Running function selector")

                fs = self.validated_function_selector(
                    user_message=user_message,
                    intent=state["currentIntent"],
                    state=state
                )

                state["selected_function"] = fs.get("chosen_function")
                state["provided_arguments"] = fs.get("provided_arguments", {})
                state["missing_arguments"] = fs.get("missing_arguments", [])

                print(f"[DEBUG][RESPOND] Selected function: {state['selected_function']}")
                print(f"[DEBUG][RESPOND] Provided args: {state['provided_arguments']}")
                print(f"[DEBUG][RESPOND] Missing args: {state['missing_arguments']}")

                if (
                    state["selected_function"] is None
                    or state["selected_function"] == "null"
                    or state["selected_function"] == " "
                ):
                    state["Status"] = "UNCERTAIN_INTENT"
                    state["error_code"] = 1
                else:
                    state["Status"] = "Function_Selected"
                    if not state["missing_arguments"]:
                        
                        state["Status"] = "Ready_to_execute"
                        return state , "READY_TO_EXECUTE 010"

            else:
                
                state["Status"] = "UNCERTAIN_INTENT"

        if state["Status"] == "Missing_Arguments":
            print("[DEBUG][RESPOND] Resolving missing arguments")

            resolver = self.validated_resolver(state, user_message)
            if resolver=="ABORT":
                return state,"New chat is started , تم بدأ محادثة جديدة"
            state["provided_arguments"].update(
                resolver.get("updated_arguments", {})
            )
            state["missing_arguments"] = resolver.get(
                "remaining_missing_arguments", state["missing_arguments"]
            )

            print(f"[DEBUG][RESPOND] Updated args: {state['provided_arguments']}")
            print(f"[DEBUG][RESPOND] Remaining missing args: {state['missing_arguments']}")

            if not state["missing_arguments"]:
                state["Status"] = "Ready_to_execute"
                return state , "READY_TO_EXECUTE 010"

        rephraser_state = {
            "status": state["Status"],
            "missing_arguments": state.get("missing_arguments", []),
            "error_message": state.get("error_message")
        }

        if state["Status"] == "Function_Selected" and state["missing_arguments"]:
            state["Status"] = "Missing_Arguments"

        if state["missing_arguments"]:
            enums = get_enum_arguments(name=state["selected_function"])
        else:
            enums = " "

        print(f"[DEBUG][RESPOND] Rephraser state: {rephraser_state}")
        print(f"[DEBUG][RESPOND] Enums: {enums}")

        response = RephraserCALL(rephraser_state, user_message, enums)
        state["lastResponse"] = response

        print(f"[DEBUG][RESPOND] Final response: {response}")
        print(f"[DEBUG][RESPOND] Final state: {state}")

        return state, response
