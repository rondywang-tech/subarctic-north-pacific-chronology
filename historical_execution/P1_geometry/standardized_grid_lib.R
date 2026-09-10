# Fixed-grid posterior age diagnostics for rbacon .out files.
# Correct layout: column 1 is the starting age, columns 2:(K+1) are rates,
# and K = ncol(.out)-3.

posterior_age_at_depth_from_elbows <- function(x, elbows, thick, depth) {
  K <- ncol(x)-3L
  stopifnot(length(elbows)==K, all(diff(elbows)>0), thick>0,
            depth>=min(elbows), depth<=max(elbows)+thick)
  section <- max(which(elbows <= depth))
  rates <- as.matrix(x[,2L:(K+1L),drop=FALSE])
  # Exact independent equivalent of rbacon 3.5.2 Bacon.Age.d.
  before <- if(section==1L) 0 else rowSums(rates[,seq_len(section-1L),drop=FALSE])
  x[,1L] + thick*before + (depth-elbows[section])*rates[,section]
}

standardized_age_grid <- function(out_file, elbows, thick, dated_min, dated_max, n_grid=201L) {
  stopifnot(n_grid >= 2L, thick > 0, dated_max > dated_min)
  x <- read.table(out_file, header=FALSE)
  K <- ncol(x)-3L
  if (K < 1L || K > 10000L) stop("invalid accumulation-section count")
  if (length(elbows)!=K) stop("actual elbow vector length does not equal .out K")
  depths <- seq(dated_min, dated_max, length.out=n_grid)
  target_section <- vapply(depths,function(d) max(which(elbows<=d)),integer(1))
  rows <- vector("list", length(depths))
  rates <- as.matrix(x[,2L:(K+1L),drop=FALSE])
  cumrates <- t(apply(rates,1,cumsum))
  for (ii in seq_along(depths)) {
    section <- target_section[ii]
    before <- if(section==1L) 0 else cumrates[,section-1L]
    a <- x[,1L] + thick*before +
      (depths[ii]-elbows[section])*rates[,section]
    q <- unname(quantile(a,c(.025,.5,.975),names=FALSE,type=7))
    rows[[ii]] <- data.frame(standardized_depth_index=ii,
      normalized_depth=(depths[ii]-dated_min)/(dated_max-dated_min),depth_cm=depths[ii],
      section_index=target_section[ii],median_cal_BP=q[2],ci_lower_95=q[1],
      ci_upper_95=q[3],ci_width_95=q[3]-q[1])
  }
  if (any(vapply(rows, is.null, logical(1)))) stop("unfilled standardized-grid row")
  list(grid=do.call(rbind, rows), K=K)
}
