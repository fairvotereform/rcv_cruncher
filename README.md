# FairVote RCV Cruncher

The cruncher is a python-based tool. You can use it to process cast vote records from RCV/IRV/STV jurisdictions and calculate various nifty statistics for each contest.

This is a command line tool and does not have a user interface. If you are unfamiliar with the command line, hopefully the instructions below will help you get started.

#### ReadMe contents

* [Installation](##Installation)
* [Crunching a contest](##Crunchingacontest)
  * Preparation
  * Example contest
  * Quick summary   
* Capabilities (CVR types)
* Output Documentation

## Installation

##### Short version (you know how github works and can use the command line)
* Clone the cruncher github repository (`git clone https://github.com/fairvotereform/rcv_cruncher.git`).

##### Longer version (you're not so familiar with the command line)
* Clone the cruncher github repository (`git clone https://github.com/fairvotereform/rcv_cruncher.git`) or download a copy of the repository files from github by clicking the green "Code" button on this [page](https://github.com/fairvotereform/rcv_cruncher).

## Crunching a contest

##### Preparation

There are some files that need to be set up before you can make any RCV calculations with your CVR file.
