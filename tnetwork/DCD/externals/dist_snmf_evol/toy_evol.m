% TOY_EVOL - A toy example to demonstrate evolutionary soft clustering
%   This will show how SNMF_EVOL improves SNMF. Note the results of the
%   second step in the example.
%
% See also SNMF_EVOL

% Author: Yu-Ru Lin <yu-ru.lin@asu.edu>, November 2008

clc;

% t=1: a toy network with 6 nodes, 2 intrisic clusters
K=2;
X=[
    1 1 1 0 0 0
    1 1 1 0 0 0
    1 1 1 0 0 0
    0 0 0 1 1 1
    0 0 0 1 1 1
    0 0 0 1 1 1
    ];
disp('A toy network X(t=1) =');disp(X)
[D, H, logl] = snmf_evol(X, K, 1e-6, 500);
Y=H./repmat(sum(H,2),[1 2]); 
disp('Soft clustering results for X:');
disp('cluster weights:');disp(full(D))
disp('cluster assignment:'); disp(full(Y));
subplot(211);spy(X); title('toy network (t=1)')
subplot(212);plot(Y); legend(['c1';'c2']); xlabel('vertex index'); ylabel('probability in the cluster')
figure(gcf);input('continue...'); 

% t=2: assume a slight change in network
X=[
    1 0 1 0 0 0
    0 1 1 0 0 0
    1 1 1 1 1 1
    0 0 1 1 1 0
    0 0 1 1 1 0
    0 0 1 0 0 1
    ];
disp('A slight change in network s.t. X(t=2) =');disp(X)
lambda = 0.2;
[D, H, logl] = snmf_evol(X, K, 1e-6, 500,D,H,lambda,H);
Y=H./repmat(sum(H,2),[1 2]);
disp('Evolutionary soft clustering results for X:');
disp('cluster weights:');disp(full(D))
disp('cluster assignment:'); disp(full(Y));

disp('Compare with soft clustering:');
[Dsn, Hsn, logl] = snmf_evol(X, K, 1e-6, 500);
Ysn=Hsn./repmat(sum(Hsn,2),[1 2]);
disp('cluster weights:');disp(full(Dsn))
disp('cluster assignment:'); disp(full(Ysn));

subplot(221);spy(X); title('toy network (t=2)')
subplot(223);plot(Y); title('with evolution'); legend(['c1';'c2'],'Location','best'); xlabel('vertex index'); ylabel('probability in the cluster')
subplot(224);plot(Ysn); title('without evolution'); legend(['c1';'c2'],'Location','best'); xlabel('vertex index'); ylabel('probability in the cluster')
figure(gcf);input('continue...');

% t=3: assume a slight change in network
X=[
    1 1 0 1 0 0
    1 1 1 0 0 0
    0 1 1 1 0 0
    1 0 1 1 1 0
    0 0 0 1 1 1
    0 0 0 0 1 1
    ];
disp('A slight change in network s.t. X(t=3) =');disp(X)
[D, H, logl] = snmf_evol(X, K, 1e-6, 500,D,H,lambda,H);
Y=H./repmat(sum(H,2),[1 2]);
disp('Evolutionary soft clustering results for X:');
disp('cluster weights:');disp(full(D))
disp('cluster assignment:'); disp(full(Y));

disp('Compare with soft clustering:');
[Dsn, Hsn, logl] = snmf_evol(X, K, 1e-6, 500);
Ysn=Hsn./repmat(sum(Hsn,2),[1 2]);
disp('cluster weights:');disp(full(Dsn))
disp('cluster assignment:'); disp(full(Ysn));

subplot(221);spy(X); title('toy network (t=3)')
subplot(223);plot(Y); title('with evolution'); legend(['c1';'c2'],'Location','best'); xlabel('vertex index'); ylabel('probability in the cluster')
subplot(224);plot(Ysn); title('without evolution'); legend(['c1';'c2'],'Location','best'); xlabel('vertex index'); ylabel('probability in the cluster')
figure(gcf);
