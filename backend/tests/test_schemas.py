from __future__ import annotations

import pytest

from bookandride_api.schemas import PartnerRental


def test_partner_rental_rejects_non_iso_timestamp() -> None:
    with pytest.raises(ValueError):
        PartnerRental(
            id=1,
            user_id=2,
            bike_id="bike-9",
            start_time="2024-05-02 08:30",  # missing Z / offset
            price_eur=1.0,
        )
