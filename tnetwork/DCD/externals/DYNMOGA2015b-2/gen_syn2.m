function [nbCluster,fname]= gen_syn2(T,z,nbChange,state,blogSize,avgDegree);
% gen_syn2.m
% to generate the synthetic data with 4 clusters,
% as described by Mark Newman's paper
%
%   inputs:
%       T: number of time steps, e.g., 10
%       z: average number of edges of a node connecting to other clusters,
%          e.g., 3, 6, 10
%       nbChange: number of nodes (divided by 3) that switch
%          membership at each time step, e.g., 1
%       state: initial state for random number generator
%       blogSize: number of nodes in each graph, e.g., 128
%       avgDegree: average degree of each node, e.g., 16
%
%    sample usage:   gen_syn2(10,z,1,100,256,32)
%

rand('state', state);
randn('state', state);

nbCluster = 4; %the number of clusters is fixed to 4
clusterSize = blogSize/4;

p_out = z/(blogSize*3/4)
p_in = (avgDegree/2 - p_out*3*clusterSize)/(clusterSize -1) %to guarantee
%avgDegree, i.e., p_in*(clusterSize-1)+p_out*(3*clusterSize)=avgDegree/2
if ( p_in < p_out )
    input('Warning: p_in < p_out! Are you sure?');
end

GT = zeros(blogSize,nbCluster);
for i = 1:1:nbCluster
    start_idx = (i-1)*clusterSize+1;
    end_idx = i*clusterSize;
    GT(start_idx:end_idx, i) = 1;
end

W = unifrnd(0,1,blogSize,blogSize);
W1 = W;
W2 = W;
WW1 = zeros(blogSize,blogSize);
WW2 = zeros(blogSize,blogSize);
WW1(W1 <= p_in) = 1;
WW2(W2 <= p_out) = 1;
W = WW2;
for i = 1:1:nbCluster
    start_idx = (i-1)*clusterSize+1;
    end_idx = i*clusterSize;
    W(start_idx:end_idx,start_idx:end_idx) = WW1(start_idx:end_idx,start_idx:end_idx);
end

W = W+W';
W(W>0)=1;
for i = 1:1:blogSize
    W(i,i) = 0;
end

W_Cube{1} = W;
GT_Cube{1} = GT;
c=zeros(clusterSize,4);
for i = 1:1:nbCluster
    start_idx = (i-1)*clusterSize+1;
    end_idx = i*clusterSize;
    cc(:,i) = start_idx:end_idx;
end

for kk=2:1:T

    W = unifrnd(0,1,blogSize,blogSize);
    W1 = W;
    W2 = W;
    WW1 = zeros(blogSize,blogSize);
    WW2 = zeros(blogSize,blogSize);
    WW1(W1 <= p_in) = 1;
    WW2(W2 <= p_out) = 1;
    W = WW2;
    for i = 1:1:nbCluster
        start_idx = (i-1)*clusterSize+1;
        end_idx = i*clusterSize;
        W(start_idx:end_idx,start_idx:end_idx) = WW1(start_idx:end_idx,start_idx:end_idx);
    end

    W = W+W';
    W(W>0)=1;
    for i = 1:1:blogSize
        W(i,i) = 0;
    end

    cc(:,1) = cc(randperm(clusterSize),1);
    cc(:,2) = cc(randperm(clusterSize),2);
    cc(:,3) = cc(randperm(clusterSize),3);
    cc(:,4) = cc(randperm(clusterSize),4);

    i = 1;
    cc(i:(i+nbChange-1),[2 3 4 1]') = cc(i:(i+nbChange-1),[1 2 3 4]');
    i = i+nbChange;
    cc(i:(i+nbChange-1),[3 4 1 2]') = cc(i:(i+nbChange-1),[1 2 3 4]');
    i = i+nbChange;
    cc(i:(i+nbChange-1),[4 1 2 3]') = cc(i:(i+nbChange-1),[1 2 3 4]');

    GT = zeros(blogSize,nbCluster);
    GT(cc(:,1),1) = 1;
    GT(cc(:,2),2) = 1;
    GT(cc(:,3),3) = 1;
    GT(cc(:,4),4) = 1;

    W([cc(:,1); cc(:,2); cc(:,3); cc(:,4)],:) = W;
    W(:,[cc(:,1); cc(:,2); cc(:,3); cc(:,4)]) = W;

    W_Cube{kk} = W;
    GT_Cube{kk} = GT;
end

GT_Matrix = zeros(blogSize, T);
for i=1:1:T
    GT_Matrix(:,i) = GT_Cube{i}*[1 2 3 4]';
end
%GT_Matrix
spy(W_Cube{1})
fname = ['syn_T_' int2str(T) '_z_' int2str(z) '_nC_' int2str(nbChange) '_bS_' int2str(blogSize) '_aD_' int2str(avgDegree) '.mat'];

eval(['save ' fname  ' W_Cube GT_Cube GT_Matrix blogSize nbCluster T z nbChange blogSize avgDegree -mat']);