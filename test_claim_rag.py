import asyncio

from app.agent.tools.query_policy_rag import query_policy_rag


async def main():

    state = {
        "disruption_type": "heavy_rain",
        "policy_rule": None,
        "steps_completed": [],
        "tool_errors": [],
    }

    state = await query_policy_rag(state)

    print("\n==============================")
    print("CLAIM RAG TEST")
    print("==============================")

    print("\nRule:")
    print(state["policy_rule"])

    print("\nRetrieved policy chunks:")

    for i, chunk in enumerate(
        state["policy_rule"].get("rag_chunks", []),
        1
    ):
        print(f"\n--- Chunk {i} ---")
        print(chunk)

    print("\nSteps:")
    print(state["steps_completed"])

    print("\nErrors:")
    print(state["tool_errors"])


if __name__ == "__main__":
    asyncio.run(main())