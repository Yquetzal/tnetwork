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

