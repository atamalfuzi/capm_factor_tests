"""Reading the French files. No downloads."""
import zipfile

import numpy as np
import pytest

import data

FILE = """This file was created using the 202609 CRSP database.

  Average Value Weighted Returns -- Monthly
,A,B
192607,   1.50,  -2.00
192608, -99.99,   3.00
192609,    4.00,-999

  Average Equal Weighted Returns -- Monthly
,A,B
192607,   9.00,   9.00

  Average Value Weighted Returns -- Annual
,A,B
1927,   7.00,   7.00
"""


def csv_zip(tmp_path, text=FILE):
    path = tmp_path / "file.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("file.csv", text)
    return path


def test_reads_only_the_named_section_and_marks_missing_values(tmp_path):
    t = data.read_monthly(csv_zip(tmp_path), data.VALUE_WEIGHTED)
    assert [str(m) for m in t.index] == ["1926-07", "1926-08", "1926-09"]
    assert list(t.columns) == ["A", "B"]
    assert t.A.iloc[0] == 1.5 and np.isnan(t.A.iloc[1]) and np.isnan(t.B.iloc[2])


def test_reads_from_the_top_when_no_title_is_given_and_stops_at_the_annual_rows(tmp_path):
    text = "Notes.\n\n,Mkt-RF,RF\n192607,2.89,0.22\n\n Annual Factors: January-December\n,Mkt-RF,RF\n1927,29.47,3.12\n"
    t = data.read_monthly(csv_zip(tmp_path, text))
    assert len(t) == 1 and t["Mkt-RF"].iloc[0] == 2.89


def test_stops_if_a_section_is_empty(tmp_path):
    with pytest.raises(ValueError):
        data.read_monthly(csv_zip(tmp_path, "Notes\n,A\nnot a month,1\n"))


def test_stops_if_the_title_is_absent(tmp_path):
    with pytest.raises(StopIteration):
        data.read_monthly(csv_zip(tmp_path), "No such section")


def test_reference_files_share_their_months():
    r, table = data.read_reference()
    assert r.index.equals(table.index) and r.shape[1] == 25


def test_each_model_extends_the_one_before():
    capm, three, five = data.MODELS.values()
    assert three[: len(capm)] == capm and five[: len(three)] == three
