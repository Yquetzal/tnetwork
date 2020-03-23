


function [CA, CR, CP, CF, CNMI] = computePerformance(Z,GT_Cube);


% This function, written by Yu-Ru Lin, has been modified to include also the computation of
% Normalized Mutual Information


%
% Input:
%   Z is the cluster membership matrix, 
%   GT_Cube is the ground truth over time
%   for each timestamp, each element is a couple (node,classlabel)
%
% Output:
%   CA: accuracy
%   CR: recall
%   CP: precision
%   CF: F1 score
%   CNMI: Normalized Mutual Information
nbCluster = size(GT_Cube{1},2); %
nodeSize = size(Z,1); %number of nodes
nbTime = size(Z,2); %number of timestamps

CA = zeros(nbTime,1);
CR = zeros(nbTime,1);
CP = zeros(nbTime,1);
CF = zeros(nbTime,1);
for i = 1:1:nbTime   
    t1 = zeros(nodeSize, nbCluster);
    for j = 1:1:nbCluster
        t1(find(Z(:,i)==j),j) = 1;
    end
    GTT = GT_Cube{i};
    CA(i,1) = trace((GTT*GTT'-t1*t1')'*(GTT*GTT'-t1*t1'));
    t1 = t1*(1:nbCluster)';
    GTT = GTT*(1:nbCluster)'; %is a vector in which at position i there is the true class
    %of node i
    [cr, cp, cf] = infoeval(GTT,t1);
    CR(i,1) = cr;
    CP(i,1) = cp;
    CF(i,1) = cf;
    
    %nbClusterF=size(unique(Z(:,i)),1) %number of clusters found
    nbClusterF=max(Z(:,i));
    truenbClusterF=size(unique(Z(:,i)),1);  %actual number of clusters found 
    CM = zeros(nbCluster,nbClusterF);
    
    truenodeSize=0;
    for j = 1: nodeSize
         if(GTT(j) ~=0)
             truenodeSize=truenodeSize+1;
             if (Z(j,i)~=0) 
               CM(GTT(j),Z(j,i))=  CM(GTT(j),Z(j,i))+1;
             end
         end
         
    end
   
    
    NMI=computeNMI(CM,truenodeSize);
    CNMI(i,1)=NMI;
end
%CNMI
end


% INFOEVAL 	Informative Evaluation of Clustering
%
% USAGE 
%		[R,P,F] = infoeval(B,C)
%
%	INPUT
%               B: true labels
%               C: clustering labels
%
%	OUTPUT
%		R: informative recall
%		P: informative precision
%		F: informative F1
%
%   Author: Shenghuo Zhu <zsh@acm.org>

function [R,P,F]=infoeval(B,C)
hB=entropy(B(:));
hC=entropy(C(:));
h=entropy([B(:),C(:)]);
ii=(hB+hC-h);
R=ii/hB;
P=ii/hC;
F=ii*2/(hB+hC);
end


% ENTROPY 	Entropy
%
% USAGE 
%		h = entropy(X)
%
%	INPUT
%		X: the distribution
%
%	OUTPUT
%		h: entropy
%
%   Author: Shenghuo Zhu <zsh@sv.nec-labs.com>

function h=entropy(X)
[B,I,J]=unique(X,'rows');
C=accumarray(J,ones(size(J)));
C=C./sum(C(:));
h=-(C'*log(C));
end
