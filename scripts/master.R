source("scripts/funcs.R")

original_data <- load_GPX()
if (nrow(data) == 0) {
  q() # quit R
}

data <- calculate_diffs(original_data)
plot(data$dist, data$gain)

# smooth elevation before finding other stats, remove outliers, find grade