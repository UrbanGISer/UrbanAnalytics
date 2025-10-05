# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
