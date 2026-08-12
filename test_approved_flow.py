import asyncio
from app.agent.classifier import classify_disruption
from app.agent.graph import (
    node_verify_shift,
    node_query_policy,
    node_make_decision,
    node_flag_review,
    node_calculate_payout,
)


async def main():

    message = "Heavy rain stopped me from delivering today."

    print("\n==============================")
    print("GIGSHIELD APPROVED FLOW TEST")
    print("==============================")

    # 1. Local Qwen classification
    disruption_type = await classify_disruption(message)

    print(f"\nClassification: {disruption_type}")

    # 2. Initial state
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
        "effective_hours": 3.0,
        "phr": None,
        "slf": None,
        "final_payout": None,
        "decision": None,
        "decision_reason": None,
        "smart_receipt": None,
        "tool_errors": [],
        "steps_completed": [],
    }

    # 3. Verify actual mock shift
    state = await node_verify_shift(state)

    print(f"Shift verified: {state['shift_verified']}")

    # 4. Simulate qualifying heavy rain
    state["weather_data"] = {
        "rainfall_mm": 84.0,
        "temp_c": 25.4,
        "wind_kmh": 12.7,
        "weather_code": 65,
        "aqi": 23,
        "pm2_5": 10.4,
        "zone": "Gurgaon Sector 14",
    }

    print(f"Simulated rainfall: {state['weather_data']['rainfall_mm']} mm")

    # 5. Use the existing policy tool
    state = await node_query_policy(state)

    # 6. Make the actual decision
    state = await node_make_decision(state)

    print(f"Decision: {state['decision']}")
    print(f"Reason: {state['decision_reason']}")

    # 7. Run review node
    state = await node_flag_review(state)

    # 8. Calculate payout if approved
    if state["decision"] == "approved":
        state = await node_calculate_payout(state)

    print("\n==============================")
    print("FINAL RESULT")
    print("==============================")

    print(f"Decision:       {state['decision']}")
    print(f"Reason:         {state['decision_reason']}")
    print(f"Effective hrs:  {state['effective_hours']}")
    print(f"PHR:            {state['phr']}")
    print(f"SLF:            {state['slf']}")
    print(f"Final payout:   ₹{state['final_payout']}")

    print("\nSteps:")
    for step in state["steps_completed"]:
        print(f"  ✓ {step}")

    print("\n==============================")


if __name__ == "__main__":
    asyncio.run(main())
