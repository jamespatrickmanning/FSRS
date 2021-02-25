<div align="justify">

# FSRS_QC
Collection of manuals and scripts to assist in automated quality assurance and quality control for bottom temperature data collected via lobster traps as a platform.

<br>

## Manual

Version 1

February 2020

Authors: James Manning, Cooper Van Vranken \& Carles Castro Muniain

<br>

## Table of contents

<!--ts-->

* [Flags](#flags)
* [Real-time Quality control](#real-time-quality-control)
	* [Fisheries quality control tests](#fisheries-quality-control-tests)
		* [Platform identification (under development)](#platform-identification-under-development)
		* [Vessel ID control (under development)](#vessel-id-control-under-development)
		* [Gear type control (under development)](#gear-type-control-under-development)
	* [Quality control tests CTD](#quality-control-test-ctd)
		* [Impossible date test](#impossible-date-test)
		* [Impossible location test](#impossible-location-test)
		* [Position on land test](#position-on-land-test)
		* [Impossible speed test](#impossible-speed-test)
		* [Global range test](#global-range-test)
		* [Spike test](#spike-test)
		* [Digit rollover test](#digit-rollover-test)
		* [Stuck value / flat line test](#stuck-value-flat-line-test)
		* [Rate of change test](#rate-of-change-test)
		* [Timing / gap test](#timing-gap-test)
		* [Climatology test](#climatology-test)
		* [Drift test (under development)](#drift-test-under-development)
	* [Quality control tests oxygen / turbidity (under development)](#quality-control-tests-oxygen-turbidity-under-development)
* [Delayed-mode Quality control (under development)](#delayed-mode-quality-control-under-development)
* [Quality control tests (under development)](#quality-control-tests-under-development)
* [References](#references)

<!--te-->

<br>

## Flags

The data collected by lobster traps, i.e. with sensors attached to the lobster pot. In order to maximize (re)usability, the data is quality controlled and flagged to characterize data. Flags are always included in the data delivery, to optimize data reliability and consistency.

Flags are indicated in Table 1.

<div align="center">

| **Code** | **Meaning** |
| :---: | :---: |
| 0/NA | No QC was performed |
| 1 | Good data |
| 3 | Suspect data |
| 4 | Bad data |
| 5 | Corrected data |
| 9 | Missing value |

<sub> Table 1. Quality flags. </sub>

</div>

- Data flagged as (0) are not quality controlled, and therefore recommended not to be used without QC performed by the user.
- Data flagged as (1) have been quality controlled, and can be used safely.
- Data flagged as (3) have been quality controlled, and marked as suspect. These data can&#39;t be used directly, but have the potential to be corrected in delayed mode.
- Data flagged as (4) have been quality controlled and should be rejected.
- Data flagged as (5) have been corrected.
- Data flagged as (9) are missing.

<br>

### Filter quality control tests

Before explaining the filtering flag, some variables are created to understand the functionality of the filter.

 - Std: temperature standard deviation using a rolling of the 5 nearest samples.
 - Std2: temperature standard deviation using a rolling of the 48 nearest samples (2 days approximately).
 - IQR: temperature InterQuartile Range between quantiles 0.2 and 0.8 using a rolling of the 48 nearest samples.

<b>qc_spike</b>: 
	- Data is flagged as failed if the following conditions are not fulfilled.
		- Filter 1: Temperature < -3 ºC
		- Filter 2: 
			- If the IQR std from the entire dataset is greater than 1 ºC (there is some data logged out of the water):
				- IQR < 5 ºC and std2 < 1 ºC
				- Std is recalculated using a rolling of the 5 nearest samples after the application of the previous filter.
				- Std < 0.8 ºC
			- If the IQR std is lower than or equal to 1 ºC
				- Std < 1 ºC
	- Data is flagged as suspect if the following conditions are not fulfilled.
		- Std is recalculated using a rolling of the 5 nearest samples after the application of filter 2.
		- Filter 3: 
			- If the IQR std > 1 ºC:
				- Contains all data within the recalculated 0.98 std.
				- A new variable called gap_time is calculated by comparing consecutive rows from the already filtered dataset. Since most of the air data is filtered, gaps between consecutive rows are considerably large.
				- Applying gap_time > 1.8 days, first and last gap times are found. Data between these times are filtered.
			- If the IQR std <= 1 ºC
				- Temp_med variable is created using the following formula: 
					<i>temp_med = abs(temp_logged - temp_logged.rolling(5).median)</i>
				- If <i>temp_med.max - (temp_med.max - temp_med.quantile(0.98)/2) > 1</i>, any data above 1 is filtered.
				- If <i>temp_med.max - (temp_med.max - temp_med.quantile(0.98)/2) <= 1</i>, any data above the bold formula is filtered as well.

<div align="center">

| **Flags** | **Description** |
| :---: | :---: |
| Fail (4) | _Filter 1 or filter 2_ |
| Suspect (3) | _Filter 3_ |
| Pass (1) | _Applies for test pass condition._ |

<sub> Table 11. Flat line flags. </sub>

</div>

<br>

### Bathymetry model quality control tests

<b>qc_bathmetry</b>: Uses the gebco model to compare with the logged depth: 
 - For depths above 20 meters, data is flagged as suspect if depth compared with the gebco model at the same location is greater than 10 meters.
 - For depths below 20 meters, data is flagged as suspect if the variance between depth and the gebco model at the same location is greater than 30%. 

<div align="center">

| **Flags** | **Description** |
| :---: | :---: |
| Suspect (3) | _Depth &gt; 20 meters: difference &gt; 10 meters <br> Depth &lt;= 20 meters: difference &gt; 15%_ |
| Pass (1) | _Applies for test pass condition._ |

<sub> Table 3. Gear type flags. </sub>

</div>

<br>

### Logged location model quality control tests

<b>qc_logged_location</b>: data is flagged as bad if consecutives samples are depth flagged as suspect and location has not varied. (Represents location has not been recorded).

<div align="center">

| **Flags** | **Description** |
| :---: | :---: |
| Suspect (3) | _Location difference is &gt; 1 km_ |
| Pass (1) | _Applies for test pass condition._ |

<sub> Table 3. Gear type flags. </sub>

</div>

<br>

### Logged depth model quality control tests

<b>qc_logged_depth</b>: 
 - For depths above 20 meters, data is flagged as suspect if consecutives depths are greater than 10 meters.
 - For depths below 20 meters, data is flagged as suspect if consecutives depths are greater than 15%. 

<div align="center">

| **Flags** | **Description** |
| :---: | :---: |
| Suspect (3) | _Depth &gt; 20 meters: difference &gt; 10 meters <br> Depth &lt;= 20 meters: difference &gt; 15%_ |
| Pass (1) | _Applies for test pass condition._ |

<sub> Table 3. Gear type flags. </sub>

</div>

<br>