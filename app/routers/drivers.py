from fastapi import APIRouter

from app.mock_data import DRIVERS

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.get("")
def list_drivers():
    """Return the full driver grid."""
    return DRIVERS
