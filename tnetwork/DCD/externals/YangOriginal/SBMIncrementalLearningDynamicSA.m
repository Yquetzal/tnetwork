function net=SBMIncrementalLearingDynamicSA(graph,K,net)
% SBM Incremental Learning using Simulated Annealing 
% this is a generalized version of SBMIncrementalLearningSA which allows
% for nodes ding out and emerging again
% usage: Z=SBMIncrementalLearningDynamicSA(graph,K,net)
%  graph a structure has the following fields
%      W: the adjacency matrix or observed links at the current time 
%      n:  the number of nodes
%      Index: the index subset of {1 ,2 ,... ,un} of current nodes  global index
%  K: the number of clusters
% net is a structure and has the following fileds
%  net.type: the type of the graph, 'binary' 'coocc' 'simi'
% net.wthrehold the w threshold for similarity graph
%  net.para: the hyperparameters
%  net.Temp the tempature sequence for simulated annealing 
%  net.N: the number of iterations for simulated annealing   length of Temp must be equal to the lenght of N
%  net.Z: the cluster lable at previous time and the initial label at the current time for this version net.Z{1}=[nodesid clusterid]; net.Z{2}=[nodeid clusterid]
%  net.verbosity the level of ouput  0 nooutput, 1 output
%  net.objfunc the final value of objective function
%  Temp=1:-0.01:0 N=[20*ones(1,20) 10*ones(1,40) 5*ones(1,40) 5]  
%  Temp=1:-0.1:0    N=[20*ones(1,2) 10*ones(1,5) 5*ones(1,4)]
if nargin<3
    help SBMIncrementalLearingDynamicSA
end

W=graph.W;
Index=graph.Index;
n=graph.n;

if issymmetric(W) && sum(diag(W))~=0
    W=W-diag(diag(W)); 
end
    
if isempty(net.Z)
    net=SBMStaticPartitionSA(graph,K,net);% 
    Z=net.Z;
    net=rmfield(net,'Z');
    net.Z{1}=[Index Z];
    return;
elseif size(net.Z,2)==1 || isempty(net.Z{2})
    Z{1}=[net.Z{1}(:,1) net.Z{1}(:,2)];
    [tf loc]=ismember(Index,net.Z{1}(:,1));
    for i=1:length(tf)
        if tf(i)==1
            Z{2}(i,:)=[Index(i) net.Z{1}(loc(i),2)];
        else
            Z{2}(i,:)=[Index(i) randsample(K,1,false)];
        end
    end
elseif size(net.Z{2},1)~=n
    error('wrong initialization at current time');
elseif length(find(net.Z{2}(:,1)~=Index))>0
    erro('wrong initilization at current time');
end
    


if issymmetric(W)
   W=formatizeW(W);
end


if isempty(net.type)
    error('you must specify the type of your W: binary coocc simi');
else
    type=net.type;
end

if isempty(net.wthreshold)&& strcmp(net.type,'simi')
    wthreshold=[0.3 0.7];
    net.wthrehold=[0.3 0.7];
else
    wthreshold=net.wthreshold;
end

if isempty(net.paraP)
    paraP=[1 4 2];
    net.paraP=[1 4 2];
else
    paraP=net.paraP;
end

if isempty(net.paraA)
    paraA=[1 2];
    net.paraA=[1 2];
else
    paraA=net.paraA;
end

if isempty(net.Temp) || isempty(net.N)
    Temp=[0];
     N=[100];
     net.Temp=Temp;
     net.N=N;
elseif length(net.Temp)~=length(net.N)
    error('length of Temp is not equal to N');
else
    Temp=net.Temp;
    N=net.N;
end


if isempty(net.verbosity)
    verbosity=1;
    net.verbosity=1;
else
    verbosity=net.verbosity;
end

if strcmp(type, 'simi')
   %PW=sparse(ones(n,n).*(W>=(wthreshold(2).*ones(n,n,T))));
   %NW=sparse(ones(n,n).*(W<=(wthreshold(1).*ones(n,n,T))));
   %MW=sparse((ones(n,n)-PW-NW));
   %NW=[];
   %MW=[];
elseif strcmp(type,'binary')
    PW=W;
    NW=[];
    MW=[];
else
    PW=W;
    NW=[];
    MW=[];
end

