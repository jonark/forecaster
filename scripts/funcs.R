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
    select(-time) %>% 
    sapply(as.double) %>% 
    as.data.table()
    
  colnames(gpx) <- c('ele', 'lat', 'lon')
  gpx
}

find_diff <- function(gpx) {
  gpx[, c('ele_next', 'lat_next', 'lon_next'):= 
              list(lag(ele), lag(lat), lag(lon)),] %>% 
    na.omit(.) %>%
    .[, id:= .I,] %>% 
    .[, gain:= as.numeric(ele_next - ele), by = id] %>% 
    .[, dist:= geosphere::distGeo(c(lat, lon), c(lat_next, lon_next)),
      by = id] %>% 
    select(-ele_next, -lat_next, -lon_next)
}

