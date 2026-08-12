import asyncio
from pprint import pprint

from app.agent.classifier import classify_disruption
from app.agent.graph import claim_graph


async def main():

    message = (
        "Heavy rain stopped me from delivering today. I could not complete my shift."
    )

    print("\n==============================")
    print("GIGSHIELD FULL FLOW TEST")
    print("==============================")

    # 1. Local Qwen classification
    print("\n[1] CLASSIFYING MESSAGE...")
    disruption_type = await classify_disruption(message)

    print(f"Message: {message}")
    print(f"Disruption type: {disruption_type}")

    # 2. Initial claim state
    state = {
        "whatsapp_id": "test_user_001",
        "worker_id": 1,
        "policy_id": 1,
        "raw_message": message,
        "platform": "blinkit",
        "partner_id": "BLK001",
        "disruption_type": disruption_type,
        "claimed_window_start": None,
        "claimed_window_end": None,
        "shift_verified": None,
        "weather_data": None,
        "gov_feed_data": None,
        "policy_rule": None,
        "fraud_history": None,
        "anomaly_score": None,
        "effective_hours": None,
        "phr": None,
        "slf": None,
        "final_payout": None,
        "decision": None,
        "decision_reason": None,
        "smart_receipt": None,
        "tool_errors": [],
        "steps_completed": [],
    }

    # 3. Run LangGraph
    print("\n[2] RUNNING CLAIM GRAPH...")

    result = await claim_graph.ainvoke(state)

    # 4. Display result
    print("\n==============================")
    print("FINAL RESULT")
    print("==============================")

    print(f"Disruption:     {result.get('disruption_type')}")
    print(f"Shift verified: {result.get('shift_verified')}")
    print(f"Weather:        {result.get('weather_data')}")
    print(f"Policy rule:    {result.get('policy_rule')}")
    print(f"Decision:       {result.get('decision')}")
    print(f"Reason:         {result.get('decision_reason')}")
    print(f"PHR:            {result.get('phr')}")
    print(f"Effective hrs:  {result.get('effective_hours')}")
    print(f"SLF:            {result.get('slf')}")
    print(f"Final payout:   ₹{result.get('final_payout')}")

    print("\nSteps completed:")
    for step in result.get("steps_completed", []):
        print(f"  ✓ {step}")

    if result.get("tool_errors"):
        print("\nErrors:")
        for error in result["tool_errors"]:
            print(f"  ✗ {error}")

    print("\n==============================")

    print("\nFULL STATE:")
    pprint(result)


if __name__ == "__main__":
    asyncio.run(main())
