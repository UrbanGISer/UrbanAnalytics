# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.3] - 2025-10-14

### Fixed
- Fixed package structure by removing erroneous root-level `__init__.py` file
- Resolved import conflicts that prevented proper module loading
- Fixed missing `__version__` attribute in installed package

### Technical Details
- Removed duplicate `__init__.py` in project root directory
- Ensured correct package structure with only `r2sfca/r2sfca/__init__.py`
- Package now correctly exposes version information after installation

## [1.1.2] - 2025-10-14

### Fixed
- Fixed `solve_beta` method to correctly maximize correlation metric instead of minimizing it
- Correlation optimization now properly uses negative values internally while returning positive correlation in results
- Both `minimize` (scipy) and `adam` optimization methods are corrected
- All correlation-based metrics (`correlation`, `fij_flow_correlation`, `tij_flow_correlation`) now properly maximized

### Technical Details
- Modified `_solve_beta_minimize` objective function to negate correlation metrics
- Modified `_solve_beta_adam` loss calculation to negate correlation metrics
- Ensures cross-entropy, RMSE, MSE, MAE continue to be minimized correctly

## [1.1.1] - 2025-01-04

### Changed
- Updated citation to journal article format
- Fixed package name capitalization in documentation
- Added optional parameter examples in documentation

## [1.1.0] - 2025-01-04

### Changed
- Updated author email addresses
- Improved documentation and examples

## [1.0.0] - 2025-01-04

### Authors
- Lingbo Liu (lingboliu@fas.harvard.edu)
- Fahui Wang (fwang@lsu.edu)

### Added
- Initial release of R2SFCA package
- Core R2SFCA class with spatial accessibility analysis capabilities
- Support for 6 distance decay functions:
  - Exponential
  - Power
  - Sigmoid (with median travel cost scaling)
  - Square Root Exponential
  - Gaussian
  - Log-Squared
- Fij and Tij calculation methods (2SFCA and i2SFCA)
- Grid search functionality for parameter optimization
- Adam optimizer for beta parameter estimation
- Accessibility and crowdedness score calculations
- Comprehensive evaluation metrics (cross-entropy, correlation, RMSE, MSE, MAE)
- Visualization utilities for grid search results
- Support for observed flow validation
- Configurable epsilon parameter for numerical stability
- Parameter validation and error handling

### Features
- Unified framework reconciling demand-side and supply-side accessibility measures
- Automatic parameter scaling for sigmoid function using median travel cost
- Flexible parameter specification (fixed values or ranges)
- Comprehensive documentation and examples
- MIT license for open-source use

### Technical Details
- Python 3.8+ compatibility
- Dependencies: numpy, pandas, scipy, matplotlib, seaborn
- Type hints throughout codebase
- Comprehensive error handling and validation
- Numerical stability improvements for sigmoid function
