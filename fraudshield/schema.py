"""Canonical transaction schema, shared by the offline pipeline, the stream and the scoring API."""

from datetime import datetime

from pydantic import BaseModel, Field


class Transaction(BaseModel):
    tx_id: str = Field(
        description="Unique transaction id (Sparkov trans_num); idempotency key and tie-breaker"
    )
    event_time: datetime = Field(description="When the transaction happened (Sparkov trans_date_trans_time)")
    card_id: int = Field(description="Card number; the entity key for behavioural features")
    merchant_id: str
    category: str
    amount: float = Field(ge=0)
    lat: float = Field(description="Cardholder home latitude")
    lon: float
    merch_lat: float
    merch_lon: float
    city_pop: int
    gender: str
    job: str
    state: str
    zip: int
    dob: datetime
    age: int = Field(description="Whole years at event_time")
    is_fraud: int = Field(ge=0, le=1)


COLUMNS = list(Transaction.model_fields)

# Sparkov CSV column -> canonical column. Columns not listed here are dropped: names and street are personal
# data with no legitimate signal; unix_time is offset from trans_date_trans_time in this dataset, so we use
# trans_date_trans_time only; city is redundant with lat/lon + city_pop.
SPARKOV_COLUMNS = {
    "trans_num": "tx_id",
    "trans_date_trans_time": "event_time",
    "cc_num": "card_id",
    "merchant": "merchant_id",
    "category": "category",
    "amt": "amount",
    "lat": "lat",
    "long": "lon",
    "merch_lat": "merch_lat",
    "merch_long": "merch_lon",
    "city_pop": "city_pop",
    "gender": "gender",
    "job": "job",
    "state": "state",
    "zip": "zip",
    "dob": "dob",
    "is_fraud": "is_fraud",
}
