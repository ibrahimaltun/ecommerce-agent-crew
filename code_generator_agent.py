"""
MultiAgent System
"""

from typing import Annotated, TypedDict
from pydantic import BaseModel, Field


# Rich Kütüphanesi Bileşenleri (Terminal UI)
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.rule import Rule


from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages


console = Console()

# ==========================================
# STRUCTURED OUTPUT ŞEMASI (Pydantic)
# ==========================================


class CodeReviewResult(BaseModel):
    is_approved: bool = Field(
        description="Kod tüm gereksinimleri karşılıyorsa True, düzeltilmesi gereken hata/eksik varsa False."
    )
    feedback: str = Field(
        description="Kod onaylandıysa tebrik/özet mesajı; onaylanmadıysa Developer'ın düzeltmesi gereken spesifik noktalar."
    )


# ==========================================
# LOCAL LLM VE STRUCTURED BINDING
# ==========================================
dev_llm = ChatOllama(
    model="qwen2.5-coder:14b",
    temperature=0.2,
    num_ctx=16384
)

reviewer_llm = ChatOllama(
    model="qwen2.5-coder:14b",
    temperature=0.1,
    num_ctx=16384
)

structured_reviewer_llm = reviewer_llm.with_structured_output(CodeReviewResult)

# ==========================================
# STATE SCHEMA
# ==========================================


class MultiAgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    revision_count: int  # Sonsuz döngü engelleme sayacı (Loop Counter)
    is_approved: bool    # Onay durumu (Approval Status)

# ==========================================
# AGENT NODES
# ==========================================


def developer_node(state: MultiAgentState) -> dict:
    """
    Developer Agent: İsteri alır veya Reviewer'dan gelen geri bildirime göre
    kodu yeniden yazar/düzeltir.
    """
    count = state.get("revision_count", 0)

    sys_prompt = SystemMessage(
        content=(
            "Sen kıdemli bir Python yazılım geliştiricisisin (Senior Python Developer).\n"
            "Görevin: Kullanıcının talebine uygun, clean code prensiplerine sahip, tip belirteçleri (type hints) "
            "ve docstring içeren eksiksiz Python kodu yazmaktır.\n"
            "Eğer konuşma geçmişinde bir 'Code Reviewer' geri bildirimi varsa, sadece o eleştirilere odaklanarak kodu revize et."
        )
    )

    messages = [sys_prompt] + state["messages"]
    response = dev_llm.invoke(messages)

    # Mesajın Developer tarafından atıldığını belirterek kaydediyoruz
    dev_message = AIMessage(
        content=f"--- [DEVELOPER KODU V{count + 1}] ---\n{response.content}", name="Developer")

    return {
        "messages": [dev_message],
        "revision_count": count + 1
    }


def reviewer_node(state: MultiAgentState) -> dict:
    """
    Reviewer Agent: Developer'ın yazdığı kodu inceler.
    Güvenlik, performans, edge-case'ler ve tip uyumluluğunu kontrol eder.
    """
    sys_prompt = SystemMessage(
        content=(
            "Sen katı bir Kod İnceleyicisisin (Lead Code Reviewer).\n"
            "Developer tarafından sunulan son Python kodunu titizlikle incele.\n"
            "Kontrol Kriterleri:\n"
            "1. Kod çalışabilir ve eksiksiz mi?\n"
            "2. Hata yönetimi (try-except) ve edge-case kontrolü var mı?\n"
            "3. Tip tanımları (Type Hints) doğru kullanılmış mı?\n\n"
            "Eğer kod mükemmel ise 'is_approved=True' ver. Herhangi bir eksiklik varsa 'is_approved=False' ver "
            "ve 'feedback' alanında düzeltilmesi gereken noktaları adım adım anlat."
        )
    )

    messages = [sys_prompt] + state["messages"]

    # Pydantic formatında yapısal çıktı alıyoruz
    review_result: CodeReviewResult = structured_reviewer_llm.invoke(messages)

    status_str = "ONAYLANDI" if review_result.is_approved else "REVİZYON İSTENDİ"
    reviewer_msg = AIMessage(
        content=f"--- [REVIEWER DEĞERLENDİRMESİ: {status_str}] ---\n{review_result.feedback}",
        name="Reviewer"
    )

    return {
        "messages": [reviewer_msg],
        "is_approved": review_result.is_approved
    }

# ==========================================
# ROUTER / EDGES LOGIC
# ==========================================


def review_decision_router(state: MultiAgentState) -> str:
    """
    Reviewer kararına ve revizyon sayısına göre akışı yönlendiren Koşullu Kenar (Conditional Edge).
    """
    if state.get("is_approved", False):
        console.print(
            Rule("[bold green]✔ KOD ONAYLANDI - SÜREÇ BAŞARIYLA TAMAMLANDI[/bold green]"))
        return END

    count = state.get("revision_count", 0)
    if count >= 3:
        console.print(
            Rule("[bold red]✘ MAKSİMUM REVİZYON SINIRINA (3) ULAŞILDI[/bold red]"))
        return END

    console.print(
        f"\n[bold yellow]🔄 Kod yetersiz görüldü. Developer'a tekrar gönderiliyor ({count}/3)...[/bold yellow]\n")
    return "developer"


# ==========================================
# GRAPH CONSTRUCTION
# ==========================================
workflow = StateGraph(MultiAgentState)

# Düğümleri tanımlıyoruz
workflow.add_node("developer", developer_node)
workflow.add_node("reviewer", reviewer_node)

# Başlangıç düğümü: İlk olarak Developer kodu yazar
workflow.set_entry_point("developer")

# Developer kod yazdıktan sonra istisnasız Reviewer'a gider
workflow.add_edge("developer", "reviewer")

# Reviewer sonrası karar mekanizması
workflow.add_conditional_edges(
    "reviewer",
    review_decision_router,
    {
        "developer": "developer",
        END: END
    }
)

app = workflow.compile()

# ==========================================
# RICH TERMINAL INTERFACE
# ==========================================
if __name__ == "__main__":
    task = "Bir metin içerisindeki e-posta adreslerini ve telefon numaralarını Regex ile ayıklayıp sözlük (dict) olarak dönen bir Python fonksiyonu yaz."

    console.clear()
    console.print(
        Rule("[bold magenta]🤖 LOCAL AGENTIC MULTI-AGENT WORKFLOW[/bold magenta]"))
    console.print(Panel(Markdown(
        f"**Görev:** {task}"), title="[bold white]Kullanıcı İsteği[/bold white]", border_style="bright_blue"))

    initial_state = {"messages": [HumanMessage(
        content=task)], "revision_count": 0, "is_approved": False}

    for output in app.stream(initial_state, stream_mode="updates"):
        for node_name, node_state in output.items():
            last_msg = node_state["messages"][-1]
            content_markdown = Markdown(last_msg.content)

            if node_name == "developer":
                rev_num = node_state.get('revision_count', 1)
                panel = Panel(
                    content_markdown,
                    title=f"[bold cyan]👨‍💻 Developer Agent (Revizyon #{rev_num})[/bold cyan]",
                    border_style="cyan",
                    padding=(1, 2)
                )
                console.print(panel)

            elif node_name == "reviewer":
                approved = node_state.get('is_approved', False)
                border_col = "green" if approved else "magenta"
                title_status = "✅ ONAY" if approved else "🔍 ELEŞTİRİ & GERİ BİLDİRİM"

                panel = Panel(
                    content_markdown,
                    title=f"[bold {border_col}]🕵️ Code Reviewer Agent — {title_status}[/bold {border_col}]",
                    border_style=border_col,
                    padding=(1, 2)
                )
                console.print(panel)
