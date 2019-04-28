%init function for the model - set the parameters of the blocks
% -> this function needs to be set as InitFcn in Simulink (Open Simulink MB.slx -> 
% make sure you are on the top layer, not in a subsystem -> View -> Property Inspector ->
% Tab "Properties" -> Callbacks -> InitFcn)

%the current model
model = strtok(get_param(gcb, 'Parent'),'/');
%find all blocks
h = find_system(model, 'LookUnderMasks', 'on', 'SearchDepth', 2);
%go through all blocks
for k=1:length(h)
    %for the transfer functions -> replace {} with []
    if endsWith(h{k}, 'tfFeedforward')
        tfFeedforward_b = strrep(tfFeedforward_b, '{', '[');
        tfFeedforward_b = strrep(tfFeedforward_b, '}', ']');
        tfFeedforward_a = strrep(tfFeedforward_a, '{', '[');
        tfFeedforward_a = strrep(tfFeedforward_a, '}', ']');
        set_param(strcat(model, '/tfFeedforward/TransferFunction'), 'Numerator', tfFeedforward_b, 'Denominator', tfFeedforward_a);
    elseif endsWith(h{k}, 'procUnitSys')
        procUnitSys_b = strrep(procUnitSys_b, '{', '[');
        procUnitSys_b = strrep(procUnitSys_b, '}', ']');
        procUnitSys_a = strrep(procUnitSys_a, '{', '[');
        procUnitSys_a = strrep(procUnitSys_a, '}', ']');   
        set_param(strcat(model, '/procUnitSys/TransferFunction'), 'Numerator', procUnitSys_b, 'Denominator', procUnitSys_a);
    elseif endsWith(h{k}, 'tfDist')   
        tfDist_b = strrep(tfDist_b, '{', '[');
        tfDist_b = strrep(tfDist_b, '}', ']');
        tfDist_a = strrep(tfDist_a, '{', '[');
        tfDist_a = strrep(tfDist_a, '}', ']');   
        set_param(strcat(model, '/tfDist/TransferFunction'), 'Numerator', tfDist_b, 'Denominator', tfDist_a);
    %for the add -> set the Input
    elseif endsWith(h{k}, 'addFeedforward')
        set_param(strcat(model, '/addFeedforward/Add'), 'Inputs', '-+|');
    %for the PID controller -> set the current values of P I D
    elseif endsWith(h{k}, 'PID')
        P = ctrlPIDSys_k;
        I = num2str(1/str2num(ctrlPIDSys_Ti));
        D = '0';
        set_param(strcat(model, '/ctrlPIDSys/PID'), 'P', P, 'I', I, 'D', D);
    end
end