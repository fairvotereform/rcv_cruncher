Filename:	state_p14_sr_blk_map.dbf, state_p14_sr_blk_map.csv

File URL:	http://statewidedatabase.org/pub/data/P14/state/state_p14_sr_blk_map.zip

Dataset:	2014 Primary Election SR precinct to 2010 Census Block conversion file

Description:	This file contains statewide SR precinct to Census Block correspondances based on the proportion of registered voters geocoded to each precinct-block record. This file can be used to merge 2010 block or tract data to the 2014 Primary Election SR precincts as well as, to merge 2010 Census block or tract data to the 2014 Primary Election SR precincts.

Geographic Unit:	SR precincts are derived from consolidated precincts and are a geographic unit constructed for statistical merging purposes by the Statewide Database.  The Census Blocks are from the U.S. Census Bureau's 2010 TIGER/Line and are the smallest statistical reporting areas for decennial Census data. 

Technical documentation: http://statewidedatabase.org/d10/Creating%20CA%20Official%20Redistricting%20Database.pdf

File Fields:

	ELECTION - 3 digit, election abbreviation
	
	TYPE - geographic unit of file

	COUNTY - 1 to 3 digit numerical codes for California's counties

	FIPS - 2 digit state code FIPS for California, "06," followed by the 3 digit county FIPS code 

	SRPREC_KEY - FIPS code followed by the SR precinct number or name

	SRPREC - SR precinct number or name

	BLOCK_KEY - 15 digit block code consisiting of the 5 digit FIPS, 6 digit tract code and 4 digit block code.

	TRACT - 3 to 6 digit tract code without leading zeros
	
	BLOCK - 4 digit block code

	BLKREG - number of registered voters geocoded to the transecting SR precinct and Census Block area 

	SRTOTREG - total number of registered voters in the SR precinct

	PCTSRPREC - percent of the total number of registered voters in the SR precinct that are located within the 	transecting census block and is calculated by dividing BLKREG by the SRTOTREG i.e. PCTSRPREC = (BLKREG * 100) / 	SRTOTREG.

	BLKTOTREG - total number of registered voters in the Census Block

	PCTBLK - percent of the total number of registered voters in the 2010 Census Block that are located within the 	transecting SR precinct and is calculated by dividing BLKREG by the BLKTOTREG i.e. PCTBLK = (BLKREG * 100) / 	BLKTOTREG.

Date last modified:	Tue, 09 Oct 2018

Previous Versions:	none

County records not available or unavailable at time of file creation:	

051 - Mono county data are unavailable
