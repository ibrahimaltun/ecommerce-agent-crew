import os
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

# ? ======================================================
# LOCAL MODEL with Ollama Endpoint
# ? ======================================================

llm_model = ChatOllama(
    model="qwen2.5-coder:14b",
    temperature=0.1,
    num_ctx=16384  # 16k context window
)

# * ======================================================
# LOCAL TOOLS
# * ======================================================


@tool
def write_file(file_path: str, content: str) -> str:
    """write content to file path"""
    try:
        os.makedirs(os.path.dirname(file_path),
                    exist_ok=True) if os.path.dirname(file_path) else None
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Succesful: {file_path} was created and saved."

    except Exception as e:
        return f"Error: It error is raising while write to file"


@tool
def read_file(filepath: str) -> str:
    """read filepath"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    except Exception as e:
        return f"Error: while rea the file"

# ~ ======================================================
# Tool Binding
# ~ ======================================================


tools = [write_file, read_file]
llm_with_tools = llm_model.bind_tools(tools)


# ! ======================================================
# STATE SCHEMA
# ! ======================================================

class AgentState(TypedDict):
    # add_messages, accumulate historical messages
    messages: Annotated[list[BaseMessage], add_messages]

# ? ======================================================
# NODES
# ? ======================================================


def reasoning_agent_node(state: AgentState) -> dict:
    """Reasoning Step"""
    sys_prompt = SystemMessage(
        content=(
            "Sen local bir yazılım mimarı ve otonom geliştiricisin. "
            "Kullanıcının isteklerini karşılamak için sana sağlanan araçları (tools) etkili bir şekilde kullan. "
            "Bir dosya oluşturman istendiğinde doğrudan 'write_file' aracını çağır."
        )
    )
    messages = [sys_prompt] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


# LangGraph's ToolNode class - node that works tools
tool_execution_node = ToolNode(tools=tools)

# - ======================================================
# GRAPH CONSTRUCTION
# - ======================================================
workflow = StateGraph(AgentState)

# add nodes
workflow.add_node("agent", reasoning_agent_node)
workflow.add_node("tools", tool_execution_node)

# start point
workflow.set_entry_point("agent")

# Conditional Edge
# if the model request a 'Tool Calling' so go to 'tools' node
# if it is normal response so end process
workflow.add_conditional_edges(
    "agent",
    tools_condition,
    {
        "tools": "tools",
        END: END
    }
)

# Loop/Cycle, after the model run, recall the model to evaluate the output
workflow.add_edge("tools", "agent")

# Compile the graph
app = workflow.compile()

# * ============================
# Execution Loop
# * ============================

if __name__ == "__main__":
    user_query = "Local ortamda kullanılmak üzere 'output/math_utils.py' adında bir Python dosyası oluştur ve içine faktöriyel hesaplayan optimizasyonlu bir fonksiyon yaz."

    print(f"--- Görev Başlatıldı: {user_query} ---\n")

    inputs = {"message": [HumanMessage(content=user_query)]}

    for event in app.stream(inputs, stream_mode="values"):
        last_message = event["messages"][-1]
        print(f"[{last_message.type.upper()}]: {last_message.content}")
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            print(f"--> [TOOL CALL]: {last_message.tool_calls}")
        print("-" * 50)
