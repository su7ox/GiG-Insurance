import logging
from app.agent.state import ClaimState
from app.integrations.platform_api.mock_client import get_shift_data
logger = logging.getLogger(__name__)
async def verify_active_shift(state: ClaimState, partner_id: str, platform: str) -> ClaimState:
    try:
        shift = get_shift_data(platform, partner_id)
        if not shift:
            logger.warning(f"No shift data found for {partner_id} on {platform}")
            state["shift_verified"] = False
            state["steps_completed"].append("verify_shift:no_data")
            return state
        state["shift_verified"] = shift.get("logged_in", False)
        state["steps_completed"].append("verify_shift:verified")
        logger.info(f"Shift verified for {partner_id}: {state['shift_verified']}")
    except Exception as e:
        logger.error(f"Shift verification error: {e}")
        state["shift_verified"] = False
        state["tool_errors"].append(f"verify_shift: {str(e)}")
    return state