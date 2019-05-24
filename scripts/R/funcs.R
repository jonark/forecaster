library(XML)
library(dplyr)
library(purrr)
library(data.table)

load_GPX <- function(file_name) {
  gpx <- file_name %>%
    xmlTreeParse(useInternalNodes = TRUE) %>%
    xmlRoot %>%
    xmlToList %>%
    (function(x) x$trk) %>%
    (function(x) unlist(x[names(x) == "trkseg"], recursive = FALSE)) %>%
    map_df(function(x) as.data.frame(t(unlist(x)), stringsAsFactors=FALSE)) %>% 
    mutate(time = lubridate::parse_date_time(time, orders = "ymdHMS")) %>%
    mutate(time = time - min(time)) %>%
    sapply(as.double) %>% 
    as.data.table()

  colnames(gpx) <- c('ele', 'time', 'lat', 'lon')
  gpx
}

calculate_diffs <- function(gpx) {
  gpx[, ele:= smooth(ele, kind = '3RS3R'),] %>% 
    .[, c('ele_next', 'lat_next', 'lon_next', 'time_next'):= 
        list(lead(ele), lead(lat), lead(lon), lead(time)),] %>% 
    na.omit(.) %>%
    .[, id:= .I,] %>% 
    .[, dT:= time_next - time, by = id] %>% 
    .[, dH:= as.numeric(ele_next - ele), by = id] %>% 
    .[, dS:= geosphere::distGeo(c(lat, lon), c(lat_next, lon_next)),
      by = id] %>% 
    .[, dist:= round(cumsum(dS)*0.001,3),] %>% 
    .[, grade:= round(dH/dS * 100, 1),] %>% 
    select(id, time, dist, grade, dT, dS, dH)
}

# should give data table in the same schema as calculate_diffs returns
# data should be of a race effort over trail terain throughout 
# new column speed modifier, 1 for flat, less than one for ascents (with different
# levels), and more or less than one on descents( steep descents are slow)
get_gap_matrix <- function(data) {
  
}

gap_coefficient <- function(grade) {
  grade <- floor(grade / 2) * 2
  gap_mat <- data.table(grad = c(-30, -28, -26, -24, -22, -20, -18, -16, 
				  -14, -12, -10, -8, -6, -4, -2, 0, 
				  2, 4, 6, 8, 10, 12, 14, 16, 
				  18, 20, 22, 24, 26, 28, 30),
		        coef = c(2, 2, 2, 2, 2, 1, 1, 1,
				 0, 0, 0, -1, -1, -1, 0, 0,
				 0, 0, 1, 1, 1, 2, 2, 2,
				 2, 2, 3, 3, 3, 3, 3)) 
  ifelse (grade > 30, 
	 return (gap_mat[grad == 30, coef]),
	 ifelse (grade < -30,
		 return (gap_mat[grad == -30, coef]),
		 return (gap_mat[grad == grade, coef])))
}

grade_adjusted_effort <- function(data, flat_pace) {

  data[, race_time:= (dS + dH*fun(grade))*flat_pace * 60 / 1000,]

}
