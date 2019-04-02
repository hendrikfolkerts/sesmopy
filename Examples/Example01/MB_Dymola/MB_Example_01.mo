within ;
package MB_Example_01

  block B
    extends Modelica.Blocks.Sources.Constant;
  end B;

  block C
    extends Modelica.Blocks.Math.Gain;
  end C;
  annotation (uses(Modelica(version="3.2.2")));
end MB_Example_01;
