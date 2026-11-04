"""Test the CAPM, three- and five-factor models and write every table the README quotes to output/."""
import numpy as np
import pandas as pd
from scipy import stats

from data import FACTOR_FILES, MAIN, MODELS, OUTPUT, PORTFOLIO_FILES, RAW, factors, portfolios, read_monthly, read_reference

COMMON_START = "1963-07"  # the first month of the five-factor file
REFERENCE_END = "2020-09"
PERIODS = {"1926-07 to 1963-06": ("1926-07", "1963-06"), "1963-07 to 1990-12": ("1963-07", "1990-12"),
           "1991-01 to 2008-12": ("1991-01", "2008-12"), "2009-01 to latest": ("2009-01", None),
           "2020-10 to latest": ("2020-10", None)}
BLOCK = 12  # months, for the resampled ranges
DRAWS = 2000


def with_constant(x):
    return np.column_stack([np.ones(len(x)), x])


def time_series(r, f):
    """OLS of each asset on the factors. Returns alphas, loadings (assets by factors) and residuals."""
    coef = np.linalg.lstsq(with_constant(f), r, rcond=None)[0]
    return coef[0], coef[1:].T, r - with_constant(f) @ coef


def grs(r, f):
    """Gibbons, Ross and Shanken (1989): F test that all the alphas are zero, exact under normal errors."""
    r, f = np.asarray(r, float), np.asarray(f, float).reshape(len(r), -1)
    if r.ndim == 1:
        r = r[:, None]
    T, N, L = len(r), r.shape[1], f.shape[1]
    if T <= N + L:
        raise ValueError(f"{T} months are too few for {N} assets and {L} factors")
    alpha, _, e = time_series(r, f)
    sigma = e.T @ e / T
    mean = f.mean(axis=0)
    omega = np.cov(f, rowvar=False, ddof=0).reshape(L, L)
    a2 = alpha @ np.linalg.solve(sigma, alpha)
    F = (T - N - L) / N * a2 / (1 + mean @ np.linalg.solve(omega, mean))
    return {"F": F, "p": stats.f.sf(F, N, T - N - L), "sharpe_alpha": np.sqrt(a2)}


def grs_resampled_p(r, f, draws=DRAWS):
    """The GRS p-value without assuming normal errors: alphas are taken out, months resampled, and the F compared with its original."""
    r, f = np.asarray(r, float), np.asarray(f, float).reshape(len(r), -1)
    null = r - time_series(r, f)[0]
    F = grs(r, f)["F"]
    return (1 + sum(grs(null[p], f[p])["F"] >= F for p in resampled(len(r), draws=draws))) / (draws + 1)


def cross_section_fit(means, b):
    """OLS of mean returns on betas with an intercept: the coefficients and R²."""
    X = with_constant(b)
    coef = np.linalg.lstsq(X, means, rcond=None)[0]
    e = means - X @ coef
    return coef, 1 - e @ e / ((means - means.mean()) ** 2).sum()


def fama_macbeth(r, f):
    """Monthly cross-sections on full-sample betas, with Fama-MacBeth and Shanken (1992) standard errors."""
    r, f = np.asarray(r, float), np.asarray(f, float).reshape(len(r), -1)
    T, N = r.shape
    alpha, b, e = time_series(r, f)
    X = with_constant(b)
    XtX_inv_Xt = np.linalg.solve(X.T @ X, X.T)
    path = (XtX_inv_Xt @ r.T).T
    lam = path.mean(axis=0)
    premia = lam[1:]
    cov_f = np.cov(f, rowvar=False).reshape(b.shape[1], b.shape[1])
    c = premia @ np.linalg.solve(cov_f, premia)
    border = np.zeros((len(lam), len(lam)))
    border[1:, 1:] = cov_f
    shanken = ((1 + c) * XtX_inv_Xt @ (e.T @ e / T) @ XtX_inv_Xt.T + border) / T
    means = r.mean(axis=0)
    r2 = cross_section_fit(means, b)[1]
    K = b.shape[1]
    return {"lambda": lam, "se_fm": path.std(axis=0, ddof=1) / np.sqrt(T), "se_shanken": np.sqrt(np.diag(shanken)), "r2": r2,
            "adj_r2": 1 - (1 - r2) * (N - 1) / (N - K - 1), "r2_constrained": 1 - alpha @ alpha / ((means - means.mean()) ** 2).sum(),
            "alpha": alpha, "beta": b}