%% Define the parameters matrices
ga=ones(1,K);
A=paraP(1)*ones(K,K)+paraP(2)*eye(K);%\alpha
B=paraP(3)*ones(K,K);
M=paraA(1).*ones(K,K)+paraA(2).*eye(K);
MS=sum(M,2);

%% compute the initial quantities
PWStateState=zeros(K,K);
NWStateState=zeros(K,K);
MWStateState=zeros(K,K);
StateState=zeros(K,K);
SelfStateState=zeros(K,K);


%% StateNumAtCurrentTime
I=[1:n]';
J=Z{2}(:,2);
S=ones(n,1);
ZM=sparse(I,J,S,n,K);
StateNumAtCurrentTime=sum(full(ZM),1);

%% PWStateState
    I=PW(:,1);
    J=PW(:,2);
    Count=PW(:,3);
    for k=1:length(I)
        i=I(k);
        j=J(k);
        wij=Count(k);
        row=Z{2}(i,2);
        col=Z{2}(j,2);
        PWStateState(row,col)=PWStateState(row,col)+wij;
        PWStateState(col,row)=PWStateState(col,row)+wij;
    end

%% SelfStateState and StateState

for i=1:n
     row=Z{2}(i,2);
     SelfStateState(row,row)=SelfStateState(row,row)+1;
end

StateState=StateNumAtCurrentTime'*StateNumAtCurrentTime-SelfStateState;

%% NWStateState MWStateState
if strcmp(type, 'coocc')
    NWStateState=StateState;
end
if strcmp(type, 'binary')
   NWStateState=StateState-PWStateState;
end

if strcmp(type, 'simi')
    I=NW(:,1);
    J=NW(:,2);
    Count=NW(:,3);
    for k=1:length(I)
        i=I(k);
        j=J(k);
        wij=Count(k);
        row=Z(i,t);
        col=Z(j,t);
        NWStateState(row,col)=NWStateState(row,col)+wij;
        NWStateState(col,row)=NWStateState(col,row)+wij;
    end
    MWStateState=StateState-PWStateState-NWStateState;
end


StateToState=zeros(K,K);
StateToAll=zeros(K,1);
for i=1:n
  gi=Z{2}(i,1);
  lip=find(Z{1}(:,1)==gi);% local index at previous time
  if isempty(lip)==0
       s1=Z{1}(lip,2);% state1
       s2=Z{2}(i,2);%state2
       StateToState(s1,s2)=StateToState(s1,s2)+1;
       StateToAll(s1,1)=StateToAll(s1,1)+1;
  end
end


