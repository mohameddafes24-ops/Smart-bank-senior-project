from fastapi import FastAPI
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Any, Dict, Optional
from fastapi.middleware.cors import CORSMiddleware
from orch_with_gate import ConversationOrchestrator
from system_init import system_init
from state import initial_state   
from payments import router as payments_router 
from webhook import router as webhook_router
# -------------------------------------------------------------------
# App & Orchestrator
# -------------------------------------------------------------------

orchestrator = ConversationOrchestrator()

@asynccontextmanager
async def lifespan(app: FastAPI):
    system_init()
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # must be False with "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(payments_router)
app.include_router(webhook_router)

# -------------------------------------------------------------------
# Request / Response models
# -------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    state: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: Any                  # can be str or JSON
    isUpdated: bool                # should backend persist state?
    state: Dict[str, Any]          # new state returned back


# -------------------------------------------------------------------
# Chat endpoint
# -------------------------------------------------------------------

@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    # ✅ If no state provided, start with initial_state()
    state = payload.state or initial_state()
    print("================= State Debug===========")
    print(state)
    new_state, agent_response = orchestrator.respond(state, payload.message)

    # -------------------------------------------------------------
    # Decision rules (same behavior as your old service version)
    # -------------------------------------------------------------

    # 1) General -> reset state and tell backend to update
    if new_state.get("currentIntentType") == "General":
        return ChatResponse(
            response=agent_response,
            isUpdated=True,
            state=initial_state()
        )
    if new_state.get("Status")=="ABORT":
        return ChatResponse(
            response=agent_response,
            isUpdated=True,
            state=initial_state()
        )
    # 2) Ready_to_execute -> return details + reset state
    if new_state.get("Status") == "Ready_to_execute":
        return ChatResponse(
            response={
                "response": agent_response,
                "function_selected": new_state.get("selected_function"),
                "provided_arguments": new_state.get("provided_arguments", {})
            },
            isUpdated=True,
            state=initial_state()
        )

    # 3) Chatting / UNCERTAIN -> no need to persist state
    if new_state.get("currentIntentType") in ("Chatting", "UNCERTAIN"):
        return ChatResponse(
            response=agent_response,
            isUpdated=True,
            state=initial_state()
        )

    # 4) Otherwise -> backend should store updated state
    return ChatResponse(
        response=agent_response,
        isUpdated=True,
        state=new_state
    )
