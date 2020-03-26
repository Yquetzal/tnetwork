function run_DYNMOGA(fileClasses,fileEdges, T,outputFile)
%T added by Remy Cazabet, number of time steps
% The following code and comments have been written by Yu-Ru Lin. 
% We added the call to our program run_DYNMOEAmain(W_Cube,nbCluster)
% and the function gen_syn_fileInput(T,fileClasses,fileEdges) in order to
% test DYNMOGA by giving "fileClasses" and "fileEdges" as input
% containing couples (node classLabel) and (node1 node2), respectively, that list for
% each node the cluster label it belongs to, and the list of edges of a
% network. 

%if no input file is given, the function gen_syn2.m, written by Yu-Ru Lin, 
%generates Newman's benchmark as described below 
% 
% Clara Pizzuti November 2016

%fI you want the FacetNet software, please contact Dr. Yu-Ru Lin.


%  run the evolutionary SNMF with Newman's generator
%   The scrip first generates synthetic dataset by Newman's generator (50
%   timesteps). 
%   The results are saved in *.mat.
%   The code for NCut clustering (case 1) and evolutionary spectral
%   clustering (case 3) is not included. Please contact Dr. Yun Chi if you
%   need the code.
%
% See also gen_syn2, computePerformance, run_snmfEvol

% Author: Yu-Ru Lin <yu-ru.lin@asu.edu> and Yun Chi <ychi@sv.nec-labs.com>,
% November 2008


zs = [5]';
ncs = [1]';

alpha = 0.8;

for k1 = 1:1:size(zs,1)
    for k2 = 1:1:size(ncs,1)

        CA1 = [];
        CR1 = [];
        CP1 = [];
        CF1 = [];
        CN1 = []; %NMI

        allCA1 = [];
        allCR1 = [];
        allCP1 = [];
        allCF1 = [];
        allCN1 = [];


        cc = 'bgrcmyk';

        %%%%%nbTime = 4;
        %%%%%T = nbTime; %%remove by remy cazabet
        %for alpha=alphas
            %total_iteration = 50; % number of runs
            total_iteration = 1; 
            for k = 1:1:total_iteration
                

                %in this case give the file names containing cluster
                %label for each node and list of edges
                [blogSize nbCluster fname]= gen_syn_fileInput(T,fileClasses,fileEdges)

                eval(['load ' fname]);

                
                %case 1, the DYNMOGA case
                %case 1, the DYNMOGA case
                %set parameters for GAs
                gen=10; %set the number of generations
                popSize=10; % set population size
                CrossoverFraction=0.8; %set crossover fraction
                mutationRate=0.2; %set mutation rate
                
               
               
                Z1 = run_DYNMOEAmain(W_Cube,nbCluster,gen,popSize,CrossoverFraction,mutationRate);
                allZ1{k} = Z1;
                allCA1 = [allCA1; CA1'];
                allCR1 = [allCR1; CR1'];
                allCP1 = [allCP1; CP1'];
                allCF1 = [allCF1; CF1'];
                allCN1 = [allCN1; CN1'];
              

                Z0 = zeros(blogSize,nbCluster);
                for j = 1:1:nbCluster
                    Z0(find(Z1(:,1)==j),j) = 1;
                end
                



            

            fname = ['result_T_' int2str(T)  ...
                '_bS_' int2str(blogSize) ...
                '.mat'];
            fname = [fileClasses "file.mat"];

            eval(['save ' fname]);

    end
end
end