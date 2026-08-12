import asyncio
from app.rag.policy_qa import answer_policy_question


async def main():
    answer = await answer_policy_question(
        "What are the conditions for heavy rain coverage?"
    )

    print("\nAnswer:\n")
    print(answer)


asyncio.run(main())