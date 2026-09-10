stageb_set_lib <- function(local_lib) {
  .libPaths(c(normalizePath(local_lib,mustWork=TRUE),.libPaths()))
  suppressPackageStartupMessages(library(posterior))
  suppressPackageStartupMessages(library(diptest))
}

stageb_convergence <- function(age_array) {
  stopifnot(length(dim(age_array))==3L,dim(age_array)[2]==4L,dim(age_array)[3]==201L)
  ndepth <- dim(age_array)[3]
  ans <- vector("list",ndepth)
  for(d in seq_len(ndepth)) {
    x <- age_array[,,d,drop=FALSE][,,1]
    stopifnot(nrow(x)==dim(age_array)[1],ncol(x)==4L,all(is.finite(x)))
    ans[[d]] <- data.frame(depth_index=d,rhat=posterior::rhat(x),
      bulk_ESS=posterior::ess_bulk(x),tail_ESS=posterior::ess_tail(x))
  }
  out <- do.call(rbind,ans)
  out$convergence_pass <- out$rhat<1.01 & out$bulk_ESS>=400 & out$tail_ESS>=400
  stopifnot(nrow(out)==201L,all(is.finite(as.matrix(out[,2:4]))))
  out
}

balanced_draw_provenance <- function(n_retained) {
  stopifnot(n_retained>=100L)
  idx <- as.integer(round(seq(1,n_retained,length.out=100L)))
  stopifnot(length(idx)==100L,length(unique(idx))==100L,all(diff(idx)>0))
  do.call(rbind,lapply(1:4,function(ch)data.frame(chain_id=ch,retained_iteration_index=idx,
    merged_draw_index=(ch-1L)*100L+seq_len(100L))))
}

stageb_unimodality <- function(age_array,depth_values) {
  stopifnot(length(dim(age_array))==3L,dim(age_array)[2]==4L,dim(age_array)[3]==201L,
            length(depth_values)==201L)
  prov <- balanced_draw_provenance(dim(age_array)[1])
  rows <- vector("list",201L)
  for(d in 1:201) {
    vals <- age_array[cbind(prov$retained_iteration_index,prov$chain_id,rep(d,400L))]
    stopifnot(length(vals)==400L,all(is.finite(vals)))
    a <- diptest::dip.test(vals,simulate.p.value=FALSE)
    rows[[d]] <- data.frame(depth_index=d,depth_cm=depth_values[d],dip_statistic=unname(a$statistic),raw_p_value=a$p.value)
  }
  out <- do.call(rbind,rows);out$holm_p_value<-p.adjust(out$raw_p_value,method="holm")
  out$reject_unimodality <- out$holm_p_value<0.05
  stopifnot(nrow(out)==201L,!anyNA(out),identical(out$depth_index,1:201))
  list(by_depth=out,draw_provenance=prov)
}
