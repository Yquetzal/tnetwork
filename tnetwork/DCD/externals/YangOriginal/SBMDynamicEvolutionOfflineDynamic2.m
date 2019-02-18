function net=SBMDynamicEvolutionOfflineDynamic2(SocNet,K,net,Indexx)
% SBM Dynamic Evolution by simutaneous learning using Simulated Annealing 
% usage: net=SBMDynamicEvolutionOfflineDynamic(SocNet,K,net)
% SocNet is a structure has the following fields
%        W the adjacent matrix of observed links at all time
%        n  the number of nodes at all time step
%        T  the number of time steps
%        cellW  the cell W at each time step for corresponding to Index
%        Index  Index{t} the nodes appeared at time t
%  K: the number of clusters
%  net is a structure and has the following fileds
%  net.type: the type of the graph, 'binary' 'coocc' 'simi'
%  net.wthrehold the w threshold for similarity graph
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
%  Temp=[1 0] N=[10 5];
% this version is different from SBMDynamicEvolutionOfflineDynamic in that we implement the
% insertion and removal mentioned in the paper
if nargin<3
    help SBMDynamicEvolutionOfflineDyanmic
end

W=SocNet.W;
% Index=SocNet.Index;
Index = Indexx
if size(W,3)>1
    W=formatizeW(W);
end

n=SocNet.n;
T=SocNet.T;

net.learning='OfflineDynamic';
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

if isempty(net.Z)
  %% initialize the hidden variables by random guess
    C=rand(n, K);
    MaxC=repmat(max(C,[],2),1,K);
    C=(C>=MaxC);
    ZB=repmat(C.*ones(n,K),[1  1 T]);
    for t=1:T


        ZBt=ZB(Index{t},:,t);
        Z{t}(:,1)=Index{t};
        [I Z{t}(:,2)]=max(ZBt,[],2);
    end
    net.Z=Z;
elseif iscell(net.Z) 
    Z=net.Z;
else
    for t=1:T
        Z{t}=[Index{t} net.Z(Index{t},t)];
    end
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
    %NW=sparse(ones(n,n,T)-W);
    %MW=sparse(zeros(n,n,T));
    NW=[];
    MW=[];
else
    PW=W;
    %NW=sparse(ones(n,n,T));
    %MW=sparse(zeros(n,n,T));
    NW=[];
    MW=[];
end

%% Define the parameters matrices
ga=ones(1,K);
A=paraP(1)*ones(K,K)+paraP(2)*eye(K);%\alpha
B=paraP(3)*ones(K,K);
if T>1
    M=paraA(1).*ones(K,K)+paraA(2).*eye(K);
    MS=sum(M,2);
else 
    M=ones(K,K);
    MS=ones(K,1);
end

%% compute the initial quantities
PWStateState=zeros(K,K);
NWStateState=zeros(K,K);
MWStateState=zeros(K,K);
StateState=zeros(K,K);
SelfStateState=zeros(K,K);
AllStateState=zeros(K,K);
StateNumOfNewNodesAllTime=zeros(T,K);
%% StateNumAtTime
for t=1:T
       Ind=Index{t};
       I=[1:length(Ind)]';
       J=Z{t}(:,2);
       S=ones(length(Ind),1);
       ZM=sparse(I,J,S,n,K);
       StateNumAtTime(t,:)=sum(full(ZM),1);
       AllStateState=AllStateState+StateNumAtTime(t,:)'*StateNumAtTime(t,:);
       if t==1
           StateNumOfNewNodesAllTime(t,:)=StateNumOfNewNodesAllTime(t,:)+StateNumAtTime(t,:);
       else
           new_index=setdiff(Index{t}, Index{t-1}); %get nodes in this timestamp that are not in the previous ones
           I=[1:length(new_index)]';
           J=Z{t}(new_index,2);
           S=ones(length(new_index),1);

           ZM=sparse(I,J,S,n,K);
           StateNumOfNewNodesAllTime(t,:)=StateNumOfNewNodesAllTime(t,:)+sum(full(ZM),1);
       end
end

%% PWStateState
for t=1:T
    Edge=find(PW(:,4)==t);
    I=PW(Edge,1);
    J=PW(Edge,2);
    Count=PW(Edge,3);
    for k=1:length(I)
        i=I(k);
        j=J(k);
        wij=Count(k);
        i_loc=find(Index{t}==i);
        j_loc=find(Index{t}==j);
        row=Z{t}(i_loc,2);
        col=Z{t}(j_loc,2);
        PWStateState(row,col)=PWStateState(row,col)+wij;
        PWStateState(col,row)=PWStateState(col,row)+wij;
    end
