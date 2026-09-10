args<-commandArgs(trailingOnly=TRUE)
if(length(args)!=9)stop("args: local_lib diag.R output_dir thick dmin dmax depth_start depth_end out1;out2;out3;out4")
local_lib<-args[1];source(args[2]);stageb_set_lib(local_lib);od<-args[3]
thick<-as.numeric(args[4]);dmin<-as.numeric(args[5]);dmax<-as.numeric(args[6])
depths<-seq(as.numeric(args[7]),as.numeric(args[8]),length.out=201)
outs<-strsplit(args[9],";",fixed=TRUE)[[1]];stopifnot(length(outs)==4)
xs<-lapply(outs,read.table,header=FALSE);stopifnot(length(unique(vapply(xs,nrow,integer(1))))==1)
n<-nrow(xs[[1]]); elbows_files<-sub("\\.out$","_actual_elbows.csv",outs)
elbows<-lapply(elbows_files,function(p)read.csv(p)$depth_cm)
K<-ncol(xs[[1]])-3L;stopifnot(all(vapply(xs,ncol,integer(1))==ncol(xs[[1]])),all(vapply(elbows,length,integer(1))==K))
stopifnot(max(vapply(elbows,function(e)max(abs(e-elbows[[1]])),numeric(1)))<1e-10)
e<-elbows[[1]]; arr<-array(NA_real_,dim=c(n,4L,201L)); structural<-TRUE
for(ch in 1:4){
 x<-xs[[ch]];rates<-as.matrix(x[,2L:(K+1L),drop=FALSE]);cumrates<-t(apply(rates,1,cumsum));prev<-NULL
 for(ii in 1:201){
  d<-depths[ii];sec<-max(which(e<=d));before<-if(sec==1L)0 else cumrates[,sec-1L]
  a<-x[,1L]+thick*before+(d-e[sec])*rates[,sec];arr[,ch,ii]<-a
  if(!is.null(prev)&&any(a<prev-1e-8))structural<-FALSE
  prev<-a
 }
}
if(!structural)stop("structural_integrity_assertion failed")
cv<-stageb_convergence(arr);cv$depth_cm<-depths
write.csv(cv,file.path(od,"stageB_convergence_by_depth.csv"),row.names=FALSE)
conv<-all(cv$convergence_pass)
um_status<-"not_evaluated";um_reject<-NA
if(conv){
 um<-stageb_unimodality(arr,depths);write.csv(um$by_depth,file.path(od,"stageB_unimodality_by_depth.csv"),row.names=FALSE)
 write.csv(um$draw_provenance,file.path(od,"stageB_400_draw_provenance.csv"),row.names=FALSE)
 um_reject<-any(um$by_depth$reject_unimodality);um_status<-if(um_reject)"holm_rejection_present" else "no_holm_rejection"
}
ages<-vector("list",201)
for(ii in 1:201){v<-c(arr[,,ii]);qq<-quantile(v,c(.025,.5,.975),names=FALSE);ages[[ii]]<-data.frame(depth_index=ii,depth_cm=depths[ii],ci_lower_95=qq[1],median_cal_BP=qq[2],ci_upper_95=qq[3],ci_width_95=qq[3]-qq[1])}
ages<-do.call(rbind,ages);write.csv(ages,file.path(od,"age_model_201_depths.csv"),row.names=FALSE)
summary<-data.frame(convergence_pass=conv,max_Rhat=max(cv$rhat),min_bulk_ESS=min(cv$bulk_ESS),min_tail_ESS=min(cv$tail_ESS),
 structural_integrity=structural,unimodality_status=um_status,unimodality_rejection=um_reject,
 CI_median_yr=median(ages$ci_width_95),CI_max_yr=max(ages$ci_width_95),iterations_per_chain=n,K=K)
write.csv(summary,file.path(od,"stageB_rung_summary.csv"),row.names=FALSE)
cat(sprintf("POSTPROCESS convergence=%s maxRhat=%.6f minBulk=%.1f minTail=%.1f\n",conv,summary$max_Rhat,summary$min_bulk_ESS,summary$min_tail_ESS))
