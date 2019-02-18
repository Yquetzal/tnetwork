function net=SBMDynamicEvolutionOnline(SocNet,K,net)
% SBM Dynamic Evolution by incremental learing using Simulated Annealing 
% usage: net=SBMDynamicEvolutionOnline(SocNet,K,net)
% SocNet is a structure has the following fields
%        W the adjacent matrix of observed links at all time
%        n  the number of nodes at all time step
%        T  the number of time steps
%        cellW  the cell W at each time step for corresponding to Index
%        Index  Index{t} the nodes appeared at time t
%  K: the number of clusters
% net is a structure and has the following fileds
%  net.type: the type of the graph, 'binary' 'coocc' 'simi'
% net.wthrehold the w threshold for similarity graph
%  net.para: the hyperparameters
%  net.Temp the tempature sequence for simulated annealing 
%  net.N: the number of iterations for simulated annealing   length of Temp must be equal to the lenght of N
%  net.Z: the initial assignment of the clusters which is n*T matrix, each  column is the cluster label at each time 
%  net.verbosity the level of ouput  0 nooutput, 1 output
%  net.objfunc the final value of objective function
%  example of net.Temp and net.N 
%  Temp=1:-0.01:0 N=[20*ones(1,20) 10*ones(1,40) 5*ones(1,40) 5]  
%  Temp=1:-0.01:0 N=[20*ones(1,20) 10*ones(1,40) 5*ones(1,40) 5]  
%  Temp=1:-0.1:0    N=[20*ones(1,2) 10*ones(1,5) 5*ones(1,4)]


T=SocNet.T;

if size(net.Z,2)>1
    net.Z=[];
end
Z=[];
for t=1:T
       disp(sprintf('Time=%d',t));
       Wt=SocNet.W(:,:,t);
       graph.W=Wt;
       graph.n=SocNet.n;
       net=SBMIncrementalLearningSA(graph,K,net);
       if t==1
          Z(:,t)=net.Z;
       else 
           Z(:,t)=net.Z(:,2);
           net.Z=net.Z(:,2);% the previous time for next time becomes the current time
       end
end
net.Z=Z;
net.learning='Online';