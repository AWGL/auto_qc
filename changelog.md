# Changelog
This format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
It contains all changes from 2024-07-09 onwards

## [Unreleased]

### Added
- CPF is now displayed alongside Q30 in the run QC table, and a warning is raised if this is below 60

### Changed
- WGS sex now returns the estimated ploidy for samples that are not XX or XY

### Removed
- FastQC check has been removed for NonacusFH to bring it in line with WES and WGS