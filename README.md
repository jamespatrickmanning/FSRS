# FSRS
This is a collection of python code to process FSRS bottom temperatures collected by Nova Scotia lobstermen 1999-2019.
There is a pair of rather extensive googledocs that describe the work done in Jim Manning's lab circa 2017-2020 in an attempt to document, archive, and serve this valuable dataset.
One is called "eMOLT_FSRS_notes" (https://docs.google.com/document/d/1VhBAl3sQAY0fMt66NVJWhwmiBJrTikGbu0k-grnCsmI/edit#) with logistics of merging the two datasets and one is called "eMOLT_FSRS_results"
(https://docs.google.com/document/d/1SJTWRh412x-rjyTOST97Wf7yG5yx8i-Ao7hEZciMjO4/edit#) with some of the results.

You will see that the most useful code is from recent years (~2020) which deal with the raw hourly data derived from the original Minilog files.
The old code (<2018) was used to examine some of the other daily-averaged versions of the dataset that had been processed in various ways by various labs.
The new code called "fsrs2emolt.py" processes the raw Minilog csv files assuming there is an associated latlon text file documenting where each unit was deployed.
There is a couple different flowcharts describing this fsrs2emolt routine. We keep our flowchart in "drawio" format at, for example, https://app.diagrams.net/#G1_GAfd70eh8BBU2I4BGuuvtfQwh8ChLLL but a Oct 2020 pdf version is provided in this repository.

As of Oct 2, 2020, this routine has only been run on a couple years of data for Lobster Fishing Area #34. It may take weeks to process all the data.

On Dec 29, 2020, at the request of Cooper and his BDC colleagues, I up loaded a set of example input files for the case of LFA#34 2012-2013.  Contained in the "lfa34_1213.tar" file is a header file "LatLong LFA 34_1213.txt" along with a few dozen minilog ascii files like, for example, "Minilog-T_3376_20130705_1.csv".  

Note that there is a set of hardcodes at the top of "fsrs2emolt.py" that need to be modified for each run.  The year,  LFA, and location of these input files on your machine need to be specified. for example.

