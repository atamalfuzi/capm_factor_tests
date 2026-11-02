# capm_factor_tests

[![tests](https://github.com/atamalfuzi/capm_factor_tests/actions/workflows/tests.yml/badge.svg)](https://github.com/atamalfuzi/capm_factor_tests/actions/workflows/tests.yml)

Does the CAPM hold up on US stock returns through the latest available month, and how much do the Fama-French three- and five-factor models add? Python, with pandas and SciPy.

This is a redo of an exercise from ECON 815 (Financial Economics) at Simon Fraser University, Fall 2021, written as a standalone analysis on current data. Results are as of November 2026, with data through September 2026 from the Kenneth French Data Library, in files built from the 202609 CRSP database.

> **Personal project.** This is my own analysis of publicly available data. It is not associated with my work for any current or past employer and does not represent their views.

| Question | Methods | Answer |
|---|---|---|
| [Does the old result reproduce?](#1-does-the-old-result-reproduce) | The assignment's regression on its own files | Yes: R² 0.1144 and slope 0.3993. On current files through 2026-09, R² is 0.098. |
| [Does the CAPM hold up?](#2-does-the-capm-hold-up) | GRS, Fama-MacBeth with Shanken errors | No. GRS rejects it (p below 0.001), and since 1963 the slope on beta is negative. |
| [How much do the factors add?](#3-how-much-do-the-factors-add) | Same tests, spanning regressions, Hansen-Jagannathan distance | Since 1963, R² goes from 0.08 to 0.66 to 0.75, and mean absolute alpha from 0.19 to 0.09 to 0.09. GRS rejects all three. |
| [Is that stable?](#4-is-that-stable) | Subperiods, ten-year windows | No. The CAPM is not rejected before 1963, and since 2009 no model's R² is above 0.16. |
| [Does it depend on the portfolios?](#5-does-it-depend-on-the-portfolios) | Three more sets of test portfolios | Yes. On 30 industries, adding factors makes the alphas larger. |

## What it shows

Test portfolios are the 25 value-weighted portfolios formed on size and book-to-market, unless stated otherwise. Returns are monthly, in per cent, and in excess of the T-bill rate. The five-factor file starts in 1963-07, so comparisons of all three models use 1963-07 to 2026-09 (759 months).

### 1. Does the old result reproduce?

| Sample | Months | R² | Slope | Mean market excess return |
|---|---:|---:|---:|---:|
| Coursework files, 1926-07 to 2020-09 | 1131 | 0.1144 | 0.399 | 0.670 |
| Coursework files, stopped at 2019-12 | 1122 | 0.1035 | 0.402 | 0.667 |
| Current files, 1926-07 to 2020-09 | 1131 | 0.1176 | 0.413 | 0.671 |
| Current files, 1926-07 to 2026-09 | 1203 | 0.0978 | 0.399 | 0.694 |
| Current files, 1963-07 to 2026-09 | 759 | 0.0822 | −0.367 | 0.600 |

The first row matches the assignment's reported R² and slope, and a test checks it. The assignment's data ran to 2020-09, so stopping at the end of 2019 does not give its figure.

The assignment used raw returns where excess returns would be usual. This moves the intercept and leaves R² and the slope unchanged, because the T-bill rate shifts every beta by the same amount. Its Sharpe ratio divided by the standard deviation of the total market return, which gives 0.1255 against 0.1253.

French's files change over time as CRSP revises its data. Over the same months, the portfolio returns moved by 0.20 points a month on average and by up to 9.4 points in one month (SMALL LoBM, 1945-01), while no portfolio's mean moved by more than 0.016. That is why the same months now give 0.1176.

### 2. Does the CAPM hold up?

![Mean excess return against market beta](figures/capm_line.png)

| Sample | GRS F | p, F distribution | p, resampled | Mean absolute alpha | R² | Intercept (Shanken t) | Price of market risk (Shanken t) | Mean market excess return |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1926-07 to 2026-09 | 3.39 | 5×10⁻⁸ | below 0.001 | 0.154 | 0.098 | 0.41 (1.27) | 0.40 (1.15) | 0.69 |
| 1963-07 to 2026-09 | 4.17 | 1×10⁻¹⁰ | below 0.001 | 0.193 | 0.082 | 1.16 (3.12) | −0.37 (−0.92) | 0.60 |

The two samples have about the same R², and they say different things. Over the full history the slope has the right sign and is about 60% of the market premium. Since 1963 it is negative, and the intercept, which the CAPM says is zero, is 1.16% a month. The R² alone hides this.

The 95% resampled range for the R² since 1963 is 0.00 to 0.53, so one sample's R² is a rough measure.

### 3. How much do the factors add?

![Actual and fitted mean returns under each model](figures/model_fit.png)

| 1963-07 to 2026-09 | CAPM | Three-factor | Five-factor |
|---|---:|---:|---:|
| GRS F | 4.17 | 3.63 | 3.21 |
| p, F distribution | 1×10⁻¹⁰ | 9×10⁻⁹ | 3×10⁻⁷ |
| p, resampled | below 0.001 | below 0.001 | below 0.001 |
| Mean absolute alpha, % a month | 0.193 | 0.087 | 0.089 |
| Largest absolute alpha | 0.529 | 0.466 | 0.277 |
| Cross-sectional R² | 0.08 | 0.66 | 0.75 |
| Adjusted R² | 0.04 | 0.61 | 0.69 |
| 95% resampled range for R² | 0.00 to 0.53 | 0.22 to 0.85 | 0.39 to 0.90 |
| R² with intercept zero and prices at factor means | −0.85 | 0.42 | 0.59 |
| Hansen-Jagannathan distance | 0.375 | 0.351 | 0.328 |
| 95% resampled range | 0.339 to 0.513 | 0.316 to 0.480 | 0.278 to 0.451 |

The three-factor model does most of the work on these portfolios. It halves the mean absolute alpha and takes out most of the value pattern. The five-factor model leaves the mean alpha where it was and mainly shrinks the largest one, small growth, from −0.47 to −0.28. The R² ranges overlap, so these data do not separate the two models on that measure. All three are rejected.

![Alpha of each portfolio under each model](figures/alphas.png)

The row with a zero intercept and prices set at factor means is the stricter measure, since it is what the models actually claim. It can be negative: the CAPM line fits worse than a flat line through the mean.

Free cross-sectional prices can look odd. In the five-factor fit the market's price is −0.49 (Shanken t −1.52) beside an intercept of 1.05. Market betas barely vary across these portfolios, so the two are hard to tell apart. Their sum, 0.56, is close to the market's mean of 0.60. The Shanken correction changes little here, for example moving that t from −1.58, because monthly factor Sharpe ratios are small.

The Hansen-Jagannathan distance prices the gross returns of the 25 portfolios and the T-bill. A constant discount factor gives 0.400 (0.368 to 0.534), so the factors take off 6%, 12% and 18% of that distance. Each model's distance can only fall as factors are added, and the ranges overlap.

Whether a factor adds anything can also be tested on the factors alone, by asking whether it has an alpha against the others (five-factor file, 1963-07 to 2026-09):

| Added | Against | Alpha, % a month | p |
|---|---|---:|---:|
| SMB and HML | Market | 0.070 and 0.376 | 0.002 |
| RMW and CMA | Market, SMB, HML | 0.298 and 0.179 | 6×10⁻⁷ |
| HML | The other four | −0.025 | 0.75 |
| SMB | The other four | 0.181 | 0.08 |
| RMW | The other four | 0.335 | 3×10⁻⁵ |
| CMA | The other four | 0.207 | 1×10⁻⁴ |

HML has no alpha once the other four are in, the result Fama and French (2015) reported, and it still holds through 2026. The highest Sharpe ratio available from the factors rises from 0.47 a year to 0.65 and 0.95.

### 4. Is that stable?

| Period | Model | GRS F | p, F distribution | p, resampled | Mean absolute alpha | R² |
|---|---|---:|---:|---:|---:|---:|
| 1926-07 to 1963-06 | CAPM | 1.38 | 0.106 | 0.185 | 0.146 | 0.30 |
| | Three-factor | 1.65 | 0.027 | 0.092 | 0.147 | 0.63 |
| 1963-07 to 1990-12 | CAPM | 1.89 | 0.007 | 0.037 | 0.264 | 0.06 |
| | Three-factor | 1.31 | 0.154 | 0.203 | 0.089 | 0.77 |
| | Five-factor | 0.93 | 0.559 | 0.540 | 0.080 | 0.87 |
| 1991-01 to 2008-12 | CAPM | 4.20 | 5×10⁻⁹ | 0.008 | 0.334 | 0.34 |
| | Three-factor | 3.75 | 9×10⁻⁸ | 0.010 | 0.150 | 0.71 |
| | Five-factor | 3.47 | 6×10⁻⁷ | 0.075 | 0.188 | 0.71 |
| 2009-01 to 2026-09 | CAPM | 1.82 | 0.013 | 0.079 | 0.229 | 0.00 |
| | Three-factor | 1.71 | 0.024 | 0.119 | 0.090 | 0.14 |
| | Five-factor | 1.68 | 0.029 | 0.119 | 0.097 | 0.16 |
| 2020-10 to 2026-09 | CAPM | 1.73 | 0.053 | n/a | 0.414 | 0.07 |
| | Three-factor | 1.48 | 0.124 | n/a | 0.261 | 0.54 |
| | Five-factor | 1.64 | 0.076 | n/a | 0.258 | 0.64 |

The last row is the months since the assignment's data ended, and it overlaps the row above it.

Before 1963 the CAPM is not rejected and beta lines up with mean returns, though the price of market risk is imprecise (0.67, Shanken t 1.22). The three- and five-factor models fit best in 1963 to 1990, close to the period they were built on. Since 2009 their R² has fallen to 0.14 and 0.16, and whether they are rejected depends on the p-value used. The 72 months since 2020-10 are too few to settle much with 25 portfolios.

![R² over ten-year windows](figures/rolling_r2.png)

### 5. Does it depend on the portfolios?

![Mean absolute alpha by set of test portfolios](figures/alpha_by_assets.png)

| 1963-07 to 2026-09 | Model | GRS F | p, resampled | R² | Adjusted R² | R² at factor means |
|---|---|---:|---:|---:|---:|---:|
| Size and profitability | CAPM | 2.20 | 0.013 | 0.00 | −0.04 | −0.47 |
| | Three-factor | 2.48 | 0.003 | 0.57 | 0.51 | 0.31 |
| | Five-factor | 2.17 | 0.023 | 0.82 | 0.77 | 0.65 |
| Size and investment | CAPM | 4.46 | below 0.001 | 0.04 | 0.00 | −1.02 |
| | Three-factor | 3.96 | below 0.001 | 0.64 | 0.59 | 0.29 |
| | Five-factor | 3.11 | 0.002 | 0.64 | 0.54 | 0.57 |
| 30 industries | CAPM | 1.32 | 0.208 | 0.05 | 0.01 | −0.54 |
| | Three-factor | 2.22 | 0.007 | 0.13 | 0.03 | −1.54 |
| | Five-factor | 2.76 | 0.002 | 0.20 | 0.03 | −2.56 |

Size and book-to-market portfolios are a low bar, because the factors are built from the same sorts (Lewellen, Nagel and Shanken, 2010). The five-factor model's gain shows up on profitability sorts, as you would expect. On industries the pattern reverses: the CAPM is not rejected, and the extra factors raise the mean absolute alpha from 0.127 to 0.175 and 0.216. The CAPM's failure here is mostly about size and value sorted portfolios, and the extra factors do not carry over to portfolios formed another way.

## Data and checks

- All returns come from the [Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html). The five-factor file has its own SMB, which correlates 0.98 with the three-factor file's, so each model uses its own file. The market and T-bill series agree between the two files to within 0.08 and 0 points.
- `coursework/` holds the assignment's two data files, copied from my public [coursework archive](https://github.com/atamalfuzi/economics_coursework), so the reproduction test runs without a download.
- GRS assumes normal errors, so I also resample months in blocks of 12 with the alphas taken out. Simulating 200 samples with zero alphas (`output/resampled_size.csv`), the F test rejects at 5% in 4% to 8% of them. The resampled test rejects in about 5% at 759 months, 2% to 3% at 213 and never at 72. So it leans conservative in shorter samples, and it is left out for the 72-month row. The p-values in `output/` for that row should not be used. With 2000 draws its floor is 0.0005.
- Betas are full-sample within each period, and fitted means use the same data. Errors in the betas bias prices toward zero. The R² ranges are percentile ranges and not corrected for this.
- The subperiod rows are several tests on the same data, with no adjustment for that.
- Tests compare GRS with the squared t of one asset and with statsmodels' multivariate test, check its size by simulation, check Shanken errors against the actual spread of simulated estimates, and check the Hansen-Jagannathan distance against a numerical minimum.

## Run it

```bash
pip install -r requirements-dev.txt
python data.py
python estimate.py
python figures.py
pytest
```

`data.py` downloads the files to `data/`, which is not committed. `estimate.py` takes a few minutes because of the resampling and writes the tables to `output/`. `figures.py` draws the charts in `figures/` from those tables. New data will change the numbers, and the text above describes the files built from the 202609 CRSP database.

## References

- Fama, E. F. and French, K. R. (1993). Common risk factors in the returns on stocks and bonds. *Journal of Financial Economics*, 33(1), 3-56.
- Fama, E. F. and French, K. R. (2015). A five-factor asset pricing model. *Journal of Financial Economics*, 116(1), 1-22.
- Fama, E. F. and MacBeth, J. D. (1973). Risk, return, and equilibrium: empirical tests. *Journal of Political Economy*, 81(3), 607-636.
- Gibbons, M. R., Ross, S. A. and Shanken, J. (1989). A test of the efficiency of a given portfolio. *Econometrica*, 57(5), 1121-1152.
- Hansen, L. P. and Jagannathan, R. (1997). Assessing specification errors in stochastic discount factor models. *Journal of Finance*, 52(2), 557-590.
- Lewellen, J., Nagel, S. and Shanken, J. (2010). A skeptical appraisal of asset pricing tests. *Journal of Financial Economics*, 96(2), 175-194.
- Shanken, J. (1992). On the estimation of beta-pricing models. *Review of Financial Studies*, 5(1), 1-33.

## License

MIT. See [LICENSE](LICENSE).
