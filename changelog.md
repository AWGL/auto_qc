# Changelog
This format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
It contains all changes from 2024-07-09 onwards

## [Unreleased]

## [v2.0.2] - 04/10/2024

### Fixed
- Hotfix, commas missing from config file
- Hotfix, BRCA does not produce _intersect.txt

## [v2.0.1] - 03/10/2024

### Added
- Update config for CRM now going into SVD
- Update min and max variants in FH config

## [v2.0.0] - 11/07/2024

### Added
- CPF is now displayed alongside Q30 in the run QC table, and a warning is raised if this is below 60
- This changelog, only showing changes as of 2024-07-09 onwards

### Changed
- WGS sex now returns the estimated ploidy for samples that are not XX or XY

### Removed
- FastQC check has been removed for NonacusFH to bring it in line with WES and WGS
