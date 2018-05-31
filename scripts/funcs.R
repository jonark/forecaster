library(XML)
library(dplyr)
library(purrr)
library(data.table)

load_GPX <- function() {
  file_name <- list.files(pattern = ".gpx$")[1]
  if (is.na(file_name)) {
    cat("Failed to find gpx file in forecaster directory.\n")
    return (data.table())
  }

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
get_gap_matrix <- function(data) {
  
}