%% iteration
change=n;
for Tk=1:length(Temp)
    Tep=Temp(Tk);
    for it=1:N(Tk)
        change=n;        
                P=randperm(n);
                P=1:n;
                for j=1:n
                   i=P(j);
                   ok=Z{2}(i,2);
                   NewStateNumAtCT=zeros(K,K);
                   NewPWStateState=zeros(K,K,K);
                   NewNWStateState=zeros(K,K,K);
                   NewMWStateState=zeros(K,K,K);
                   NewSelfStateState=zeros(K,K,K);
                   NewStateState=zeros(K,K,K);
                   NewStateToState=zeros(K,K,K);
                   NewStateToAll=zeros(K,K);
                   m=-inf;
                   shifK=[];
                   for k=1:K
                        CondPro=zeros(1,K);
                         newk=k;                   
                        [NewStateNumAtCurrentTime(k,:) NewPWStateState(:,:,k)  NewNWStateState(:,:,k)  NewMWStateState(:,:,k)  NewStateState(:,:,k)  NewSelfStateState(:,:,k)   NewStateToState(:,:,k)  NewStateToAll(:,k)]=update(StateNumAtCurrentTime, PWStateState, NWStateState,MWStateState, StateState,SelfStateState,StateToState,StateToAll, i,newk,Z,PW,NW,MW,n,K,type);
                        PWSD=(1/2).*diag(NewPWStateState(:,:,k));
                        NWSD=(1/2).*diag(NewNWStateState(:,:,k));
                        MWSD=(1/2).*diag(NewMWStateState(:,:,k));
                        PWS=NewPWStateState(:,:,k)-diag(diag(NewPWStateState(:,:,k)))+diag(PWSD);
                        NWS=NewNWStateState(:,:,k)-diag(diag(NewNWStateState(:,:,k)))+diag(NWSD);
                        MWS=NewMWStateState(:,:,k)-diag(diag(NewMWStateState(:,:,k)))+diag(MWSD);
                        if strcmp(type,'simi')
                           PWS=2.*PWS;
                           PWSD=2.*PWSD;
                           NWS=2.*NWS;
                           NWSD=2.*NWSD;
                        end
                        o=sum(sum(gammaln(NewStateToState(:,:,k)+M)))-sum(gammaln(NewStateToAll(:,k)+MS))+(sum(sum(betaln(PWS+MWS+A, NWS+MWS+B)))+sum(betaln(PWSD+MWSD+diag(A), NWSD+MWSD+diag(B))))/2;%gammaln(NewWStateState+A)+gammaln(NewNWStateState+B)-gammaln(NewWStateState+NewNWStateState+A+B)));
                        if o==inf
                            disp('error');
                        end
                        if o>m
                            if Tep~=0
                                for pk=1:k-1
                                    shifK(pk)=shifK(pk)*exp((m-o)/Tep);
                                end                 
                                shifK(k)=exp((o-o)/Tep);
                            else
                                for pk=1:k-1
                                    shifK(pk)=0;
                                end
                                shifK(k)=1;
                            end
                            m=o;
                        else
                            if Tep~=0
                                shifK(k)=exp((o-m)/Tep);
                            else
                                shifK(k)=0;
                            end
                        end
                   end
                   maxPro=1./sum(shifK);
                   CondPro=shifK.*maxPro;

        %% Gibbs Sampling
                     if Tep~=0
                            NormCondPro=CondPro./sum(CondPro);
                            NormCondPro_Cum=cumsum(NormCondPro);
                            SampPro=rand(1);
                            NewZ=zeros(1,K);
                            NormCondPro_Cum=[0 NormCondPro_Cum];
                            for ki=2:(K+1)
                                if SampPro>NormCondPro_Cum(ki-1) && SampPro<=NormCondPro_Cum(ki)
                                    NewZ(ki-1)=1;
                                end
                            end
                            if length(find(NewZ==1))~=1
                                disp('error'); 
                            end
                            newk=find(NewZ);
                            if newk==ok
                                change=change-1;
                          else
                                %% update
                                Z{2}(i,2)=newk;
                                StateNumAtCurrentTime=NewStateNumAtCurrentTime(newk,:);
                                PWStateState=NewPWStateState(:,:,newk);
                                NWStateState=NewNWStateState(:,:,newk);
                                MWStateState=NewMWStateState(:,:,newk);
                                StateState=NewStateState(:,:,newk);
                                SelfStateState=NewSelfStateState(:,:,newk);
                                StateToState=NewStateToState(:,:,newk);
                                StateToAll=NewStateToAll(:,newk);
                             end
        %% ICM  
                     else
                            MaxCondPro=max(CondPro);
                            I=find(CondPro==MaxCondPro);
                            if length(I)>1
                                p=randperm(length(I));
                                newk=I(p(1));
                            else
                                newk=I;
                            end
                            NewZ=zeros(1,K);
                            NewZ(newk)=1;
                            if newk==ok
                                change=change-1;
                            else
                                %% update
                                Z{2}(i,2)=newk;
                                StateNumAtCurrentTime=NewStateNumAtCurrentTime(newk,:);
                                PWStateState=NewPWStateState(:,:,newk);
                                NWStateState=NewNWStateState(:,:,newk);
                                MWStateState=NewMWStateState(:,:,newk);
                                StateState=NewStateState(:,:,newk);
                                SelfStateState=NewSelfStateState(:,:,newk);
                                StateToState=NewStateToState(:,:,newk);
                                StateToAll=NewStateToAll(:,newk);
                            end
                     end% endif
                end% end all members
        if verbosity==1
            Temp_iteration=[Tep it]
            m
        end
    end% end one iteration
end% end all tempature
net.objfun=o;
net.Z=Z;

function [NewStateNumAtCurrentTime NewPWStateState NewNWStateState NewMWStateState NewStateState NewSelfStateState NewStateToState NewStateToAll]=update(StateNumAtCurrentTime, PWStateState, NWStateState,MWStateState,StateState,SelfStateState,StateToState, StateToAll, i, newk, Z,PW,NW,MW, n,K,type)

