import random
import string
from datetime import datetime


def generate_experiment_id() -> str:
    """Generate a unique experiment ID in the format: exp_{YYYYMMDD}_{6-char random}.

    Returns:
        A string like 'exp_20250301_a3f9c2'.
    """
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"exp_{date_str}_{random_str}"
