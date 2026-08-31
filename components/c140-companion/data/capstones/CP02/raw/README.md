# Supporting data for assessing impacts of satellite GPS transmitters on survival, nesting propensity, and nest success of greater sage-grouse

<https://doi.org/10.5061/dryad.573n5tbf3>

The data files contain data used to conduct the following analyses: 1) multi-state modeling of daily mortality probabilities for hen sage-grouse in program MARK (MultiState.inp), 2) nest survival modeling to estimate daily nest survival probabilities for greater sage grouse in program MARK (NestSurvival.inp), 3) mixed effects logistic regression modeling of nesting propensity for hen sage-grouse (i.e., proportion of females initiating a nest) in program R (nest_propensity.csv), and 4) mixed effects Gaussian regression modeling of timing of nest initiation for hen sage-grouse in program R (NestTiming.R). In addition, analysis scripts, written in R language, are provided for analyses 3 (LogisticReg.R) and 4 (GaussianReg.R) above. These R scripts are self contained and annotated within to explain each piece of code.

## Description of the data and file structure

### Description of the data and file structure for file MultiState.inp for multi-state model analyses in MARK

Each row of data represents a single encounter history observation and the corresponding covariates.

The first column of data is a string of data for n = 154 encounter occasions, with each observation consisting of either: "A" (observed alive), "D" (observed dead), "." (no attempt to monitor and therefore no data), "0" (attempted to monitor but failed to detect).

Columns 2-4 represent animal group number, transmitter type (0 = VHF transmitter, 1 = PTT transmitter), and age of hen (1 = yearling, 0 = adult). Columns 5-9 represent individual covariates (binary indicator variables) for each corresponding year of study (year 2016 is indicated by all other year columns being set to 0). All remaining columns contain time-specific individual covariate data for each observation day (days 1-153), which were used to fit the linear and quadratic time effects to model changes in daily mortality risk across the spring-summer period.

### Description of the data and file structure for file NestSurvival.inp for nest survival model analyses in MARK

Nesting data are organized for analysis according to two groups: 1) hens marked with VHF transmitters, and 2) hens marked with PTT transmitters.

Each row of data represents a single nest and its corresponding nest check data and covariates. The first column is a nest identification code that does not get used at all in the statistical analysis; it's there simply to indicate which nest is being observed.

Columns 2-5 contain the standard nest survival data (going left to right): day of the nesting season on which the nest was found, last day the nest was checked when alive, last day the nest was checked, and nest fate (0 = successful, 1 = depredated). Column 6 is all 1s and indicated the number of nests each row represents. Columns 7-13 are individual covariates for each corresponding year of study. Column 14 is ordinal day of nest initiation, and column 15 is nest age on the first observation day of each season (used to model nest age as an individual covariate).

### Description of the data and file structure for file nest\_propensity.csv for mixed effects logistic regression analyses in R

This csv file contains 6 columns: 1) transmitter type, 2) Year, 3) number of nests initiated (No_nests), and 4-5) total number of hens available for nesting under the conservative (Total_method_1) and liberal (Total_method_2) definitions of hens available for nesting (see methods section in manuscript text).

### Description of the data and file structure for file nest\_initiation\_data.csv for mixed effects Gaussian regression analyses in R

This csv file contains 5 columns of data: 1) individual nest ID, 2) year, 3) ordinal day of nest initiation, 4) transmitter type (VHF or PTT), and 5) age of hen (adult [A], yearling [Y], or not available [NA]).

## Sharing/Access information

NA

## Code/Software

Code scripts described above are written and executed in the R statistical computing language.
