package MBOM
  block TransferFunction
    extends Modelica.Blocks.Continuous.TransferFunction;
  end TransferFunction;

  block Add
    extends Modelica.Blocks.Math.Add;
  end Add;

  block Constant
    extends Modelica.Blocks.Sources.Constant;
  end Constant;

  block Feedback
    extends Modelica.Blocks.Math.Feedback;
  end Feedback;
end MBOM;
