#!/usr/bin/env Rscript

# Direct single-date calibration helper. This deliberately does not call Bacon;
# it evaluates a Gaussian measurement likelihood against an official
# three-column calibration curve supplied by rintcal.

script_arg <- commandArgs(trailingOnly = FALSE)[grep("^--file=", commandArgs(trailingOnly = FALSE))]
if (length(script_arg) != 1L) stop("Run this file with Rscript")
out_dir <- dirname(normalizePath(sub("^--file=", "", script_arg)))

curve_path <- function(name) {
  path <- system.file(paste0("extdata/3Col_", name, ".14C"), package = "rintcal")
  if (!nzchar(path)) stop("Calibration curve not found: ", name)
  path
}

calibrate_direct <- function(curve, determination, determination_sd, delta_r = 0, delta_r_sd = 0) {
  x <- read.table(curve_path(curve), col.names = c("cal_BP", "curve_14C_BP", "curve_sd_yr"))
  combined_sd <- sqrt(determination_sd^2 + delta_r_sd^2 + x$curve_sd_yr^2)
  likelihood <- dnorm(determination, mean = x$curve_14C_BP + delta_r, sd = combined_sd)
  probability <- likelihood / sum(likelihood)
  cdf <- cumsum(probability)
  quant <- function(p) x$cal_BP[which(cdf >= p)[1]]
  list(
    distribution = transform(x, combined_sd_yr = combined_sd, probability = probability),
    summary = data.frame(
      curve = curve,
      determination_14C_BP = determination,
      determination_sd_yr = determination_sd,
      delta_R_yr = delta_r,
      delta_R_sd_yr = delta_r_sd,
      median_cal_BP = quant(0.5),
      ci_lower_95_cal_BP = quant(0.025),
      ci_upper_95_cal_BP = quant(0.975),
      mean_cal_BP = sum(x$cal_BP * probability),
      mode_cal_BP = x$cal_BP[which.max(probability)],
      stringsAsFactors = FALSE
    )
  )
}

# PUBLIC CODE-ONLY RELEASE NOTE
# Historical project-specific calibration invocations and output filenames were
# removed here because they embedded record-level measurement values. The
# reusable calibrate_direct() implementation above is unchanged. Supply
# authorized inputs explicitly in a separate driver script.
