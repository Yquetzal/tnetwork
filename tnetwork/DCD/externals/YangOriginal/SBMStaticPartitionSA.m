function net=SBMStaticPartitionSA(graph,K,net)
% SBM Static Clustering using Simulated Annealing 
% usage: Z=SBMStaticPartitionSA(graph,K,net)
%  graph a structure has the following fields
%      W: the adjacency matrix or observed links at the current time 
%      n:  the number of nodes
%  K: the number of clusters
%  net is a structure and has the following fileds
%  net.type: the type of the graph, 'binary' 'coocc' 'simi'
%  net.wthrehold the w threshold for similarity graph
%  net.para: the hyperparameters
%  net.Temp the tempature sequence for simulated annealing 
%  net.N: the number of iterations for simulated annealing   length of Temp must be equal to the lenght of N
%  net.Z: the initial assignment of the clusters which is empty or  n*K binary matrix
%  net.verbosity the level of ouput  0 nooutput, 1 output
%  net.objfunc the final value of objective function
%  Temp=1:-0.01:0 N=[20*ones(1,20) 10*ones(1,40) 5*ones(1,40) 5]  
%  Temp=1:-0.1:0    N=[20*ones(1,2) 10*ones(1,5) 5*ones(1,4)]


if nargin<3
    help SBMStaticPartitionSA
end

net.learning='StaticClustering';

W=graph.W;
n=graph.n;

if issymmetric(W)==0
    if length(find(W==0))>1
        error('W matrix is not symmetric');
    else
        W=sparse(W(:,1),W(:,2),W(:,3));% transfer the link format to matrix 
        W=W+W';% symmetric 
    end
else
    W=W-diag(diag(W));
end

if isempty(net.type)
    error('you must specify the type of your W: binary coocc simi');
else
    type=net.type;
end

if isempty(net.wthreshold)&& strcmp(net.type,'simi')
    wthreshold=[0.3 0.7]; % wthreshold for similarity link
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
  %% initial the hidden variables by random guess
    C=rand(n, K);
    MaxC=repmat(max(C,[],2),1,K);
    C=(C>=MaxC);
    Z=sparse(C.*ones(n,K)); 
else 
    Z=sparse(net.Z);
end

if isempty(net.verbosity)
    verbosity=1;
    net.verbosity=1;
else
    verbosity=net.verbosity;
end

if strcmp(type, 'simi')
   %PW=sparse(ones(n,n).*(W>=(wthreshold(2).*ones(n,n))));
   %NW=sparse(ones(n,n).*(W<=(wthreshold(1).*ones(n,n))));
   %MW=sparse((ones(n,n)-PW-NW));
   NW=[];
   MW=[];
elseif strcmp(type,'binary')
    PW=sparse(W);
    NW=[];
    MW=[];
elseif strcmp(type,'coocc')
    PW=sparse(W);
    NW=[];
    MW=[];
end

%% Define the parameters matrices
ga=ones(1,K);
A=paraP(1)*ones(K,K)+paraP(2)*eye(K);%\alpha
B=paraP(3)*ones(K,K);

%% compute the initial quantities
PWStateState=zeros(K,K);
NWStateState=zeros(K,K);
MWStateState=zeros(K,K);
StateState=zeros(K,K);
SelfStateState=zeros(K,K);

%% StateNumAtOne
StateNumAtOne=sum(Z(:,:),1);
%% PWStateState
[I J]=find(PW);
for k=1:length(I)
    i=I(k);
    j=J(k);
    if j>i
        row=find(Z(i,:));
        col=find(Z(j,:));
        PWStateState(row,col)=PWStateState(row,col)+PW(i,j);
        PWStateState(col,row)=PWStateState(col,row)+PW(i,j);
    end
end
%% SelfStateState and StateState
for i=1:n
    row=find(Z(i,:));
    SelfStateState(row,row)=SelfStateState(row,row)+1;
end

StateState=StateNumAtOne'*StateNumAtOne-SelfStateState;

%% NWStateState MWStateState
if strcmp(type, 'coocc')
    NWStateState=StateState;
end
if strcmp(type, 'binary')
   NWStateState=StateState-PWStateState;
end

if strcmp(type, 'simi')
    [I J]=find(NW);
    Link=[I J];
    In=find((Link(:,1)-Link(:,2))<0);
    I=Link(In,1);
    J=Link(In,2);
    ZI=Z(I,:);
    ZJ=Z(J,:);
    NWSS=sparse(zeros(K,K));
    NWSS=PWSS+ZI'*ZJ;
    NWStateState=NWSS+NWSS';
    MWStateState=StateState-PWStateState-NWStateState;
end


