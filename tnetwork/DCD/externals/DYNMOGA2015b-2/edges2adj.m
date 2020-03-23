%Generate the adjacency matrix from the file fileinput containing the edges 

function mat = edges2adj(fileinput,numNodes)

couple = load(fileinput);
mat=zeros(numNodes,numNodes);

for i=1:size(couple,1)
    mat(couple(i,1),couple(i,2)) = 1;
    mat(couple(i,2),couple(i,1)) = 1;
end

q=symamd(mat);
spy(mat(q,q))


