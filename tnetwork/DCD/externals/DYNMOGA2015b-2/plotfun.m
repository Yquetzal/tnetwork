%visualizza la best fitness in scala logaritmica
function state = plotfun(options,state,flag)


persistent last_best;
if strcmpi(flag,'init')
  %set(gca,'xlim',[1,options.Generations],'Yscale','log');
   set(gca,'xlim',[1,options.Generations]);
  hold on;
  xlabel Generation
  title('Change in Best Fitness value')
end
best = min(state.Score);
if state.Generation == 0
    last_best = best;
else
    change = last_best - best;
    last_best = best;
    plot(state.Generation,change,'.r');
    title('Change in Best Fitness value')
end


%[unused,i] = min(state.Score);
%genotype = state.Population{i};

%plot(locations(:,1),locations(:,2),'bo');
%plot(locations(genotype,1),locations(genotype,2));
%hold off
