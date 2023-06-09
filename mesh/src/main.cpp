#include <stdio.h>
#include <iostream>
#include <ctime>
#include <array>

#include "../misc_files/CommonInterfaces/CommonExampleInterface.h"
#include "../misc_files/CommonInterfaces/CommonGUIHelperInterface.h"
#include "../misc_files/Utils/b3Clock.h"

#ifdef VISUAL
	#include "../misc_files/OpenGLWindow/SimpleOpenGL3App.h"
#endif
#include "../misc_files/ExampleBrowser/OpenGLGuiHelper.h"

#include "../lib/json.hpp"

#include "cnt_mesh.h"

// this block of code and the global variable and function is used for handling mouse input and
// moving objects via mouse. you can comment it if this capability is not needed any more.
//*************************************************************************************************
// CommonExampleInterface*    example;
cnt_mesh*    example;
int gSharedMemoryKey=-1;

#ifdef VISUAL
b3MouseMoveCallback prevMouseMoveCallback = 0;
static void OnMouseMove( float x, float y)
{
	bool handled = false; 
	handled = example->mouseMoveCallback(x,y); 	 
	if (!handled)
	{
		if (prevMouseMoveCallback)
			prevMouseMoveCallback (x,y);
	}
}

b3MouseButtonCallback prevMouseButtonCallback  = 0;
static void OnMouseDown(int button, int state, float x, float y) {
	bool handled = false;

	handled = example->mouseButtonCallback(button, state, x,y); 
	if (!handled)
	{
		if (prevMouseButtonCallback )
			prevMouseButtonCallback (button,state,x,y);
	}
}
#endif
//*************************************************************************************************


