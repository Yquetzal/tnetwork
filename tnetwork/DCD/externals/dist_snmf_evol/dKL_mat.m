function d = dKL_mat(X,Y)
%     Xi = find(X .* Y); 
%     X = X(Xi);
%     Y = Y(Xi);
%     d = sum(sum(X .* log(X ./ Y) - X + Y));
% modified for large (sparse) matrices
%     [i,j,vx] = find(X .* spones(Y));
%     [i,j,vy] = find(spones(X) .* Y);
%     X = vx;
%     Y = vy;
%     d = sum(sum(X .* log(X ./ Y) - X + Y));
% handling "log of zero" by adding small value to all probabilities
    X=X./sum(sum(X));
    Y=Y./sum(sum(Y));
    X = X+eps; 
    Y = Y+eps; 
%     d = sum(sum(X .* log(X ./ Y)) - X + Y);
    d = sum(sum(X .* log(X ./ Y)));
    d = full(d);
end %