from dotenv import load_dotenv
load_dotenv()

from typing import TypedDict, Literal, List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import DirectoryLoader
from langchain.schema import Document
from langgraph.prebuilt import create_react_agent
from langgraph.graph import START, StateGraph, END


# --- State ---
class AgentState(TypedDict):
    user_query: str
    answer: str
    agent_used: str


# --- LLM ---
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.5,
)

# --- Tools (for search agent) ---
tools = [TavilySearch(max_results=5)]


# --- Search Agent ---
def search_agent(state: AgentState) -> AgentState:
    print("\n--- Search Agent ---")
    agent = create_react_agent(model=llm, tools=tools)
    result = agent.invoke({"messages": [("user", state["user_query"])]})
    state["answer"] = result["messages"][-1].content
    state["agent_used"] = "Search"
    return state


# --- Math Agent ---
def math_agent(state: AgentState) -> AgentState:
    """A math-solving agent that uses the LLM to process and solve math problems."""
    print("\n--- Math Node ---")
    prompt = f"Solve this math problem and return only the answer: {state['user_query']}"
    response = llm.invoke(prompt)
    state["answer"] = response.content.strip()
    state["agent_used"] = "Math"
    return state


# --- RAG Setup ---
def build_retriever():
    loader = DirectoryLoader("data/", glob="*.txt")
    docs = loader.load()
    if not docs:
        print("⚠️ No documents found in ./data folder. RAG will return empty answers.")

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name="docs"
    )
    return vectorstore.as_retriever(search_kwargs={"k": 3})


retriever = build_retriever()


# --- RAG Agent (with sentinel & fallback signal) ---
def rag_agent(state: AgentState) -> AgentState:
    """Retrieval-Augmented Generation (RAG) Agent.
    If no/insufficient docs, set answer=None so the graph can fall back to Search.
    """
    print("\n--- RAG Agent ---")
    query = state["user_query"]

    docs: List[Document] = retriever.invoke(query)
    if not docs:
        print("⚠️ RAG: No relevant documents found.")
        state["answer"] = None
        state["agent_used"] = "RAG"
        return state

    context = "\n\n".join([d.page_content for d in docs])

    prompt = f"""
    You are a retrieval-augmented assistant. Answer using ONLY the context below.
    If the context is insufficient to answer the question, reply with EXACTLY:
    NOT_ENOUGH_CONTEXT
    (no extra words, punctuation, or explanation).

    # Context:
    {context}

    # Question:
    {query}
    """
    response = llm.invoke(prompt)
    raw = (response.content or "").strip()

    # Sentinel: trigger fallback
    if raw == "NOT_ENOUGH_CONTEXT":
        print("⚠️ RAG: Insufficient context → signaling fallback")
        state["answer"] = None
        state["agent_used"] = "RAG"
        return state

    # Otherwise we have a real answer
    state["answer"] = raw
    state["agent_used"] = "RAG"
    return state


# --- Input Node ---
#def input_agent(state: AgentState) -> AgentState:
#    print("\n--- Input Node ---")
    # If a caller (like FastAPI) provided a query, skip CLI prompt.
#    if state.get("user_query"):
#        state["answer"] = None
#        state["agent_used"] = ""
#        return state

    # (Optional) CLI path if you ever run interactively
#    query = input("Input user query (or type 'exit' to quit): ")
#    if query.lower() == "exit":
#        print("Goodbye! 👋")
#        exit(0)
#    state["user_query"] = query
#    state["answer"] = None
#    state["agent_used"] = ""
#    return state

def input_agent(state: AgentState) -> AgentState:
    # Skip prompt if provided by HTTP
    if state.get("user_query"):
        state["answer"] = None
        state["agent_used"] = ""
        return state

    # (Optional CLI; can delete if you never use it)
    query = input("Input user query (or type 'exit' to quit): ")
    if query.lower() == "exit":
        raise SystemExit(0)
    state["user_query"] = query
    state["answer"] = None
    state["agent_used"] = ""
    return state


# --- Route Decider (router function ONLY; not a node) ---
def route_decider(state: AgentState) -> Literal["math_agent", "rag_agent"]:
    """
    Initial routing (LLM-driven) with RAG-first design:
    - Math → math_agent
    - Everything else → rag_agent (Search is reserved for fallback after RAG)
    """
    prompt = f"""
    You are a router agent. Choose the best initial agent for the user query below.
    You MUST choose ONLY one of: math_agent or rag_agent (do NOT choose search_agent here).

    Query: {state['user_query']}

    Agent descriptions:
    - math_agent: solves any calculation or numeric problem, including when written in words (e.g., "divide ten by two").
    - rag_agent: answers from local documents (knowledge base). If RAG fails later, the graph will fall back to search automatically.

    Rules:
    - If the query is any kind of calculation or math (even in words), choose math_agent.
    - Otherwise choose rag_agent.

    Respond with just the agent name.
    """
    response = llm.invoke(prompt)
    decision = response.content.strip().lower()
    if "math" in decision:
        print("🤖 RouteDecider (LLM): chose math_agent")
        return "math_agent"
    else:
        print("🤖 RouteDecider (LLM): chose rag_agent")
        return "rag_agent"


# --- After-RAG Conditional (decide next hop) ---
def rag_followup(state: AgentState) -> Literal["search_agent", "END"]:
    """
    If RAG produced an answer → END.
    If RAG failed (answer is None) → go to search_agent.
    """
    if state.get("answer") is None:
        print("🔄 RAG follow-up: no answer → routing to search_agent")
        return "search_agent"
    return "END"


# --- Graph Workflow ---
workflow = StateGraph(AgentState)

# Nodes
workflow.add_node("input_agent", input_agent)
workflow.add_node("math_agent", math_agent)
workflow.add_node("rag_agent", rag_agent)
workflow.add_node("search_agent", search_agent)

# Edges
workflow.add_edge(START, "input_agent")

# Conditional route straight from input_agent (no route_decider node)
workflow.add_conditional_edges("input_agent", route_decider)

# Math finishes
workflow.add_edge("math_agent", END)

# RAG: either END or fallback to Search
workflow.add_conditional_edges(
    "rag_agent",
    rag_followup,
    {"search_agent": "search_agent", "END": END},
)

# Search finishes
workflow.add_edge("search_agent", END)

app = workflow.compile()


# --- Run workflow loop ---
#if __name__ == "__main__":
#    while True:
#        result = app.invoke({})
#        print(f"\n--- Final Output ({result.get('agent_used', 'Unknown')}) ---")
#        print(result["answer"])
#        print("\n----------------------------------------\n")