end


%% SelfStateState and StateState
for t=1:T
    Ind=Index{t};
    for i_loc=1:length(Ind)
         row=Z{t}(i_loc,2);
         SelfStateState(row,row)=SelfStateState(row,row)+1;
    end
end

StateState=AllStateState-SelfStateState;

%% NWStateState MWStateState
if strcmp(type, 'coocc')
    NWStateState=StateState;

elseif strcmp(type, 'binary')
   NWStateState=StateState-PWStateState;

elseif strcmp(type, 'simi')
    Edge=find(NW(:,4)==t);
    I=NW(Edge,1);
    J=NW(Edge,2);
    Count=NW(Edge,3);
    for k=1:length(I)
        i=I(k);
        j=J(k);
        wij=Count(k);
        i_loc=find(Index{t}==i);
        j_loc=find(Index{t}==j);
        row=Z{t}(i_loc,2);
        col=Z{t}(j_loc,2);
        NWStateState(row,col)=NWStateState(row,col)+wij;
        NWStateState(col,row)=NWStateState(col,row)+wij;
    end
    MWStateState=StateState-PWStateState-NWStateState;
end

StateToState=zeros(K,K);
StateToAll=zeros(K,1);
for t=2:T
    for i=1:n
        if ismember(i, Index{t-1})
            i_loc=find(Index{t}==i);
            i_loc_pre=find(Index{t-1}==i);
            s1=Z{t-1}(i_loc_pre,2);% state1
            s2=Z{t}(i_loc,2);%state2
            StateToState(s1,s2)=StateToState(s1,s2)+1;
            StateToAll(s1,1)=StateToAll(s1,1)+1;
        end
    end
end


%% iteration
change=n;
for Tk=1:length(Temp)
    Tep=Temp(Tk);
    for it=1:N(Tk)
        change=n;        
        for t=1:T
                %P=randperm(n);
                P=randperm(length(Index{t}));
                for j=1:length(Index{t})
                   i_loc=P(j); % localindex at current time
                   ok=Z{t}(i_loc,2);
                   NewStateNumAtCurrentTime=zeros(K,K);
                   NewPWStateState=zeros(K,K,K);
                   NewNWStateState=zeros(K,K,K);
                   NewMWStateState=zeros(K,K,K);
                   NewSelfStateState=zeros(K,K,K);
                   NewAllStateState=zeros(K,K,K);
                   NewStateState=zeros(K,K,K);
                   NewStateToState=zeros(K,K,K);
                   NewStateToAll=zeros(K,K);
                   m=-inf;
                   shifK=[];
                   for k=1:K
                        CondPro=zeros(1,K);
                         newk=k;                   
                        [NewStateNumAtCurrentTime(k,:) NewStateNumOfNewNodesAtCurrentTime(k,:) NewPWStateState(:,:,k)  NewNWStateState(:,:,k)  NewMWStateState(:,:,k)  NewStateState(:,:,k)  NewSelfStateState(:,:,k)  NewAllStateState(:,:,k)  NewStateToState(:,:,k)  NewStateToAll(:,k)]=update(StateNumAtTime,StateNumOfNewNodesAllTime(t,:), PWStateState, NWStateState,MWStateState, StateState,SelfStateState,AllStateState,StateToState,StateToAll, i_loc,t,newk,Z,PW,NW,MW,n,K,T,type,Index);
                        PWSD=(1/2).*diag(NewPWStateState(:,:,k));
                        NWSD=(1/2).*diag(NewNWStateState(:,:,k));
                        MWSD=(1/2).*diag(NewMWStateState(:,:,k));
                        PWS=NewPWStateState(:,:,k)-diag(diag(NewPWStateState(:,:,k)))+diag(PWSD);
                        NWS=NewNWStateState(:,:,k)-diag(diag(NewNWStateState(:,:,k)))+diag(NWSD);
                        MWS=NewMWStateState(:,:,k)-diag(diag(NewMWStateState(:,:,k)))+diag(MWSD);
                        NewStateNumOfNewNodesAllTime=StateNumOfNewNodesAllTime;
                        NewStateNumOfNewNodesAllTime(t,:)=NewStateNumOfNewNodesAtCurrentTime(k,:);
                        if strcmp(type,'simi')
                           PWS=2.*PWS;
                           PWSD=2.*PWSD;
                           NWS=2.*NWS;
                           NWSD=2.*NWSD;
                        end
                        if t==1
                            NewStateNumAtOne=NewStateNumAtCurrentTime(k,:);
                        else
                            NewStateNumAtOne=StateNumAtTime(1,:);
                        end
                        o=sum(sum(gammaln(NewStateNumOfNewNodesAllTime+repmat(ga,T,1))))+sum(sum(gammaln(NewStateToState(:,:,k)+M)))-sum(gammaln(NewStateToAll(:,k)+MS))+(sum(sum(betaln(PWS+MWS+A, NWS+MWS+B)))+sum(betaln(PWSD+MWSD+diag(A), NWSD+MWSD+diag(B))))/2;%gammaln(NewWStateState+A)+gammaln(NewNWStateState+B)-gammaln(NewWStateState+NewNWStateState+A+B)));
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
                                Z{t}(i_loc,2)=newk;
                                StateNumAtTime(t,:)=NewStateNumAtCurrentTime(newk,:);
                                PWStateState=NewPWStateState(:,:,newk);
                                NWStateState=NewNWStateState(:,:,newk);
                                MWStateState=NewMWStateState(:,:,newk);
                                StateState=NewStateState(:,:,newk);
                                SelfStateState=NewSelfStateState(:,:,newk);
                                AllStateState=NewAllStateState(:,:,newk);
                                StateToState=NewStateToState(:,:,newk);
                                StateToAll=NewStateToAll(:,newk);
                                StateNumOfNewNodesAllTime(t,:)=NewStateNumOfNewNodesAtCurrentTime(newk,:);
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
                                Z{t}(i_loc,2)=newk;
                                StateNumAtTime(t,:)=NewStateNumAtCurrentTime(newk,:);
                                PWStateState=NewPWStateState(:,:,newk);
                                NWStateState=NewNWStateState(:,:,newk);
                                MWStateState=NewMWStateState(:,:,newk);
                                StateState=NewStateState(:,:,newk);
                                SelfStateState=NewSelfStateState(:,:,newk);
                                AllStateState=NewAllStateState(:,:,newk);
                                StateToState=NewStateToState(:,:,newk);
                                StateToAll=NewStateToAll(:,newk);
                                StateNumOfNewNodesAllTime(t,:)=NewStateNumOfNewNodesAtCurrentTime(newk,:);
                            end
                     end% endif
                end% end all members
        end% end all time steps
        if verbosity==1
            Temp_iteration=[Tep it]
            m
        end
    end% end one iteration
