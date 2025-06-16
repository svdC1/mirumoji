from typing import List, Dict, Optional
from dotenv import load_dotenv
import logging
import os

logger = logging.getLogger(__name__)


def check_env(expected: List,
              input: Dict,
              dotenv_path: Optional[str] = None
              ) -> Dict:
    """
    Check if environment variables are available
    and return dictionary with expected variables
    """
    # Load from dotenv
    load_dotenv(dotenv_path=dotenv_path)
    # Get available vars from env
    API_KEYS = {k: v for k, v in os.environ.items() if k in expected}
    logger.info(f"Retrieved {','.join(API_KEYS.keys())} from ENV")
    missing = [k for k in expected if k not in API_KEYS.keys()]
    # Get missing from input
    if missing:
        logger.info(f"{','.join(missing)} not found in ENV")
        for m in missing:
            if m not in input.keys() or not input[m]:
                raise ValueError(f"Could not find variable: {m}")
            API_KEYS[m] = input[m]
    return API_KEYS


def using_modal() -> bool:
    load_dotenv()
    keys = ["MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET"]
    if keys[0] in os.environ and keys[1] in os.environ:
        return True
    return False
