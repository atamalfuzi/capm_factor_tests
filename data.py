"""Get the Kenneth French Data Library files and read their monthly sections."""
import re
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
RAW, REFERENCE = ROOT / "data", ROOT / "reference_2021"
OUTPUT, FIGURES = ROOT / "output", ROOT / "figures"
BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"

FACTOR_FILES = {"three": "F-F_Research_Data_Factors_CSV.zip", "five": "F-F_Research_Data_5_Factors_2x3_CSV.zip"}
PORTFOLIO_FILES = {"Size and book-to-market": "25_Portfolios_5x5_CSV.zip", "Size and profitability": "25_Portfolios_ME_OP_5x5_CSV.zip",
                   "Size and investment": "25_Portfolios_ME_INV_5x5_CSV.zip", "30 industries": "30_Industry_Portfolios_CSV.zip"}
MAIN = "Size and book-to-market"
VALUE_WEIGHTED = "Average Value Weighted Returns -- Monthly"
MODELS = {"CAPM": ["Mkt-RF"], "Three-factor": ["Mkt-RF", "SMB", "HML"], "Five-factor": ["Mkt-RF", "SMB", "HML", "RMW", "CMA"]}


def download():
    RAW.mkdir(exist_ok=True)
    for name in [*FACTOR_FILES.values(), *PORTFOLIO_FILES.values()]:
        request = urllib.request.Request(BASE + name, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=300) as r:
            (RAW / name).write_bytes(r.read())


def read_monthly(path, title=None):
    """The rows dated YYYYMM of one section, from its title (or the top of the file) to the first other line. Per cent."""
    with zipfile.ZipFile(path) as z:
        lines = z.read(z.namelist()[0]).decode("latin-1").splitlines()
    start = 0 if title is None else next(i for i, line in enumerate(lines) if title in line)
    head = next(i for i in range(start, len(lines)) if lines[i].startswith(","))
    rows = {}
    for line in lines[head + 1:]:
        fields = [f.strip() for f in line.split(",")]
        if not re.fullmatch(r"\d{6}", fields[0]):
            break
        rows[fields[0]] = [float(f) for f in fields[1:]]
    if not rows:
        raise ValueError(f"no monthly rows under {title or 'the top of the file'} in {path}")
    table = pd.DataFrame.from_dict(rows, orient="index", columns=[c.strip() for c in lines[head].split(",")[1:]])
    table.index = pd.PeriodIndex(table.index, freq="M")
    return table.replace([-99.99, -999.0], np.nan)


def factors(model):
    """A model's factors and the T-bill rate. The five-factor file has its own SMB, so that model reads from it."""
    table = read_monthly(RAW / FACTOR_FILES["five" if model == "Five-factor" else "three"])
    return table[MODELS[model]], table.RF


def portfolios(name=MAIN):
    """Value-weighted monthly returns, in per cent and before taking out the T-bill rate."""
    return read_monthly(RAW / PORTFOLIO_FILES[name], VALUE_WEIGHTED)


def read_reference():
    """The 2021 copies of the portfolio and factor files, as the 2021 run read them."""
    returns = pd.read_csv(REFERENCE / "Average_Value_Weighted.csv", index_col=0)
    table = pd.read_csv(REFERENCE / "Fama_French_Factors_cleaned.csv", index_col=0)
    for d in (returns, table):
        d.index = pd.PeriodIndex(d.index.astype(str), freq="M")
    return returns, table


if __name__ == "__main__":
    download()
    print(portfolios().index[[0, -1]], read_monthly(RAW / FACTOR_FILES["five"]).index[[0, -1]])