end% end all tempature
net.objfun=o;
net.Z=Z;

function [NewStateNumAtCurrentTime NewStateNumOfNewNodesAtCurrentTime NewPWStateState NewNWStateState NewMWStateState NewStateState NewSelfStateState NewAllStateState NewStateToState NewStateToAll]=update(StateNumAtTime, StateNumOfNewNodesAtCurrentTime, PWStateState, NWStateState,MWStateState,StateState,SelfStateState,AllStateState,StateToState, StateToAll, i_loc, t, newk, Z,PW,NW,MW, n,K,T,type,Index)
% i is the local index, change it to global index
i=Index{t}(i_loc);
ok=Z{t}(i_loc,2);

if newk==ok
   NewStateNumAtCurrentTime=StateNumAtTime(t,:);
   NewStateNumOfNewNodesAtCurrentTime=StateNumOfNewNodesAtCurrentTime;
   NewPWStateState=PWStateState;
   NewNWStateState=NWStateState;
   NewMWStateState=MWStateState;
   NewStateState=StateState;
   NewSelfStateState=SelfStateState;
   NewAllStateState=AllStateState;
   NewStateToState=StateToState;
   NewStateToAll=StateToAll;
else
   NewStateNumAtCurrentTime=StateNumAtTime(t,:);
   NewStateNumAtCurrentTime(ok)=NewStateNumAtCurrentTime(ok)-1;
   NewStateNumAtCurrentTime(newk)=NewStateNumAtCurrentTime(newk)+1;

   NewStateNumOfNewNodesAtCurrentTime=StateNumOfNewNodesAtCurrentTime;
   if t==1 || ismember(i, Index{t-1})==0
       NewStateNumOfNewNodesAtCurrentTime(ok)=NewStateNumOfNewNodesAtCurrentTime(ok)-1;
       NewStateNumOfNewNodesAtCurrentTime(newk)=NewStateNumOfNewNodesAtCurrentTime(newk)+1;
   end
   
   NewStateNumAtTime=StateNumAtTime;
   NewStateNumAtTime(t,:)=NewStateNumAtCurrentTime;
   NewPWStateState=PWStateState;
   NewNWStateState=zeros(K,K);
   NewMWStateState=zeros(K,K);
   
   EACT=find(PW(:,4)==t);% EdgeAtCurrentTime

   WACT=sparse(PW(EACT,1), PW(EACT,2), PW(EACT,3),n,n);% WAtCurrentTime
   WACT=WACT+WACT';
   J=find(WACT(i,:));
   for k=1:length(J)
           j=J(k);% j is th global index
           j_loc=find(Index{t}==j);
           kj=Z{t}(j_loc,2);
           wij=WACT(i,j);
           NewPWStateState(ok,kj)=NewPWStateState(ok,kj)-wij;
           NewPWStateState(kj,ok)=NewPWStateState(kj,ok)-wij;
           NewPWStateState(newk,kj)=NewPWStateState(newk,kj)+wij;
           NewPWStateState(kj,newk)=NewPWStateState(kj,newk)+wij;   
   end
 
   
   NewSelfStateState=SelfStateState;
   NewSelfStateState(ok,ok)=SelfStateState(ok,ok)-1;
   NewSelfStateState(newk,newk)=SelfStateState(newk,newk)+1;
   NewAllStateState=NewStateNumAtTime'*NewStateNumAtTime;
   NewStateState=NewAllStateState-NewSelfStateState;
   
   
   if strcmp(type, 'coocc')
       NewNWStateState=NewStateState;
 
   elseif strcmp(type, 'binary')
      NewNWStateState=NewStateState-NewPWStateState; 
   
   elseif strcmp(type, 'simi')
       EACT=find(NW(:,4)==t);% EdgeAtCurrentTime
       WACT=sparse(NW(EACT,1), NW(EACT,2), NW(EACT,3));% WAtCurrentTime
       WACT=WACT+WACT';
       J=find(WACT(i,:));
       for k=1:length(J)
               j=J(k);
               kj=find(Z(j,:));
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

