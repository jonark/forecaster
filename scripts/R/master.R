source("scripts/funcs.R")

file_name <- list.files(pattern = ".gpx$")[1]
if (is.na(file_name)) {
  cat("Failed to find gpx file in forecaster directory.\n")
  return (data.table())
}

original_data <- load_GPX(file_name)
if (nrow(data) == 0) {
  #q() # quit R
}

data <- calculate_diffs(original_data)
plot(data$dist, data$grade)
