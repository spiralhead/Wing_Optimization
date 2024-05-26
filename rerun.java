package macro;

import java.util.*;

import star.common.*;
import star.base.neo.*;
import star.meshing.*;
import java.io.File;
import java.util.concurrent.TimeUnit;
import star.base.report.*;

public class rerun extends StarMacro {

  public void execute() {
	  Simulation simulation_0 = 
      getActiveSimulation();
	  simulation_0.println("Current directory is" + System.getProperty("user.dir"));
	  simulation_0.println("Session directory is" + get_session_dir());
	  
	Solution solution_0 = 
      simulation_0.getSolution();

    solution_0.clearSolution();
	
      boolean result = true;
    result =  wait_for_file();  
     for(int i=0;i<=100;i++){
		 
	if (check_end()){end_of_optimization();return;}
  
if (result)
        rerun();
    else
        adjoint();

    result =  wait_for_file();
    }
  }
  
  private boolean check_end()
  {
	  	 Simulation simulation_0 = 
      getActiveSimulation();
	  String home_dir = get_session_dir();
      File file = new File(home_dir+"\\optimization_end.command");
      return file.exists();
	  
  }
  
  private void end_of_optimization(){
	  
    Simulation simulation_0 = 
      getActiveSimulation();

    MonitorPlot monitorPlot_0 = 
      ((MonitorPlot) simulation_0.getPlotManager().getPlot("Loss Monitor Plot"));
	  
	  String home_dir = get_session_dir();

    monitorPlot_0.export(resolvePath(home_dir + "\\quality_convergence.csv"), ",");
	
  }
  
  private String get_session_dir(){
	  	  Simulation simulation_0 = 
      getActiveSimulation();
	  return simulation_0.getSessionDir();
  }
  
  private boolean wait_for_file(){
	 Simulation simulation_0 = 
      getActiveSimulation();
	  String home_dir = get_session_dir();
      File file = new File(home_dir+"\\parametric_wing.x_t");
      File jac_eval_file = new File(home_dir+ "\\jac_eval.command");
      while((!file.exists())&&(!jac_eval_file.exists())){
		  simulation_0.println("Still waiting for parametric_wing.x_t or jac_eval.command");
		  if (check_end()){end_of_optimization();return false;}
		  try{TimeUnit.SECONDS.sleep(1);}
      catch(InterruptedException ex){}
      }
      if(file.exists()) 
          return true;
      else
          return false;
  }
  
  private void adjoint(){
          Simulation simulation_0 = 
      getActiveSimulation();
      
          AdjointSolver adjointSolver_0 = 
      ((AdjointSolver) simulation_0.getSolverManager().getSolver(AdjointSolver.class));
      
	  String home_dir = get_session_dir();
          File jac_eval_file = new File(home_dir + "\\jac_eval.command");
		  
		
      if(jac_eval_file.exists())
    {
    
    adjointSolver_0.runAdjoint();

    adjointSolver_0.computeMeshSensitivity();

    XyzInternalTable xyzInternalTable_0 = 
    ((XyzInternalTable) simulation_0.getTableManager().getTable("AllSensitivity"));

    xyzInternalTable_0.extract();

    xyzInternalTable_0.export(home_dir + "\\AllSensitivity.csv", ",");
    
    jac_eval_file.delete();
    }
  }

  private void rerun() {

    Simulation simulation_0 = 
      getActiveSimulation();
	
	String home_dir = get_session_dir();
	
	simulation_0.println("Starting rerun!");
	
    CadPart cadPart_2 = 
      ((CadPart) simulation_0.get(SimulationPartManager.class).getPart("region"));

    cadPart_2.reimportPart(resolvePath(home_dir + "\\parametric_wing.x_t"), 0.0, false, NeoProperty.fromString("{\'STEP\': 0, \'NX\': 0, \'CATIAV5\': 0, \'SE\': 0, \'JT\': 0}"));
    
    File file = new File(home_dir + "\\parametric_wing.x_t");
    
    if (file.delete()){
        
    }
    else{
        return;
    }

    MeshPipelineController meshPipelineController_0 = 
      simulation_0.get(MeshPipelineController.class);

    meshPipelineController_0.generateVolumeMesh();
    
        ScalarGlobalParameter scalarGlobalParameter_0 = 
      ((ScalarGlobalParameter) simulation_0.get(GlobalParameterManager.class).getObject("AsymptoticParameter"));
      
     scalarGlobalParameter_0.getQuantity().setValue(0.0005);

	
	    StepStoppingCriterion stepStoppingCriterion_0 = 
      ((StepStoppingCriterion) simulation_0.getSolverStoppingCriterionManager().getSolverStoppingCriterion("Maximum Steps"));

    stepStoppingCriterion_0.setIsUsed(true);

	    IntegerValue integerValue_0 = 
      stepStoppingCriterion_0.getMaximumNumberStepsObject();

    integerValue_0.getQuantity().setValue(simulation_0.getSimulationIterator().getCurrentIteration()+500);
	simulation_0.getSimulationIterator().step(50);
	simulation_0.getSimulationIterator().run();
	
	    stepStoppingCriterion_0.setIsUsed(false);
	
    scalarGlobalParameter_0.getQuantity().setValue(0.0);

    Units units_0 = 
      ((Units) simulation_0.getUnitsManager().getObject(""));

    scalarGlobalParameter_0.getQuantity().setUnits(units_0);


      
    refresh_points();
    
	    ReportMonitor reportMonitor_0 = 
      ((ReportMonitor) simulation_0.getMonitorManager().getMonitor("Loss Monitor"));

    simulation_0.getMonitorManager().export(home_dir + "\\quality.csv", ",", new NeoObjectVector(new Object[] {reportMonitor_0}));

  }
  
   private void refresh_points() {

    Simulation simulation_0 = 
      getActiveSimulation();
	  
	 simulation_0.println("Starting adjoint stage");

    FileTable fileTable_0 = 
      ((FileTable) simulation_0.getTableManager().getTable("inner_surf"));

    fileTable_0.extract();

    PointSet pointSet_0 = 
      ((PointSet) simulation_0.get(PointSetManager.class).getObject("Table Point Set"));

    TablePointGenerator tablePointGenerator_0 = 
      ((TablePointGenerator) pointSet_0.getPointGenerator());

    tablePointGenerator_0.setTable(fileTable_0);

    tablePointGenerator_0.setX0Data("X");

    tablePointGenerator_0.setY0Data("Y");

    tablePointGenerator_0.setZ0Data("Z");

    tablePointGenerator_0.regeneratePointSet();

  }
}
