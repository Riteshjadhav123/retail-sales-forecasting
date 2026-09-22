"""RetailMind-X API Dependencies."""
from typing import Generator
import pandas as pd
from fastapi import HTTPException
from app.data.session_manager import SESSION

def get_current_session():
    """Yields or returns active DatasetSession singleton."""
    return SESSION

def get_active_dataframe() -> pd.DataFrame:
    """Returns clean dataframe if available, else raw dataframe, else raises 400."""
    if SESSION.clean_df is not None:
        return SESSION.clean_df
    if SESSION.raw_df is not None:
        return SESSION.raw_df
    raise HTTPException(status_code=400, detail="No active dataset session or dataset uploaded yet. Please upload a dataset first.")
