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
