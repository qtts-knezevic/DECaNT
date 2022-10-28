import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os
import matplotlib as mpl
import json

# TODO fix EOF error on input?????
#  howto: change prompt to put comment before EVERY line not just first

def take_input(l):
  '''
  Extension of input(): tries taking console input until a string
  not beginning in "#" is given (strings beginning in # regarded as comments),
  adds to l and returns first non-comment

  Parameters:
    l (list): list to add input to.

  Returns:
    first non-comment console input.
  '''
  
  inputval = input()
  while len(inputval) != 0 and inputval[0] == "#":
    inputval = input()
    
  l.append(inputval)
  return inputval

# end take_input


def make_comment(s):
    '''
    Parameters:
      s (string): string to make comment
    Returns
      string with # appended to the front
    '''
    
    return "#" + s

# end make_comment



def prompt(s, l):
  '''
    Extention of print() which adds printed string to given list as well
    (with leading "#" to mark it as a comment which will not be taken as input).

    Parameters:
      s (string): string to print and add to l
      l (list): list to add s to as comment
  
    Returns:
      none
  '''
  
  print(s)
  l.extend(map(make_comment, s.split("\n")))

# end prompt


def main():
  # using command-line input rather than args because argparse documentation did not specify clear
  # means of allowing an indefinite number of values associated with optional arguments/flags
  ins = [] # Array storing all console input strings

  # Prompt for data directories to plot from
  directories = []
  
  while 1:
    prompt("Enter a simulation output data directory (enter blank line when all directories have been specified):", ins)
    inputval = take_input(ins)
    
    if (inputval == "" and len(directories) != 0):
      break;
    elif not os.path.exists(inputval):
      prompt("Not a valid path!", ins)
    elif os.path.isfile(inputval):
      prompt("Path was to a file, not the directory!", ins)
    elif not os.access(inputval, os.R_OK):
      prompt("Cannot read path!", ins)
    elif not os.path.exists(os.path.join(inputval, "input.json")):
      prompt("Directory doesn't contain input.json!", ins)
    elif not os.path.exists(os.path.join(inputval, "mesh_input.json")):
      prompt("Directory doesn't contain mesh_input.json!", ins)
    elif not os.path.exists(os.path.join(inputval, "particle_diffusion_length.dat")):
      prompt("Directory doesn't contain diffusion length data file, particle_diffusion_length.dat!", ins)
    elif not os.path.exists(os.path.join(inputval, "particle_diffusion_tensor.dat")):
      prompt("Directory doesn't contain diffusion tensor data file, particle_diffusion_tensor.dat!", ins)
    elif (inputval != ""):
      directories.append(os.path.abspath(inputval)) # standard format, so duplicates can be identified
  # end while

  directories = list(set(directories)) #remove duplicate paths
  data = []
  
  for d in directories:
    f0 = open(os.path.join(d, "input.json"))
    f1 = open(os.path.join(d, "mesh_input.json"))
    f2 = open(os.path.join(d, "particle_diffusion_length.dat"))
    f3 = open(os.path.join(d, "particle_diffusion_tensor.dat"))
              
    data.append({"input": json.loads(f0.read()),
                 "mesh_input": json.loads(f1.read()),
                 "particle_diffusion_length": f2.read().split("\n"),
                 "particle_diffusion_tensor": f3.read().split("\n")
                 })

    f0.close()
    f1.close()
    f2.close()
    f3.close()
  # end for
  
  plots = []

  # data 
  xAxis = 0
  yAxis = 0
  dataPoints = []

  # TODO see if some of these aren't needed
  TIME                   = 0
  TUBE_SPACING           = 1
  QUENCHING_SITE_DENSITY = 2
  TEMPERATURE            = 3
  RELATIVE_PERMITTIVITY  = 4

  DIFFUSION_LENGTH              = 0
  DIFFUSION_TENSOR_COEFFICIENTS = 1
  
  # TODO: make x-axis selectable as either time or some quantity from
  # x-axis: time, tube spacing, quenching site density | temperature, permittivity
  # y-axis:
  # data points: random/parallel, single/bundle, chirality (6,5), (8,7), diffusion tensor coefficients
  #   diffusion length, lifetime ;
  # Maybe preview plot and then have option for editing???
  # export all input as file when finished
  
  # loop broken internally by os.exit
  while 1:
    prompt("Creating Plot " + str(len(plots) + 1), ins)
    
    # prompt user for data directories to use in this plot
    for i in range(len(directories)):
      prompt(str(i) + " " + directories[i] + ("" if i == (len(directories) - 1) else "\n"), ins)

    usedDirectoryIndices = []
    usedDirectories = []
    usedData = []

    prompt("Enter directories to plot data from (enter numbers given in above list, on one space-separated line):", ins)
    while len(usedDirectoryIndices) == 0:
      inputval = take_input(ins);
      usedDirectoryIndices.extend(inputval.split())
      usedDirectoryIndices = list(set(usedDirectoryIndices)) # remove duplicates

    
    
    for i in usedDirectoryIndices:
      try:
        i = int(i)
      except:
        i = -1;
      if i > -1 and i < len(directories):
        usedDirectories.append(directories[i])
        usedData.append(data[i])
    # end for

    print(usedDirectories) # TODO remove

    # prompt for data to graph on x-axis
    inputval = -1
    
    while inputval < 0 or inputval > 4:
      prompt("0  time\n1  tube spacing\n2  quenching site density\n3  temperature\n4  relative permittivity", ins)
      prompt("Enter data to plot on x-axis (enter a single number given in above list):", ins)
      inputval = take_input(ins)
      try:
        inputval = int(inputval)
      except:
        inputval = -1
    # end while
    
    xAxis = inputval

    # prompt for data to graph on y-axis
    inputval = -1

    
    while inputval < 0 or inputval > 1:
      prompt("0 diffusion length \n1 diffusion tensor coefficients", ins)
      prompt("Enter data to plot on y-axis (enter up to two numbers given in above list, on one space-separated line):", ins)
      inputval = take_input(ins)
      
      try:
        inputval = int(inputval)
        yAxis.append(inputval)
      except:
        inputval = -1
    # end while
    
      
    if DIFFUSION_TENSOR_COEFFICIENTS in yAxis :
      prompt("Enter tensor elements to plot (single line, space separated, xx xy xz yx yy yz zx zy zz))", ins)
    if plotDiffusionL:
      prompt("")

    prompt("Plot title:")
    plots.append(plotObj(take_input(ins), xAxis, yAxis, usedDirectories, usedData))
    
    prompt("All plots created? (Y/y to exit plot menu)", ins)
    
    inputval = take_input(ins).upper()
    if len(inputval) == 1 and inputval[0] == "Y":
      break
    
  # end while

  # Prompt for directory to plot data in
  saveDirectory = "."
  
  while 1:
    prompt("Directory to save plots to (be careful, will overwrite previous plot files if present):", ins)
    saveDirectory = take_input(ins)

    if not os.path.exists(saveDirectory):
      try:
        os.mkdir(saveDirectory)
        prompt("Created directory " + saveDirectory, ins)
        break
      except:
        prompt("Not a valid path or otherwise couldn't create it!!", ins)
    elif os.path.isfile(inputval):
      prompt("Path was to a file, not the directory!", ins)
    elif not os.access(saveDirectory, os.W_OK):
      prompt("Cannot write to " + saveDirectory, ins)
    else:
      prompt("Saving to " + saveDirectory, ins)
      break
      
  # end while

  # output all plots

  # write all input arguments (with prompts as comments) to file for reuse
  savedInputFile = open(os.path.join(saveDirectory, "input.log"), "w")
  savedInputFile.write("\n".join(ins) + "\n")
  savedInputFile.close()

# end main

  
    
class plotObj:
  
  def __init__(self, title, x, y, directories, data):
    '''
    Constructor for 

    Parameters:
      
    '''
    this.x = x
    this.y = y
    this.directories = directories
    this.data = data
    
  def outputPlot(d):
    '''
    
    
    Parameters:
      d (str): path to directory plot will be saved in
    '''
    pass
  

if __name__ == '__main__':
  main()
