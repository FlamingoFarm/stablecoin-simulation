import numpy as np


def jump_diffusion(S, params, seed=None, num_paths=1, timesteps=1, delta_t=1 / 365):
    """
    Monte Carlo simulation of Merton's Jump Diffusion Model.
    The model is specified through the stochastic differential equation (SDE):

                        dS(t)
                        ----- = mu*dt + sigma*dW(t) + dJ(t)
                        S(t-)

    with:

    mu, sigma: constants, the drift and volatility coefficients of the stock
               price process;
    W: a standard one-dimensional Brownian motion;
    J: a jump process, independent of W, with piecewise constant sample paths.
       It is defined as the sum of multiplicative jumps Y(j).

    Input
    ---------------------------------------------------------------------------
    S: float. The current asset price.
    params: Contains the following parameters:
        mu, sigma: float. Respectively, the drift and volatility coefficients of
                the asset price process.
        lam: float. The intensity of the Poisson process in the jump diffusion
                model.
        a, b: float. Parameters required to calculate, respectively, the mean and
            variance of a standard lognormal distribution, log(x) ~ N(a, b**2).
            (see code).
    timesteps: int. The number of time steps.
    num_paths: int. The number of Monte Carlo simulations (at least 10,000 required
          to generate stable results).
    seed: int. Set random seed, for reproducibility of the results. Default
          value is None (the best seed available is used, but outcome will vary
          in each experiment).

    References
    ---------------------------------------------------------------------------
    [1] Glasserman, P. (2003): 'Monte Carlo Methods in Financial Engineering',
        Springer Applications of Mathematics, Vol. 53
    [2] Merton, R.C. (1976): 'Option Pricing when Underlying Stock Returns are
        Discontinuous', Journal of Financial Economics, 3:125-144.
    [3] https://github.com/federicomariamassari/financial-engineering
    """

    mu = params["coll_price_drift"]
    sigma = params["coll_price_vol"]
    lam = params["jump_rate"]
    a = params["jump_param_a"]
    b = params["jump_param_b"]

    # Set random seed
    np.random.seed(seed)

    simulated_paths = np.zeros([num_paths, timesteps + 1])
    simulated_paths[:, 0] = S

    """
    To account for the multiple sources of uncertainty in the jump diffusion
    process, generate three arrays of random variables.

     - The first one is related to the standard Brownian motion, the component
       epsilon(0,1) in epsilon(0,1) * np.sqrt(dt);
     - The second and third ones model the jump, a compound Poisson process:
       the former (a Poisson process with intensity Lambda) causes the asset
       price to jump randomly (random timing); the latter (a Gaussian variable)
       defines both the direction (sign) and intensity (magnitude) of the jump.
    """
    Z_1 = np.random.normal(size=[num_paths, timesteps])
    Z_2 = np.random.normal(size=[num_paths, timesteps])
    Poisson = np.random.poisson(lam * delta_t, [num_paths, timesteps])

    # Populate the matrix with Nsim randomly generated paths of length Nsteps
    for i in range(timesteps):
        simulated_paths[:, i + 1] = simulated_paths[:, i] * np.exp(
            (mu - sigma**2 / 2) * delta_t
            + sigma * np.sqrt(delta_t) * Z_1[:, i]
            + a * Poisson[:, i]
            + b * np.sqrt(Poisson[:, i]) * Z_2[:, i]
        )

    return simulated_paths.squeeze()