t=2;
ok=Z{t}(i,2);
if newk==ok
   NewStateNumAtCurrentTime=StateNumAtCurrentTime;
   NewPWStateState=PWStateState;
   NewNWStateState=NWStateState;
   NewMWStateState=MWStateState;
   NewStateState=StateState;
   NewSelfStateState=SelfStateState;
   NewStateToState=StateToState;
   NewStateToAll=StateToAll;
else
   NewStateNumAtCurrentTime=StateNumAtCurrentTime;
   NewStateNumAtCurrentTime(ok)=NewStateNumAtCurrentTime(ok)-1;
   NewStateNumAtCurrentTime(newk)=NewStateNumAtCurrentTime(newk)+1;
   NewPWStateState=PWStateState;
   NewNWStateState=zeros(K,K);
   NewMWStateState=zeros(K,K);
   

   WACT=sparse(PW(:,1), PW(:,2), PW(:,3),n,n);% WAtCurrentTime
   WACT=WACT+WACT';
   J=find(WACT(i,:));
   for k=1:length(J)
           j=J(k);
           kj=Z{t}(j,2);
           wij=WACT(i,j);
           NewPWStateState(ok,kj)=NewPWStateState(ok,kj)-wij;
           NewPWStateState(kj,ok)=NewPWStateState(kj,ok)-wij;
           NewPWStateState(newk,kj)=NewPWStateState(newk,kj)+wij;
           NewPWStateState(kj,newk)=NewPWStateState(kj,newk)+wij;   
   end
 
   
   NewSelfStateState=SelfStateState;
   NewSelfStateState(ok,ok)=SelfStateState(ok,ok)-1;
   NewSelfStateState(newk,newk)=SelfStateState(newk,newk)+1;

   
   NewStateState=NewStateNumAtCurrentTime'*NewStateNumAtCurrentTime-NewSelfStateState;
   
   if strcmp(type, 'coocc')
       NewNWStateState=NewStateState;
 
   elseif strcmp(type, 'binary')
      NewNWStateState=NewStateState-NewPWStateState; 
   
   elseif strcmp(type, 'simi')
       WACT=sparse(NW(:,1), NW(:,2), NW(:,3));% WAtCurrentTime
       WACT=WACT+WACT';
       J=find(WACT(i,:));
       for k=1:length(J)
               j=J(k);
               kj=Z{t}(j,2);
               wij=WACT(i,j);
               NewNWStateState(ok,kj)=NewNWStateState(ok,kj)-wij;
               NewNWStateState(kj,ok)=NewNWStateState(kj,ok)-wij;
               NewNWStateState(newk,kj)=NewNWStateState(newk,kj)+wij;
               NewNWStateState(kj,newk)=NewNWStateState(kj,newk)+wij;   
       end
       NewMWStateState=NewStateState-NewPWStateState-NewNWStateState;
   end
   
    NewStateToState=StateToState;
    NewStateToAll=StateToAll;
    
    gi=Z{t}(i,1);
    lpi=find(Z{t-1}(:,1)==gi);
    if isempty(lpi)==0
       pki=Z{t-1}(lpi,2);
       NewStateToState(pki,ok)=NewStateToState(pki,ok)-1;
       NewStateToState(pki,newk)=NewStateToState(pki,newk)+1;
    end
end

if length(find(NewStateNumAtCurrentTime<0))>0
    disp('error at line 420');
elseif length(find(NewPWStateState<0))>0
    disp('error at line 422');
elseif length(find(NewNWStateState<0))>0
    disp('error at line 424');
elseif length(find(NewMWStateState<0))>0
    disp('error at line 426');
elseif length(find(NewSelfStateState<0))>0
    disp('error at line 428');
elseif length(find(NewStateState<0))>0
    disp('error at line 430');
elseif length(find(NewStateToState<0))>0
    disp('error at line 432');
elseif length(find(NewStateToAll<0))>0
    disp('error at line 434');
end

%%
function WF=formatizeW(W)
% a form for W each row corresponds to a link at a time : node_i node_j  wij  time
T=size(W,3);
n=size(W,2);

link=1;
for t=1:T
    for i=1:n
        for j=(i+1):n
            if W(i,j,t)~=0
                WF(link,:)=[i j W(i,j,t) t];
                link=link+1;
            end
        end
    end
end