int main(int argc, char* argv[]) {

	// print the start time and start recording the run time
	std::clock_t start = std::clock();
	std::time_t start_time = std::time(nullptr);
	std::cout << std::endl << "start time:" << std::endl << std::asctime(std::localtime(&start_time)) << std::endl;


	// get the input JSON filename
	std::string filename;
	if (argc <= 1){
		filename = "input.json";
	} else {
		filename = argv[1];
	}

	// read the input JSON file
	std::ifstream input_file(filename.c_str());
	nlohmann::json j;
	input_file >> j;	
	
	int number_of_tubes_added_together = j["number of tubes added together"];
	int number_of_active_bundles = j["number of active bundles"];
	int number_of_tubes_before_deletion = j["number of tubes before deletion"];
	int number_of_unsaved_tubes = j["number of unsaved tubes"];
	int number_of_bundles = j["number of bundles"];
	int number_of_steps = j["number_of_steps"];
	btScalar time_step = j["time_step"];
	bool parallel = j["parallel"];
	bool bundle = j["bundle"];
	double spacing = j["cnt intertube spacing [nm]"];
	double thickness = j["cnt expected film thickness [nm]"];


	// flag to let the graphic visualization happen
	bool visualize = j["visualize"];

	#ifdef VISUAL
	SimpleOpenGL3App* app;
	GUIHelperInterface* gui;
	// SimpleOpenGL3App is a child of CommonGraphicsApp virtual class.
	app = new SimpleOpenGL3App("carbon nanotube mesh",1024,768,true);

	prevMouseButtonCallback = app->m_window->getMouseButtonCallback();
	prevMouseMoveCallback = app->m_window->getMouseMoveCallback();

	app->m_window->setMouseButtonCallback((b3MouseButtonCallback)OnMouseDown);
	app->m_window->setMouseMoveCallback((b3MouseMoveCallback)OnMouseMove);
	
	gui = new OpenGLGuiHelper(app,false); // the second argument is a dummy one
	// gui = new DummyGUIHelper();
	CommonExampleOptions options(gui);
	#endif
	#ifdef VISUAL
		// CommonExampleInterface* example;
		example = new cnt_mesh(options.m_guiHelper, j);
	#else
		example = new cnt_mesh(NULL, j);
	#endif

	example->parse_json_prop();
	example->save_json_properties(j);

	
	example->initPhysics();
	example->create_ground_plane(); //container size is set in input.json
	if(parallel)
		example->create_z_plane();
	example->create_tube_colShapes(spacing);
	
	
	#ifdef VISUAL
	if (visualize) {
		example->resetCamera();
	}
	#endif

	int step_number = 0;
	while(true)
	{
		step_number++;
		btScalar dtSec = time_step;
		// btScalar dtSec = 0.01;
		example->stepSimulation(dtSec);
		//example->printtube(2);

		// run logic to add/freeze/etc tubes and draw only on certain ticks (for speed)
		if (step_number % number_of_steps == 0)
		{	
			example->get_Ly(parallel);
			example->get_maxY();
			
			// only drop new tubes when no tubes near or above the drop height
			if (example->read_maxY() < example->read_drop_height() - (bundle ? 2.0 : 1.0))
			{
				// add this many cnt's at a time
				for (int i=0; i<number_of_tubes_added_together; i++)
				{
					// each successive bundle generated higher such that non-parallel bundles don't generate intersecting
					// (the fibers will interleave and keep them intersecting).
					if (bundle)
						example->add_bundle_in_xz(parallel, float(i) * 2.0);
					else 
						example->add_single_tube_in_xz(parallel, 0.0);
					
				}
			}
			
			example->save_tubes(number_of_unsaved_tubes);
			
			if (bundle) {
				example->freeze_bundles(number_of_active_bundles); // keep only this many bundles active (for example 100) and freeze the rest of the bundles
			}
			else
			{
				example->freeze_tubes(number_of_active_bundles); // keep only this many tubes active (for example 100) and freeze the rest of the tubes
			}
				
			example->remove_tubes(number_of_tubes_before_deletion); // keep only this many tubes in the simulation (for example 400) and delete the rest of objects
			
			std::cout << "number of saved tubes: " << example->no_of_saved_tubes() << ",  height [nm]:" << example->read_Ly() << "      \r" << std::flush;
			
			#ifdef VISUAL
			if (visualize)
			{
				app->m_instancingRenderer->init();
				app->m_instancingRenderer->updateCamera(app->getUpAxis());
				example->renderScene();
				
				// draw some grids in the space
				DrawGridData dg;
				dg.upAxis = app->getUpAxis();
				app->drawGrid(dg);
				
				app->swapBuffer();

			}
			#endif
			
		}
		// number of tubes that would be added if simulation were to end now: must be used in num saved tubes used for simulation end check
		int final_added_tube_cnt = number_of_unsaved_tubes - number_of_active_bundles * (bundle ? 7 : 1);
		
		if((example->no_of_saved_tubes() + final_added_tube_cnt) > number_of_bundles || example->read_Ly() > thickness)
			break;
	}

	#ifdef VISUAL
	// if we did not visualize the simulation all along now visualize it one last time.
	if (not visualize)
	{
		example->resetCamera();
		app->m_instancingRenderer->init();
		app->m_instancingRenderer->updateCamera(app->getUpAxis());
		example->renderScene();
		
		// draw some grids in the space
		DrawGridData dg;
		dg.upAxis = app->getUpAxis();
		app->drawGrid(dg);
		
		app->swapBuffer();

	}
	#endif
	
	// save all non-dynamic tubes to bring mesh up to measured height
	if (bundle)
		example->save_tubes(number_of_active_bundles * 7);
	else
		example->save_tubes(number_of_active_bundles);
	std::cout << "number of saved tubes: " << example->no_of_saved_tubes() << ",  height [nm]:" << example->read_Ly() << "      \r" << std::flush;
	
	// overwrite the directory in create_fine_mesh.py with this cnt mesh's output directory
	std::ifstream interpolationScriptIn("./python_scripts/create_fine_mesh.py");
	std::fstream interpolationScriptOut("./python_scripts/~create_fine_mesh.py", std::ios::out);
	const int DIR_LINE = 19;
	int currentLineNum = 0;
	std::string currentLine = "";
	
	for (; currentLineNum < DIR_LINE; currentLineNum++)
	{
		std::getline(interpolationScriptIn, currentLine);
		interpolationScriptOut << currentLine << "\n";
	}
	
	interpolationScriptOut << "DIR = '";
	if (example->output_path().is_relative())
	{
		// path must be relative to python_scripts, which is one directory down from current (mesh)
		if (example->output_path().string()[0] == '.' && example->output_path().string()[1] == '.') {
		  interpolationScriptOut << ".." << std::experimental::filesystem::path::preferred_separator;
		}
		else
		{
		  interpolationScriptOut << ".";
		}
	}
	interpolationScriptOut << example->output_path().string() << "'";
	std::getline(interpolationScriptIn, currentLine);
	
	while (!interpolationScriptIn.eof())
	{
		std::getline(interpolationScriptIn, currentLine);
		interpolationScriptOut << "\n" << currentLine;
		currentLineNum++;
	}
	
	interpolationScriptOut.close();
	std::experimental::filesystem::remove("./python_scripts/create_fine_mesh.py");
	std::experimental::filesystem::rename("./python_scripts/~create_fine_mesh.py", "./python_scripts/create_fine_mesh.py");
	
	
	// print the end time and the runtime
	std::clock_t end = std::clock();
	std::time_t end_time = std::time(nullptr);
	std::cout << std::endl << "end time:" << std::endl << std::asctime(std::localtime(&end_time));
	std::cout << "runtime: " << std::difftime(end_time,start_time) << " seconds" << std::endl << std::endl;
	
	example->exitPhysics();
	delete example;
	#ifdef VISUAL
		delete app;
	#endif
	 
	
	
	return 0;
}

