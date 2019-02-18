function [Modu Ncut MutInf]=evalClustering(W,K,Z,realZ)
%% W adjacent matrix
%% K number of cluters
%% Z returned community label
%% realZ real label
%% Modu modularity
%% Ncut
%% MutInf

Modu=[];
Ncut=[];
MutInf=[];
n=size(W,1);

if size(Z,2)==1
    if isempty(realZ)==0
      [R  P MutInf]=infoeval(Z,realZ);
    end
    I=[1:n]';
    J=Z;
    Z=sparse(I,J, ones(n,1), n,K);
end
Modu=0;
AllSimi=sum(sum(W));

Ncut=0;
for k=1:K
    I=find(Z(:,k));
    J=find(Z(:,k)==0);
    CW=W(I,I);
    BW=W(I,:);
    DW=W(I,J);
    InCSimi=sum(sum(CW));
    BeCSimi=sum(sum(BW));
    Modu=Modu+(InCSimi/AllSimi-(BeCSimi/AllSimi)^2);
    
    volC=sum(sum(BW));
    cutC=sum(sum(DW));
    Ncut=Ncut+cutC/volC;
end

