import os
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from config import OLLAMA_BASE_URL, OLLAMA_LLM_MODEL
MODEL_NAME = OLLAMA_LLM_MODEL
llm = OllamaLLM(
    model=MODEL_NAME,
    base_url=OLLAMA_BASE_URL,
    temperature=0.0,
    num_ctx=2048,
    stream=False,
)
template = """You are a function selector.

You receive:
- A user message
- A list of available functions, structured as objects with:
  - name
  - description
  - parameters (with type)
  - optional required array defining mandatory parameters

Your task:
1. Select exactly one function whose intent most specifically matches the user’s request.
2. Extract argument values only if they are explicitly stated or unambiguously implied by the user message.
3. Use only the function schema to determine which parameters are required.
4. If the intent matches a function but required parameters are missing, still select the function and list the missing parameters.
5. If no function clearly matches the user’s intent, return null.

Argument rules:
- Do not guess, infer hidden intent, fabricate values, or transform user input.
- If a value is uncertain, ambiguous, or inferred from context alone, treat it as missing.
- If a provided value does not match the parameter’s declared type or allowed values in the ENUM_ARGUMENTS field (if present), treat it as missing.
- Only extract parameters defined in the selected function’s parameters.

Disambiguation rules:
- If multiple functions could match, choose the most specific one based on the description.
- If two functions are equally specific, choose the one with more required parameters satisfied.
- Do not select multiple functions.

Output rules:
- Output JSON only.
- Do not include explanations, comments, or markdown.
- If chosen_function is null, provided_arguments must be empty and missing_arguments must be [].

Output format:
{{
  "chosen_function": string | null,
  "provided_arguments": {{ "param": value }},
  "missing_arguments": [ "param" ]
}}

"""

prompt=ChatPromptTemplate.from_template(template)

chain=prompt | llm
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

#model=OllamaLLM(model="qwen3:1.7b")

#prompt=ChatPromptTemplate.from_template(template)

#chain=prompt | model
MODEL_NAME = OLLAMA_LLM_MODEL
llm = OllamaLLM(
    model=MODEL_NAME,
    base_url=OLLAMA_BASE_URL,
    temperature=0.0,
    num_ctx=2048,
    stream=False,
)
functions_by_category = {}
def FunctionSelectorINIT():
    
    import os
        
    category_files = {
        "JARS": "jars_functions.txt",
        "ACCOUNT": "account_functions.txt",
        "TRANSFER": "transfer_functions.txt",
        "CALENDAR": "calendar_functions.txt",
        "EXCHANGE": "exchange_functions.txt",
        "LOAN":"loan_functions.txt",
        "GENERAL_EXCHANGE": "general_exchange_functions.txt",
    }

    global functions_by_category
    for category, file_name in category_files.items():
        if not os.path.exists(file_name):
            raise FileNotFoundError(f"Functions file not found: {file_name}")

        with open(file_name, "r", encoding="utf-8") as f:
            functions_by_category[category] = f.read()


def functionSelectorCALL(user_message: str, category: str) -> dict:
    """
    Function selector wrapper.

    Args:
        user_message (str): User input message (untrusted).
        category (str): One of ["JARS", "ACCOUNT", "TRANSFER", "CALENDAR", "EXCHANGE", "GENERAL_EXCHANGE"]

    Returns:
        dict: JSON result with chosen_function, provided_arguments, missing_arguments.
    """
    
    functions=functions_by_category[category]
    prompt = f"""{template}

    user_message:
    {user_message}
    
    list of available functions: {functions}

    Return ONLY valid JSON (no markdown, no extra text).
    """

    response = llm.invoke(prompt)
    return response

#functions=""
#with open("jars_functions.txt", "r", encoding="utf-8") as f:
    #functions = f.read()

#while True:
    #print("--------")
   # m = input("how can i help you? ")

    #if m.strip().lower() in ["q", "ق"]:
       # break

   # result = chain.invoke({
        # "user_message": m,
         
        # "functions":functions
    #})

   # print(result)

    #with open("a.txt", "w", encoding="utf-8") as f:
       # f.write(str(result))



