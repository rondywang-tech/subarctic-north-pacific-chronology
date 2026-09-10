# Third-party notices

No third-party package source code or upstream package metadata is redistributed in this repository. The historical scripts call or import external software that users must install separately under the upstream terms.

| Dependency | Recorded/used version | Upstream licence | Role |
|---|---:|---|---|
| R | 4.1.0 | GPL-2.0-or-later | Runtime |
| rbacon | 3.5.2 | GPL-2.0-or-later | Bayesian age-depth modelling |
| rintcal | 1.4.0 | GPL-2.0-or-later | Calibration-curve access |
| posterior | 1.7.0 | BSD-3-Clause | MCMC diagnostics |
| diptest | 0.77-2 | GPL-2.0-or-later | Dip-test diagnostic; install separately from upstream |
| NumPy | external dependency | BSD-3-Clause | Numerical arrays |
| pandas | external dependency | BSD-3-Clause | Tabular processing |
| Matplotlib | external dependency | Matplotlib licence (PSF/BSD-style) | Figures |
| Cartopy | external dependency | LGPL-3.0-or-later | Geographic plotting |

Imports and calls to these separately installed dependencies do not copy their source code or package metadata into this release. Refer to each upstream project for complete current licence texts and dependency terms.
