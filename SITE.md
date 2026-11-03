# Proposed site text

For the session that integrates the website. Nothing here has been added to the site.

## Portfolio entry

**Title:** Does the CAPM still hold? Testing it and the Fama-French factor models through 2026

**Type and year:** Open data analysis in Python, 2026

**Text:** Tests of the capital asset pricing model and the Fama-French three- and five-factor models on US stock returns from 1926 to 2026, starting from a reproduction of my 2021 result. All three models are rejected on the usual size and value portfolios, although the factors explain far more of the differences in average returns than market beta does. On industry portfolios the extra factors make the errors larger.

**Links:** Project page, and code at https://github.com/atamalfuzi/capm_factor_tests

## Project page

### Summary

The capital asset pricing model (CAPM) says a stock's expected return depends only on its market beta, how strongly it moves with the market as a whole. I test it on US stock returns from 1926 to September 2026, along with the Fama-French three-factor model, which adds company size and value, and the five-factor model, which also adds profitability and investment. The data come from the Kenneth French Data Library.

The tests ask two things. Are the returns a model leaves unexplained, its alphas, zero across 25 portfolios? And do portfolios with higher betas earn higher average returns, by the amount the model predicts?

### The CAPM

Figure: `figures/capm_line.png`

In 2021, betas explained 11.4% of the differences in average returns across these portfolios, and that figure reproduces exactly from the same files. With today's files and data through 2026, it is 9.8%. Since 1963 the relation runs the wrong way, with higher-beta portfolios earning slightly less. The joint test of the alphas rejects the CAPM with a p-value below 0.001.

### What the extra factors add

Figures: `figures/model_fit.png`, then `figures/alphas.png`

Since 1963, the share of differences in average returns explained rises from 8% under the CAPM to 66% with three factors and 75% with five. The three-factor model halves the average alpha. The five-factor model mainly shrinks the largest one, for small growth stocks. All three models are still rejected. The value factor adds nothing once profitability and investment are included, as Fama and French found in 2015.

### Over time, and on other portfolios

Figures: `figures/rolling_r2.png`, then `figures/alpha_by_assets.png`

The CAPM is not rejected before 1963. The factor models fit best from 1963 to 1990, and since 2009 no model explains more than 16%. The usual test portfolios are sorted on the same features the factors are built from, which makes the test easy for the factor models. On 30 industry portfolios the CAPM is not rejected, and adding factors makes the alphas larger.

### Notes for the page

- Use the "Personal project" disclaimer from the README.
- Keep the note that results describe files built from the 202609 CRSP database.
- The tables in the README can be reused as they are. The source numbers are in `output/`.