%% iteration
change=n;
for Tk=1:length(Temp)
    T=Temp(Tk);
    for it=1:N(Tk)
        change=n;
        %P=randperm(n);
        P=1:n;
        for j=1:n
           i=P(j);
           ok=find(Z(i,:));
           NewStateNumAtOne=zeros(K,K);
           NewPWStateState=zeros(K,K,K);
           NewNWStateState=zeros(K,K,K);
           NewMWStateState=zeros(K,K,K);
           NewSelfStateState=zeros(K,K,K);
           NewStateState=zeros(K,K,K);
           m=-inf;
           shifK=[];
           for k=1:K
                CondPro=zeros(1,K);
                NewZ=sparse(zeros(1,K));
                NewZ(k)=1;
                [NewStateNumAtOne(k,:) NewPWStateState(:,:,k) NewNWStateState(:,:,k) NewMWStateState(:,:,k) NewStateState(:,:,k) NewSelfStateState(:,:,k)]=update(StateNumAtOne, PWStateState, NWStateState,MWStateState, StateState,SelfStateState, i,NewZ,Z,PW,NW,MW,n,K,type);
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
                o=sum(gammaln(NewStateNumAtOne(k,:)+ga))+(sum(sum(betaln(PWS+MWS+A, NWS+MWS+B)))+sum(betaln(PWSD+MWSD+diag(A), NWSD+MWSD+diag(B))))/2;%gammaln(NewWStateState+A)+gammaln(NewNWStateState+B)-gammaln(NewWStateState+NewNWStateState+A+B)));
                if o>m
                    if T~=0
                        for pk=1:k-1
                            shifK(pk)=shifK(pk)*exp((m-o)/T);
                        end                 
                        shifK(k)=exp((o-o)/T);
                    else
                        for pk=1:k-1
                            shifK(pk)=0;
                        end
                        shifK(k)=1;
                    end
                    m=o;
                else
                    if T~=0
                        shifK(k)=exp((o-m)/T);
                    else
                        shifK(k)=0;
                    end
                end
           end
           maxPro=1./sum(shifK);
           CondPro=shifK.*maxPro;

%% Gibbs Sampling
             if T~=0
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
                        Z(i,:)=NewZ;
                        StateNumAtOne=NewStateNumAtOne(newk,:);
                        PWStateState=NewPWStateState(:,:,newk);
                        NWStateState=NewNWStateState(:,:,newk);
                        StateState=NewStateState(:,:,newk);
                        SelfStateState=NewSelfStateState(:,:,newk);       
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
                        Z(i,:)=NewZ;
                        StateNumAtOne=NewStateNumAtOne(newk,:);
                        PWStateState=NewPWStateState(:,:,newk);
                        NWStateState=NewNWStateState(:,:,newk);
                        StateState=NewStateState(:,:,newk);
                        SelfStateState=NewSelfStateState(:,:,newk);   
                    end
             end% endif
        end% end all members
        if verbosity==1
%             Temp_iteration=[T it]
%             m
              net.objfun(sum(N(1:Tk-1))+it)=o;
              disp(sprintf('Temp=%d, Iteration=%d, objfun=%f', T,it, o));
        end
    end% end one iteration
end% end all tempature
%net.objfun=o;
for k=1:K
    Z(:,k)=(k*ones(n,1)).*Z(:,k);
end
Z=sum(Z,2);
net.Z=full(Z);

function [NewStateNumAtOne NewPWStateState NewNWStateState NewMWStateState NewStateState NewSelfStateState]=update(StateNumAtOne, PWStateState, NWStateState,MWStateState,StateState,SelfStateState, i, NewZ, Z,PW,NW,MW, n,K,type)
ok=find(Z(i,:));
k=find(NewZ);
if k==ok
   NewStateNumAtOne=StateNumAtOne;
   NewPWStateState=PWStateState;
   NewNWStateState=NWStateState;
   NewMWStateState=MWStateState;
   NewStateState=StateState;
   NewSelfStateState=SelfStateState;
else
   NewStateNumAtOne=StateNumAtOne;
   NewStateNumAtOne(ok)=StateNumAtOne(ok)-1;
   NewStateNumAtOne(k)=NewStateNumAtOne(k)+1;
   NewPWStateState=PWStateState;
   NewNWStateState=zeros(K,K);
   NewMWStateState=zeros(K,K);
   
   J=find(PW(i,:));
   index1=find(Z(i,:));
   Newindex1=find(NewZ);
   for k=1:length(J)
           j=J(k);
           index2=find(Z(j,:));
           NewPWStateState(index1,index2)=NewPWStateState(index1,index2)-PW(i,j);
           NewPWStateState(index2,index1)=NewPWStateState(index2,index1)-PW(i,j);
           NewPWStateState(Newindex1,index2)=NewPWStateState(Newindex1,index2)+PW(i,j);
           NewPWStateState(index2,Newindex1)=NewPWStateState(index2,Newindex1)+PW(i,j);   
   end
 
   
   NewSelfStateState=SelfStateState;
   NewSelfStateState(index1,index1)=SelfStateState(index1,index1)-1;
   NewSelfStateState(Newindex1,Newindex1)=SelfStateState(Newindex1,Newindex1)+1;
   
   NewStateState=NewStateNumAtOne'*NewStateNumAtOne-NewSelfStateState;
   
   if strcmp(type, 'coocc')
       NewNWStateState=NewStateState;
   end
   if strcmp(type, 'binary')
      NewNWStateState=NewStateState-NewPWStateState; 
   end
   if strcmp(type, 'simi')
       J=find(NW(i,:));
       for k=1:length(J)
               j=J(k);
               index2=find(Z(j,:));
               NewNWStateState(index1,index2)=NewNWStateState(index1,index2)-NW(i,j);
               NewNWStateState(index2,index1)=NewNWStateState(index2,index1)-NW(i,j);
               NewNWStateState(Newindex1,index2)=NewNWStateState(Newindex1,index2)+NW(i,j);
               NewNWStateState(index2,Newindex1)=NewNWStateState(index2,Newindex1)+NW(i,j);
       end
       NewMWStateState=NewStateState-NewPWStateState-NewNWStateState;
    end
end


if length(find(NewStateNumAtOne<0))>0
    disp('error at line 346');
elseif length(find(NewPWStateState<0))>0
    disp('error at line 348');
elseif length(find(NewNWStateState<0))>0
    disp('error at line 350');
elseif length(find(NewMWStateState<0))>0
    disp('error at line 352');
elseif length(find(NewSelfStateState<0))>0
    disp('error at line 354');
elseif length(find(NewStateState<0))>0
    disp('error at line 356');
end