if t==1&& T>1 && ismember(i, Index{t+1})
    i_loc_next=find(Index{t+1}==i);
    nki=Z{t+1}(i_loc_next,2);
    NewStateToState(ok,nki)=NewStateToState(ok,nki)-1;
    NewStateToState(newk,nki)=NewStateToState(newk,nki)+1;
    NewStateToAll(ok)=NewStateToAll(ok)-1;
    NewStateToAll(newk)=NewStateToAll(newk)+1;
elseif t==T &&T>1 && ismember(i, Index{t-1})
    i_loc_pre=find(Index{t-1}==i);
    pki=Z{t-1}(i_loc_pre,2);
    NewStateToState(pki,ok)=NewStateToState(pki,ok)-1;
    NewStateToState(pki,newk)=NewStateToState(pki,newk)+1;
elseif T>1
    if ismember(i, Index{t+1});
       i_loc_next=find(Index{t+1}==i);
        nki=Z{t+1}(i_loc_next,2);
        NewStateToState(ok,nki)=NewStateToState(ok,nki)-1;
        NewStateToState(newk,nki)=NewStateToState(newk,nki)+1;
        NewStateToAll(ok)=NewStateToAll(ok)-1;
        NewStateToAll(newk)=NewStateToAll(newk)+1;
    end
    if ismember(i, Index{t-1})
        i_loc_pre=find(Index{t-1}==i);
        pki=Z{t-1}(i_loc_pre,2);
        NewStateToState(pki,ok)=NewStateToState(pki,ok)-1;
        NewStateToState(pki,newk)=NewStateToState(pki,newk)+1;
    end
end
end

if length(find(NewStateNumAtCurrentTime<0))>0
    disp('error happens at line 457')
elseif length(find(NewPWStateState<0))>0
    disp('error happens at line 459')
elseif length(find(NewNWStateState<0))>0
    disp('error happens at line 461')
elseif length(find(NewMWStateState<0))>0
    disp('error happens at line 463')
elseif length(find(NewAllStateState<0))>0
   disp('error happens at line 465')
elseif length(find(NewSelfStateState<0))>0
    disp('error happens at line 467')
elseif length(find(NewStateState<0))>0
    disp('error happens at line 469')
elseif length(find(NewStateToState<0))>0
    disp('error happens at line 471')
elseif length(find(NewStateToAll<0))>0
    disp('error happens at line 473')
elseif length(find(NewStateNumOfNewNodesAtCurrentTime<0))>0
    disp('error happens at line 475')
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