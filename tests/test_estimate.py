"""The 2021 figure and the estimators, against statsmodels, SciPy and simulations. No downloads."""
import numpy as np
import pytest
import statsmodels.api as sm
from scipy.optimize import minimize
from statsmodels.multivariate.multivariate_ols import _MultivariateOLS

from data import read_reference
from estimate import capm_line, cross_section_fit, fama_macbeth, grs, grs_resampled_p, hj_distance, resampled, time_series


def panel(T=600, N=10, L=2, alpha=0.0, seed=0):
    rng = np.random.default_rng(seed)
    f = rng.normal(0.5, 2, size=(T, L))
    b = rng.uniform(0.5, 1.5, size=(N, L))
    return alpha + f @ b.T + rng.normal(0, 2, size=(T, N)), f


def test_reproduces_the_2021_regression():
    r, table = read_reference()
    fit = capm_line(r, table["Mkt-RF"])
    assert (fit["first"], fit["last"], fit["months"]) == ("1926-07", "2020-09", 1131)
    assert round(fit["r2"], 4) == 0.1144  # the R^2 reported by the 2021 run
    assert round(fit["slope"], 4) == 0.3993
    assert round(fit["mean_mkt_rf"], 2) == 0.67


def test_2021_extremes_are_the_small_portfolios_it_names():
    means = read_reference()[0].mean()
    assert (means.idxmax(), means.idxmin()) == ("SMALL HiBM", "SMALL LoBM")


def test_taking_out_the_t_bill_moves_only_the_intercept():
    r, table = read_reference()
    raw, net = capm_line(r, table["Mkt-RF"]), capm_line(r.sub(table.RF, axis=0), table["Mkt-RF"])
    assert net["r2"] == pytest.approx(raw["r2"]) and net["slope"] == pytest.approx(raw["slope"])
    assert net["intercept"] != pytest.approx(raw["intercept"])


def test_grs_with_one_asset_is_the_squared_t_of_its_alpha():
    r, f = panel(N=1, alpha=0.2)
    fit = sm.OLS(r[:, 0], sm.add_constant(f)).fit()
    found = grs(r, f)
    assert found["F"] == pytest.approx(fit.tvalues[0] ** 2)
    assert found["p"] == pytest.approx(fit.pvalues[0])


def test_grs_matches_the_multivariate_test_of_the_intercepts():
    r, f = panel(N=10, alpha=0.1)
    test = _MultivariateOLS(r, sm.add_constant(f)).fit().mv_test().results["x0"]["stat"]  # x0 is the constant
    assert grs(r, f)["F"] == pytest.approx(float(test.loc["Wilks' lambda", "F Value"]))
    assert grs(r, f)["p"] == pytest.approx(float(test.loc["Wilks' lambda", "Pr > F"]))


def test_grs_is_correctly_sized_when_the_alphas_are_zero():
    found = [grs(*panel(T=120, N=10, seed=s))["p"] for s in range(1000)]
    assert np.mean(np.array(found) < 0.05) == pytest.approx(0.05, abs=0.02)


def test_grs_stops_when_months_are_too_few():
    with pytest.raises(ValueError):
        grs(*panel(T=12, N=10))


def test_resampled_p_is_low_with_alphas_and_not_without():
    assert grs_resampled_p(*panel(alpha=0.5), draws=200) < 0.01
    assert grs_resampled_p(*panel(alpha=0.0), draws=200) > 0.1


def test_fama_macbeth_averages_equal_one_regression_on_mean_returns():
    r, f = panel()
    fm = fama_macbeth(r, f)
    coef, r2 = cross_section_fit(r.mean(axis=0), time_series(r, f)[1])
    assert fm["lambda"] == pytest.approx(coef)
    assert fm["r2"] == pytest.approx(r2)


def test_fama_macbeth_finds_the_prices_when_betas_are_known_to_fit():
    r, f = panel(T=20000, N=25, L=1, seed=1)
    fm = fama_macbeth(r - r.mean(axis=0) + 0.2 + time_series(r, f)[1] @ f.mean(axis=0), f)
    assert fm["lambda"] == pytest.approx([0.2, f.mean()])
    assert fm["r2"] == pytest.approx(1)
    assert fm["r2_constrained"] < 1


def test_shanken_errors_match_the_spread_of_the_estimates_when_betas_are_noisy():
    """With a high Sharpe ratio factor and noisy betas, Fama-MacBeth errors are too small and the correction closes the gap."""
    rng = np.random.default_rng(0)
    T, N = 600, 25
    b = np.linspace(0.2, 1.8, N)
    prices, fm_se, shanken_se = [], [], []
    for _ in range(2000):
        f = rng.normal(1.5, 2.0, size=(T, 1))
        r = f @ b[None, :] + rng.normal(0, 5, size=(T, N))
        fm = fama_macbeth(r, f)
        prices.append(fm["lambda"][1])
        fm_se.append(fm["se_fm"][1])
        shanken_se.append(fm["se_shanken"][1])
    actual = np.std(prices)
    assert np.mean(fm_se) < 0.95 * actual
    assert np.mean(shanken_se) == pytest.approx(actual, rel=0.05)


def test_hj_distance_is_the_minimum_of_the_pricing_error_norm():
    r, f = panel(N=8)
    gross, f = 1 + r / 100, f / 100
    G_inv = np.linalg.inv(gross.T @ gross / len(r))
    D = gross.T @ np.column_stack([np.ones(len(f)), f]) / len(r)
    numeric = minimize(lambda b: (D @ b - 1) @ G_inv @ (D @ b - 1), np.zeros(3), method="BFGS", options={"gtol": 1e-10}).fun
    assert hj_distance(gross, f) == pytest.approx(np.sqrt(numeric), rel=1e-4)


def test_hj_distance_is_zero_with_as_many_parameters_as_assets():
    r, f = panel(N=3)
    assert hj_distance(1 + r / 100, f / 100) == pytest.approx(0, abs=1e-6)


def test_hj_distance_never_rises_as_factors_are_added():
    r, f = panel(N=8)
    gross, f = 1 + r / 100, f / 100
    assert hj_distance(gross, np.empty((len(r), 0))) >= hj_distance(gross, f[:, :1]) >= hj_distance(gross, f)


def test_resampled_positions_run_in_blocks_and_wrap():
    picks = resampled(100, block=12, draws=5)
    assert picks.shape == (5, 100) and picks.min() >= 0 and picks.max() < 100
    assert np.all((picks[0, 1:12] - picks[0, :11]) % 100 == 1)
