function [Modu NCut MutInf TAC]=evalClusteringDynamic(SocNet,K,Z,realZ)

Modu=[];
NCut=[];
MutInf=[];
TAC=[];
T=SocNet.T;
if iscell(Z)
    for t=1:T
        Wt=SocNet.cellW{t};
        if isempty(realZ)==0 && iscell(realZ)
           [Modu(t) NCut(t) MutInf(t)]=evalClustering(Wt,K,Z{t}(:,2),realZ{t}(:,2));
        elseif isempty(realZ)==0 && iscell(realZ)==0
            [Modu(t) NCut(t) MutInf(t)]=evalClustering(Wt,K,Z{t}(:,2),realZ(:,t));
        else
            [Modu(t) NCut(t)]=evalClustering(Wt,K,Z{t}(:,2),[]);
        end
    end
  
elseif iscell(Z)==0
    for t=1:T
         Zt=Z(:,t);
         Wt=SocNet.W(:,:,t);
        if isempty(realZ)==0
           [Modu(t) NCut(t) MutInf(t)]=evalClustering(Wt,K,Z(:,t),realZ(:,t));
        else
            [Modu(t) NCut(t)]=evalClustering(Wt,K,Z(:,t),[]);
        end
    end
end

if iscell(Z) && iscell(realZ)
    Z=cellZ2Z(Z,SocNet.Index,SocNet.n,K,'nosample');
    realZ=cellZ2Z(realZ,SocNet.Index, SocNet.n, K,'nosample');
end

TAC=[];
if isempty(realZ)==0
if iscell(realZ)==0 && iscell(Z)==0
   for t=2:T
      CL=find(realZ(:,t)~=realZ(:,t-1));
      ECL=find(Z(:,t)~=Z(:,t-1));
      IL=intersect(CL, ECL);
     TAC(t-1,1)=length(IL)/length(ECL);
     TAC(t-1,2)=length(IL)/length(CL);
   end
end
TAC=mean(TAC,1);
end