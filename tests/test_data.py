import io

import pandas as pd
import pytest

from fraudshield.data import card_sample, load_raw, to_canonical
from fraudshield.schema import COLUMNS, Transaction

# Same header as the Sparkov files. Rows are deliberately out of time order, and two share a timestamp.
HEADER = (
    ",trans_date_trans_time,cc_num,merchant,category,amt,first,last,gender,street,city,state,zip,lat,long,"
    "city_pop,job,dob,trans_num,unix_time,merch_lat,merch_long,is_fraud"
)
ROWS = [
    "0,2019-01-01 00:05:00,111,fraud_A,grocery_pos,10.5,Ann,Lee,F,1 Main St,X,NY,10001,40.7,-74.0,"
    "8000000,Nurse,1990-06-15,ccc,1325376300,40.8,-74.1,0",
    "1,2019-01-01 00:00:00,222,fraud_B,shopping_net,999.0,Bob,Ray,M,2 Elm St,Y,CA,90001,34.0,-118.2,"
    "4000000,Chef,1960-01-01,bbb,1325376000,35.0,-117.0,1",
    "2,2019-01-01 00:00:00,111,fraud_C,gas_transport,40.0,Ann,Lee,F,1 Main St,X,NY,10001,40.7,-74.0,"
    "8000000,Nurse,1990-06-15,aaa,1325376000,40.6,-73.9,0",
]


def raw(rows=ROWS) -> pd.DataFrame:
    return pd.read_csv(io.StringIO("\n".join([HEADER, *rows])))


def test_canonical_columns_and_no_personal_data():
    df = to_canonical(raw())
    assert list(df.columns) == COLUMNS
    assert not {"first", "last", "street", "unix_time"} & set(df.columns)


def test_sorted_by_time_then_tx_id():
    df = to_canonical(raw())
    assert list(df["tx_id"]) == ["aaa", "bbb", "ccc"]  # aaa and bbb tie on time; tx_id breaks the tie


def test_age_at_transaction():
    df = to_canonical(raw()).set_index("tx_id")
    assert df.loc["aaa", "age"] == 28  # born 1990-06-15, transaction 2019-01-01
    assert df.loc["bbb", "age"] == 59  # born 1960-01-01, transaction 2019-01-01 (birthday on the day)


def test_rows_validate_against_pydantic_model():
    for rec in to_canonical(raw()).to_dict("records"):
        Transaction.model_validate(rec)


def test_load_raw_concatenates_and_rejects_duplicates(tmp_path):
    raw().iloc[:2].to_csv(tmp_path / "fraudTrain.csv", index=False)
    raw().iloc[2:].to_csv(tmp_path / "fraudTest.csv", index=False)
    assert len(load_raw(tmp_path)) == 3

    raw().to_csv(tmp_path / "fraudTest.csv", index=False)  # overlaps with fraudTrain
    with pytest.raises(ValueError, match="duplicate"):
        load_raw(tmp_path)


def test_card_sample_keeps_whole_cards():
    df = pd.DataFrame({"card_id": [1, 1, 1, 2, 2, 3, 4, 5, 6, 7], "x": range(10)})
    sample = card_sample(df, 0.3, seed=0)
    kept = set(sample["card_id"])
    assert len(kept) == 2
    assert len(sample) == df["card_id"].isin(kept).sum()  # every row of a sampled card is kept
    assert sample.equals(card_sample(df, 0.3, seed=0))  # deterministic
