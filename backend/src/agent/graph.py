import os

from agent.tools_and_schemas import SearchQueryList, Reflection
from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from langgraph.types import Send
from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langchain_core.runnables import RunnableConfig
from tavily import TavilyClient

from agent.state import (
    OverallState,
    QueryGenerationState,
    ReflectionState,
    WebSearchState,
)
from agent.configuration import Configuration, ModelReference
from agent.prompts import (
    get_current_date,
    query_writer_instructions,
    web_searcher_instructions,
    reflection_instructions,
    answer_instructions,
)
from agent.models import get_model_factory
from agent.utils import (
    get_citations,
    get_research_topic,
    insert_citation_markers,
    resolve_urls,
)

load_dotenv()

# Initialize model factory
model_factory = get_model_factory()

# Initialize Tavily Search API client
def get_tavily_client():
    """Get Tavily client for web search API."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY is not set. Please set the environment variable.")
    return TavilyClient(api_key=api_key)


# Nodes
def generate_query(state: OverallState, config: RunnableConfig) -> QueryGenerationState:
    """LangGraph node that generates search queries based on the User's question.

    Uses the configured language model to create optimized search queries for web research based on
    the User's question.

    Args:
        state: Current graph state containing the User's question
        config: Configuration for the runnable, including LLM provider settings

    Returns:
        Dictionary with state update, including search_query key containing the generated queries
    """
    configurable = Configuration.from_runnable_config(config)

    # check for custom initial search query count
    if state.get("initial_search_query_count") is None:
        state["initial_search_query_count"] = configurable.number_of_initial_queries

    # Get model reference and create model
    model_ref = configurable.get_query_generator_ref()
    provider = model_factory.get_provider(model_ref.provider)

    # Create model with structured output
    if provider.supports_structured_output(model_ref.model):
        structured_llm = provider.create_model_with_structured_output(
            model_ref.model,
            SearchQueryList,
            temperature=1.0
        )
    else:
        # Fallback for models that don't support structured output
        llm = provider.get_model(model_ref.model, temperature=1.0)
        # We'll handle the structured output manually in this case
        structured_llm = llm

    # Format the prompt
    current_date = get_current_date()
    formatted_prompt = query_writer_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        number_queries=state["initial_search_query_count"],
    )

    # Generate the search queries
    result = structured_llm.invoke(formatted_prompt)

    # Handle non-structured output case
    if not hasattr(result, 'query'):
        # Parse the result manually (this is a fallback)
        # In practice, you might want to use a more sophisticated parsing method
        import re
        queries = re.findall(r'"([^"]+)"', str(result))
        if not queries:
            queries = [str(result)]  # Fallback to using the entire result as one query

        # Create a SearchQueryList-like object
        class FallbackSearchQueryList:
            def __init__(self, queries):
                self.query = queries

        result = FallbackSearchQueryList(queries)

    return {"search_query": result.query}


def continue_to_web_research(state: QueryGenerationState):
    """LangGraph node that sends the search queries to the web research node.

    This is used to spawn n number of web research nodes, one for each search query.
    """
    return [
        Send("web_research", {"search_query": search_query, "id": int(idx)})
        for idx, search_query in enumerate(state["search_query"])
    ]


def web_research(state: WebSearchState, config: RunnableConfig) -> OverallState:
    """LangGraph node that performs web research using search tools.

    Executes web research using the Tavily Search API for all providers.

    Args:
        state: Current graph state containing the search query and research loop count
        config: Configuration for the runnable, including search API settings

    Returns:
        Dictionary with state update, including sources_gathered, research_loop_count, and web_research_results
    """
    # Configure
    configurable = Configuration.from_runnable_config(config)
    formatted_prompt = web_searcher_instructions.format(
        current_date=get_current_date(),
        research_topic=state["search_query"],
    )

    # Use Tavily Search API for all providers
    try:
        tavily_client = get_tavily_client()

        # Perform the search using Tavily
        search_result = tavily_client.search(
            query=state["search_query"],
            max_results=5,
            search_depth="basic",
            include_answer=True
        )

        # Extract search results and format them
        if search_result and 'results' in search_result:
            # Format the search results into a readable text
            search_text_parts = []
            sources_gathered = []

            # Add the answer if available
            if 'answer' in search_result and search_result['answer']:
                search_text_parts.append(f"Answer: {search_result['answer']}\n")

            # Add individual search results
            for i, result in enumerate(search_result['results'][:5], 1):
                title = result.get('title', 'No title')
                content = result.get('content', 'No content available')
                url = result.get('url', '#')

                search_text_parts.append(f"Source {i}: {title}\n{content}\nURL: {url}\n")

                # Add to sources gathered
                sources_gathered.append({
                    "short_url": f"[{i}]",
                    "value": url,
                    "title": title
                })

            modified_text = "\n".join(search_text_parts)
        else:
            modified_text = f"No search results found for '{state['search_query']}'."
            sources_gathered = []

    except Exception as e:
        # Handle search errors gracefully
        modified_text = f"Error performing web search for '{state['search_query']}': {str(e)}"
        sources_gathered = []

    return {
        "sources_gathered": sources_gathered,
        "search_query": [state["search_query"]],
        "web_research_result": [modified_text],
    }


def reflection(state: OverallState, config: RunnableConfig) -> ReflectionState:
    """LangGraph node that identifies knowledge gaps and generates potential follow-up queries.

    Analyzes the current summary to identify areas for further research and generates
    potential follow-up queries. Uses structured output to extract
    the follow-up query in JSON format.

    Args:
        state: Current graph state containing the running summary and research topic
        config: Configuration for the runnable, including LLM provider settings

    Returns:
        Dictionary with state update, including search_query key containing the generated follow-up query
    """
    configurable = Configuration.from_runnable_config(config)
    # Increment the research loop count and get the reasoning model
    state["research_loop_count"] = state.get("research_loop_count", 0) + 1
    reasoning_model = state.get("reasoning_model", configurable.reflection_model)

    # Get model reference and create model
    model_ref = ModelReference.from_string(reasoning_model)
    provider = model_factory.get_provider(model_ref.provider)

    # Format the prompt
    current_date = get_current_date()
    formatted_prompt = reflection_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        summaries="\n\n---\n\n".join(state["web_research_result"]),
    )

    # Create model with structured output
    if provider.supports_structured_output(model_ref.model):
        structured_llm = provider.create_model_with_structured_output(
            model_ref.model,
            Reflection,
            temperature=1.0
        )
        result = structured_llm.invoke(formatted_prompt)
    else:
        # Fallback for models that don't support structured output
        llm = provider.get_model(model_ref.model, temperature=1.0)
        raw_result = llm.invoke(formatted_prompt)

        # Parse the result manually (simplified fallback)
        # In practice, you might want to use a more sophisticated parsing method
        import json
        try:
            # Try to parse JSON from the response
            result_text = str(raw_result.content)
            # Extract JSON if present
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = result_text[json_start:json_end]
                parsed = json.loads(json_str)

                # Create a Reflection-like object
                class FallbackReflection:
                    def __init__(self, data):
                        self.is_sufficient = data.get('is_sufficient', False)
                        self.knowledge_gap = data.get('knowledge_gap', '')
                        self.follow_up_queries = data.get('follow_up_queries', [])

                result = FallbackReflection(parsed)
            else:
                # If no JSON found, create default response
                class FallbackReflection:
                    def __init__(self):
                        self.is_sufficient = True
                        self.knowledge_gap = ''
                        self.follow_up_queries = []

                result = FallbackReflection()
        except Exception:
            # If parsing fails, create default response
            class FallbackReflection:
                def __init__(self):
                    self.is_sufficient = True
                    self.knowledge_gap = ''
                    self.follow_up_queries = []

            result = FallbackReflection()

    return {
        "is_sufficient": result.is_sufficient,
        "knowledge_gap": result.knowledge_gap,
        "follow_up_queries": result.follow_up_queries,
        "research_loop_count": state["research_loop_count"],
        "number_of_ran_queries": len(state["search_query"]),
    }


def evaluate_research(
    state: ReflectionState,
    config: RunnableConfig,
) -> OverallState:
    """LangGraph routing function that determines the next step in the research flow.

    Controls the research loop by deciding whether to continue gathering information
    or to finalize the summary based on the configured maximum number of research loops.

    Args:
        state: Current graph state containing the research loop count
        config: Configuration for the runnable, including max_research_loops setting

    Returns:
        String literal indicating the next node to visit ("web_research" or "finalize_summary")
    """
    configurable = Configuration.from_runnable_config(config)
    max_research_loops = (
        state.get("max_research_loops")
        if state.get("max_research_loops") is not None
        else configurable.max_research_loops
    )
    if state["is_sufficient"] or state["research_loop_count"] >= max_research_loops:
        return "finalize_answer"
    else:
        return [
            Send(
                "web_research",
                {
                    "search_query": follow_up_query,
                    "id": state["number_of_ran_queries"] + int(idx),
                },
            )
            for idx, follow_up_query in enumerate(state["follow_up_queries"])
        ]


def finalize_answer(state: OverallState, config: RunnableConfig):
    """LangGraph node that finalizes the research summary.

    Prepares the final output by deduplicating and formatting sources, then
    combining them with the running summary to create a well-structured
    research report with proper citations.

    Args:
        state: Current graph state containing the running summary and sources gathered

    Returns:
        Dictionary with state update, including running_summary key containing the formatted final summary with sources
    """
    configurable = Configuration.from_runnable_config(config)
    reasoning_model = state.get("reasoning_model") or configurable.answer_model

    # Get model reference and create model
    model_ref = ModelReference.from_string(reasoning_model)
    provider = model_factory.get_provider(model_ref.provider)

    # Format the prompt
    current_date = get_current_date()
    formatted_prompt = answer_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        summaries="\n---\n\n".join(state["web_research_result"]),
    )

    # Create model (temperature=0 for final answers)
    llm = provider.get_model(model_ref.model, temperature=0)
    result = llm.invoke(formatted_prompt)

    # Replace the short urls with the original urls and add all used urls to the sources_gathered
    unique_sources = []
    for source in state["sources_gathered"]:
        if source["short_url"] in result.content:
            result.content = result.content.replace(
                source["short_url"], source["value"]
            )
            unique_sources.append(source)

    return {
        "messages": [AIMessage(content=result.content)],
        "sources_gathered": unique_sources,
    }


# Create our Agent Graph
builder = StateGraph(OverallState, config_schema=Configuration)

# Define the nodes we will cycle between
builder.add_node("generate_query", generate_query)
builder.add_node("web_research", web_research)
builder.add_node("reflection", reflection)
builder.add_node("finalize_answer", finalize_answer)

# Set the entrypoint as `generate_query`
# This means that this node is the first one called
builder.add_edge(START, "generate_query")
# Add conditional edge to continue with search queries in a parallel branch
builder.add_conditional_edges(
    "generate_query", continue_to_web_research, ["web_research"]
)
# Reflect on the web research
builder.add_edge("web_research", "reflection")
# Evaluate the research
builder.add_conditional_edges(
    "reflection", evaluate_research, ["web_research", "finalize_answer"]
)
# Finalize the answer
builder.add_edge("finalize_answer", END)

graph = builder.compile(name="pro-search-agent")
