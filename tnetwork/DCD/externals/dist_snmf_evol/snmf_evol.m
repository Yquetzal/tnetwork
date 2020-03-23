function [D, H, logl] = snmf_evol(X, K, minper, maxiternum, D, H, lambda, seed_H)
% SNMF_EVOL - evolutionary non-negative matrix factorization algorithm  
%   This function is a wrapper for the SNMF_EVOL implementation,
%   snmf_evol_imp.p. The implementation details are hidden for proprietary
%   reasons.
%   The implementation extends the soft clustering algorithm by Shipeng Yu
%   and Kai Yu (NIPS 2005).
%
%   Evolutionary Clustering Objective:
%     J = min (1-lambda)*D(W, HDH') + lambda*D(B, HD)
%     s.t. sum_i H_ip = 1; sum_p 1/D_p = 1;
%     regularize model paramters H, D with prior model H(t-1), D(t-1)
%     where B = H(t-1)*D(t-1)
%
%	USAGE
%		[D, H, logl]=snmf_evol(X, K, minper, maxiternum, D, H, lambda, seed_H)
%
%	INPUT
%		X: symmetric similarity matrix of data, N*N
%		K: number of latent clusters
%		minper: the minimum improvement over log likelihood for stopping,
%		default 1e-6
%		maxiternum: maximal number of iterations, default 100
%		D, H: specified prior model parameters
%       lambda: weight for the prior
%       seedH: specified initionalization of parameters (use random
%       initialization if seedH is not specified.
%
%	OUTPUT
%		D: K*1, learned cluster weights
%		H: N*K, learned cluster assignments
%		logl: vector of log likelihood
% 
% Example:
%   See toy_evol.m

% Author: Yu-Ru Lin <yu-ru.lin@asu.edu>, July 2007
% Reference:
%   Yu-Ru Lin et. al. , "FaceNet: A Framework for Analyzing Communities and
%   Their Evolutions in Dynamics Networks", WWW 2008

if nargin < 3
    minper = 1e-6;
end
if nargin < 4
    maxiternum = 100;
end
if nargin < 5
    [D, H, logl]=snmf_evol_imp(X, K, minper, maxiternum);
elseif nargin < 8
    [D, H, logl]=snmf_evol_imp(X, K, minper, maxiternum, D, H, lambda)
else
    [D, H, logl]=snmf_evol_imp(X, K, minper, maxiternum, D, H, lambda, seed_H)
end


