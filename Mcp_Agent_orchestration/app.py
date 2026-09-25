import asyncio

from langchain_core.messages import HumanMessage, SystemMessage

from graph import build_graph
from logging_config import configure_logging

logger = configure_logging()


async def main():
    graph = await build_graph()
    logger.info("Agent application started")

    print("VCTI AI Assistant is ready.")
    print("Type 'exit' to stop.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            logger.info("Agent application stopped by user")
            print("Goodbye!")
            break

        if not user_input:
            continue

        try:
            logger.info("User request: %s", user_input)
            result = await graph.ainvoke(
                {
                    "messages": [
                        SystemMessage(
                            content=(
                                "You are a helpful AI assistant. "
                                "Use available tools only when they are needed. "
                                "For directory requests, use the list_files tool. "
                                "For current weather requests, use the get_weather tool. "
                                "For every public factual question that is not a greeting or an internal-document question, "
                                "use the web_search tool before answering. This includes questions about people, organizations, events, products, facts, and public information. "
                                "Prefer official, primary, government, university, or well-established reference sources. "
                                "For webpage reading or summarization requests with a URL, use the scrape_url tool. "
                                "For questions about internal documents, policies, or the knowledge base, use rag_search. "
                                "Use standard Markdown only when useful. Do not escape standard Markdown characters such as **, [], (), or | unless they must be displayed literally. Do not use HTML tags. "
                                "Never claim that you used a tool when you did not. Never invent a source URL."
                            )
                        ),
                        HumanMessage(content=user_input),
                    ]
                }
            )

            print(f"\nAssistant: {result['messages'][-1].content}\n")
            logger.info("Agent response completed successfully")

        except Exception as error:
            logger.exception("Agent request failed: %s", error)
            print(f"\nAssistant: I could not complete that request: {error}\n")


if __name__ == "__main__":
    asyncio.run(main())