def hj_distance(gross, f):
    """Hansen-Jagannathan (1997) distance of the linear SDF m = b0 + b'f from pricing the gross returns at 1. f may have no columns."""
    gross, f = np.asarray(gross, float), np.asarray(f, float).reshape(len(gross), -1)
    T, N = gross.shape
    G = gross.T @ gross / T
    D = gross.T @ with_constant(f) / T
    b = np.linalg.solve(D.T @ np.linalg.solve(G, D), D.T @ np.linalg.solve(G, np.ones(N)))
    miss = D @ b - 1
    return np.sqrt(miss @ np.linalg.solve(G, miss))


def resampled(T, block=BLOCK, draws=DRAWS, seed=0):
    """Month positions for each draw, from circular blocks so that spells of high volatility stay together."""
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, T, size=(draws, T // block + 1))
    return (starts[:, :, None] + np.arange(block)).reshape(draws, -1)[:, :T] % T


def percentile_range(values):
    return tuple(np.percentile(values, [2.5, 97.5]))


def excess(name, model, start=None, end=None):
    """Excess returns and factors over the months the two files share, in per cent."""
    f, rf = factors(model)
    p = portfolios(name)
    months = p.index.intersection(f.index)
    p, f, rf = p.loc[months].loc[start:end], f.loc[months].loc[start:end], rf.loc[months].loc[start:end]
    return p.sub(rf, axis=0), f, rf


def summary(r, f):
    """One row of the tests for one model, one sample and one set of portfolios."""
    g, fm = grs(r, f), fama_macbeth(r, f)
    return {"months": len(r), "first": str(r.index[0]), "last": str(r.index[-1]), "grs_f": g["F"], "grs_p": g["p"], "grs_p_resampled": grs_resampled_p(r, f), "sharpe_alpha": g["sharpe_alpha"],
            "mean_abs_alpha": np.abs(fm["alpha"]).mean(), "max_abs_alpha": np.abs(fm["alpha"]).max(), "r2": fm["r2"], "adj_r2": fm["adj_r2"],
            "r2_constrained": fm["r2_constrained"], "intercept": fm["lambda"][0], "t_intercept_shanken": fm["lambda"][0] / fm["se_shanken"][0]}


def r2_range(r, f):
    r, f = r.to_numpy(), f.to_numpy()
    found = [cross_section_fit(r[p].mean(axis=0), time_series(r[p], f[p])[1])[1] for p in resampled(len(r))]
    return percentile_range(found)


def capm_line(returns, market):
    """The 2021 regression: raw mean returns on betas from raw returns on the market excess return."""
    (intercept, slope), r2 = cross_section_fit(returns.mean().to_numpy(), time_series(returns.to_numpy(), market.to_numpy())[1])
    return {"first": str(returns.index[0]), "last": str(returns.index[-1]), "months": len(returns), "r2": r2, "slope": slope, "intercept": intercept,
            "mean_mkt_rf": market.to_numpy().mean()}


def reproduction():
    r, table = read_reference()
    rows = [("2021 files", r, table["Mkt-RF"]), ("2021 files, stopped at 2019-12", r.loc[:"2019-12"], table["Mkt-RF"].loc[:"2019-12"])]
    p, (mkt, _) = portfolios(), factors("CAPM")
    rows += [("Current files, same months", p.loc[:REFERENCE_END], mkt.loc[:REFERENCE_END]),
             ("Current files, through latest", p, mkt.loc[p.index]),
             ("Current files, 1963-07 to latest", p.loc[COMMON_START:], mkt.loc[COMMON_START:])]
    return pd.DataFrame([{"sample": label} | capm_line(returns, m) for label, returns, m in rows])


def revisions():
    """How far the current files have moved from the 2021 copies over the same months."""
    r, table = read_reference()
    p = portfolios().loc[r.index]
    f = read_monthly(RAW / FACTOR_FILES["three"]).loc[r.index]
    gap = (p - r).abs()
    worst = gap.stack().idxmax()
    rows = [{"series": "25 portfolios", "mean_abs_monthly_change": gap.to_numpy().mean(), "largest_monthly_change": gap.to_numpy().max(), "where": f"{worst[0]} {worst[1]}",
             "largest_change_in_mean": (p.mean() - r.mean()).abs().max()}]
    for c in ("Mkt-RF", "SMB", "HML", "RF"):
        g = (f[c] - table[c]).abs()
        rows.append({"series": c, "mean_abs_monthly_change": g.mean(), "largest_monthly_change": g.max(), "where": str(g.idxmax()), "largest_change_in_mean": abs(f[c].mean() - table[c].mean())})
    return pd.DataFrame(rows)


def model_table():
    """Each model from the first month it has, then all three over the months they share."""
    rows = []
    for sample, start in (("Full history", None), ("Common sample", COMMON_START)):
        for model in MODELS:
            r, f, _ = excess(MAIN, model, start)
            low, high = r2_range(r, f)
            rows.append({"sample": sample, "model": model} | summary(r, f) | {"r2_low": low, "r2_high": high})
    return pd.DataFrame(rows)


def premia_table():
    """Estimated price of risk beside each factor's sample mean, which it would equal if the model held."""
    rows = []
    for sample, start in (("Full history", None), ("Common sample", COMMON_START)):
        for model in MODELS:
            r, f, _ = excess(MAIN, model, start)
            fm = fama_macbeth(r, f)
            means = np.r_[0, f.mean()]
            for i, name in enumerate(["Intercept", *f.columns]):
                rows.append({"sample": sample, "model": model, "term": name, "lambda": fm["lambda"][i], "factor_mean": means[i], "se_fm": fm["se_fm"][i],
                             "se_shanken": fm["se_shanken"][i], "t_fm": fm["lambda"][i] / fm["se_fm"][i], "t_shanken": fm["lambda"][i] / fm["se_shanken"][i]})
    return pd.DataFrame(rows)


def subperiod_table():
    rows = []
    for label, (start, end) in PERIODS.items():
        for model in MODELS:
            r, f, _ = excess(MAIN, model, start, end)
            if len(r) == 0 or r.index[0] > pd.Period(start, "M"):
                continue
            fm = fama_macbeth(r, f)
            rows.append({"period": label, "model": model} | summary(r, f)
                        | {"market_price": fm["lambda"][1], "t_market_shanken": fm["lambda"][1] / fm["se_shanken"][1], "mkt_mean": f["Mkt-RF"].mean()})
    return pd.DataFrame(rows)


def other_assets_table():
    """The same tests on portfolios the factors were or were not built from, over the months they share."""
    rows = []
    for name in PORTFOLIO_FILES:
        for model in MODELS:
            r, f, _ = excess(name, model, COMMON_START)
            rows.append({"portfolios": name, "model": model} | summary(r, f))
    return pd.DataFrame(rows)


def spanning_table():
    """Does a factor have an alpha against the others? All from the five-factor file, 1963-07 to latest."""
    f = read_monthly(RAW / FACTOR_FILES["five"])
    tests = [(["SMB", "HML"], ["Mkt-RF"]), (["RMW", "CMA"], ["Mkt-RF", "SMB", "HML"]), (["HML"], ["Mkt-RF", "SMB", "RMW", "CMA"]),
             (["SMB"], ["Mkt-RF", "HML", "RMW", "CMA"]), (["RMW"], ["Mkt-RF", "SMB", "HML", "CMA"]), (["CMA"], ["Mkt-RF", "SMB", "HML", "RMW"])]
    rows = []
    for added, base in tests:
        alpha = time_series(f[added].to_numpy(), f[base].to_numpy())[0]
        g = grs(f[added], f[base])
        rows.append({"added": " + ".join(added), "against": ", ".join(base), "alpha_per_month": " / ".join(f"{a:.3f}" for a in alpha), "grs_f": g["F"], "grs_p": g["p"]})
    return pd.DataFrame(rows)


def sharpe_table():
    """Highest monthly Sharpe ratio available from each model's factors, annualised, from the five-factor file."""
    f = read_monthly(RAW / FACTOR_FILES["five"])
    rows = []
    for model, columns in MODELS.items():
        x = f[columns]
        rows.append({"model": model, "annual_sharpe": np.sqrt(12 * x.mean() @ np.linalg.solve(x.cov().to_numpy(), x.mean().to_numpy()))})
    return pd.DataFrame(rows)


def hj_table():
    """Gross returns of the 25 portfolios and the T-bill, with the common sample, and a constant SDF as the floor to beat."""
    rows = []
    for model in [None, *MODELS]:
        r, f, rf = excess(MAIN, model or "CAPM", COMMON_START)
        gross = np.column_stack([1 + (r.add(rf, axis=0)).to_numpy() / 100, 1 + rf.to_numpy() / 100])
        x = f.to_numpy() / 100 if model else np.empty((len(r), 0))
        low, high = percentile_range([hj_distance(gross[p], x[p]) for p in resampled(len(r))])
        rows.append({"model": model or "Constant SDF", "hj_distance": hj_distance(gross, x), "low": low, "high": high, "months": len(r)})
    return pd.DataFrame(rows)


def alpha_table():
    """Each portfolio's alpha under each model, common sample, for the five-by-five chart."""
    rows = {}
    for model in MODELS:
        r, f, _ = excess(MAIN, model, COMMON_START)
        rows[model] = pd.Series(time_series(r.to_numpy(), f.to_numpy())[0], index=r.columns)
    return pd.DataFrame(rows).rename_axis("portfolio").reset_index()


def rolling_r2(window=120):
    """Cross-sectional R² of each model over each ten-year window ending that month."""
    out = {}
    for model in MODELS:
        r, f, _ = excess(MAIN, model)
        x, y = r.to_numpy(), f.to_numpy()
        out[model] = pd.Series({r.index[t - 1]: cross_section_fit(x[t - window:t].mean(axis=0), time_series(x[t - window:t], y[t - window:t])[1])[1]
                                for t in range(window, len(r) + 1)})
    return pd.DataFrame(out).rename_axis("window_end").reset_index()


def fitted_table():
    """Mean return against each model's cross-sectional fit, common sample."""
    rows = []
    for model in MODELS:
        r, f, _ = excess(MAIN, model, COMMON_START)
        fm = fama_macbeth(r, f)
        fitted = with_constant(fm["beta"]) @ fm["lambda"]
        rows += [{"model": model, "portfolio": c, "mean": m, "fitted": v, "market_beta": b} for c, m, v, b in zip(r.columns, r.mean(), fitted, fm["beta"][:, 0])]
    return pd.DataFrame(rows)


def size_table(trials=200, draws=300):
    """How often each GRS p-value falls below 5% when every alpha is truly zero: 25 assets, one factor, normal or fat-tailed errors."""
    rows = []
    for T in (72, 213, 759):
        for errors, draw in (("normal", lambda g, size: g.normal(0, 2, size)), ("t, 4 df", lambda g, size: 1.4 * g.standard_t(4, size))):
            rng = np.random.default_rng(T)
            exact, boot = [], []
            for _ in range(trials):
                f = rng.normal(0.5, 4, size=(T, 1))
                r = f @ rng.uniform(0.5, 1.5, size=(25, 1)).T + draw(rng, (T, 25))
                exact.append(grs(r, f)["p"] < 0.05)
                boot.append(grs_resampled_p(r, f, draws=draws) < 0.05)
            rows.append({"months": T, "errors": errors, "rejects_f": np.mean(exact), "rejects_resampled": np.mean(boot)})
    return pd.DataFrame(rows)


def main():
    OUTPUT.mkdir(exist_ok=True)
    tables = {"reproduction": reproduction(), "revisions": revisions(), "models": model_table(), "premia": premia_table(), "subperiods": subperiod_table(),
              "other_assets": other_assets_table(), "spanning": spanning_table(), "sharpe": sharpe_table(), "hj_distance": hj_table(), "alphas": alpha_table(),
              "fitted": fitted_table(), "rolling_r2": rolling_r2(), "resampled_size": size_table()}
    for name, table in tables.items():
        table.to_csv(OUTPUT / f"{name}.csv", index=False, float_format="%.5g")
        print(f"\n{name}\n{table.tail(6).to_string(index=False) if name in ('rolling_r2', 'fitted') else table.to_string(index=False)}")


if __name__ == "__main__":
    main()
