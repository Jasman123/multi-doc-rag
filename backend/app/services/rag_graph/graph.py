from functools import partial

from langgraph.graph import END, START, StateGraph

from app.services.rag_graph.nodes import RAGNodes
from app.services.rag_graph.state import RAGState


def _route_after_precheck(state: RAGState) -> str:
    return "empty" if state.get("corpus_empty") else "analyze"


def _route_after_retrieve(state: RAGState) -> str:
    return "empty" if not state.get("candidates") else "grade"


def _route_after_grade(state: RAGState, max_retries: int) -> str:
    if state.get("grade") == "insufficient" and state.get("attempt", 0) < max_retries:
        return "rewrite"
    return "generate"


def build_rag_graph(nodes: RAGNodes, max_retries: int):
    graph = StateGraph(RAGState)

    graph.add_node("precheck", nodes.precheck)
    graph.add_node("analyze_query", nodes.analyze_query)
    graph.add_node("retrieve", nodes.retrieve)
    # Named "grade_documents", not "grade" — LangGraph forbids a node name
    # that collides with a state key, and RAGState already has a "grade" field.
    graph.add_node("grade_documents", nodes.grade)
    graph.add_node("rewrite_query", nodes.rewrite_query)
    graph.add_node("generate", nodes.generate)
    graph.add_node("no_results", nodes.no_results)

    graph.add_edge(START, "precheck")
    graph.add_conditional_edges(
        "precheck", _route_after_precheck, {"empty": "no_results", "analyze": "analyze_query"}
    )
    graph.add_edge("analyze_query", "retrieve")
    graph.add_conditional_edges(
        "retrieve", _route_after_retrieve, {"empty": "no_results", "grade": "grade_documents"}
    )
    graph.add_conditional_edges(
        "grade_documents",
        partial(_route_after_grade, max_retries=max_retries),
        {"rewrite": "rewrite_query", "generate": "generate"},
    )
    graph.add_edge("rewrite_query", "retrieve")
    graph.add_edge("generate", END)
    graph.add_edge("no_results", END)

    return graph.compile()
