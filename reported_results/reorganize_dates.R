library(readr)
library(dplyr)
library(stringr)
library(tidyr)

contest_set <- read_csv("C:/Users/User/Documents/fairvote/projects/rcv-cruncher/contest_sets/all_contests/contest_set.csv")

new_date_formats <- read_csv("C:/Users/User/Documents/fairvote/projects/rcv-cruncher/reported_results/single_winner_dates.csv")

new_date_formats <- 
  new_date_formats %>%
  unite(id, Jurisdiction, State, Year, Office, sep = "_")

contest_set <- 
  contest_set %>%
  unite(id, place, state, date, office, sep = "_", remove = FALSE)

df <- left_join(contest_set, new_date_formats, by = "id")

write_csv(df, "C:/Users/User/Documents/fairvote/projects/rcv-cruncher/reported_results/partial_dates_added.csv", na = "")