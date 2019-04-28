within ;
package MB
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

  block PID
    extends Modelica.Blocks.Continuous.PID;
  end PID;

  block Step
    extends Modelica.Blocks.Sources.Step;
  end Step;
  annotation (uses(Modelica(version="3.2.2")));
end MB;
