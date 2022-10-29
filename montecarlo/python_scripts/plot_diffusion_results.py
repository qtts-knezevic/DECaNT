import matplotlib.pyplot as plt
import os
import json
import pandas as pd

# TODO see if some of these aren't needed
# X-AXIS GLOBALS
TIME                   = 0
TUBE_SPACING           = 1
QUENCHING_SITE_DENSITY = 2
TEMPERATURE            = 3
RELATIVE_PERMITTIVITY  = 4

AVG_DISPLACEMENT_SQUARED      = 0
DIFFUSION_TENSOR              = 1
DIFFUSION_LENGTH              = 2
DIFFUSION_TENSOR_COEFFICIENTS = ["Dxx", "Dxy", "Dxz", "Dyy", "Dyz", "Dzz"]

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
      directories.append(os.path.abspath(inputval)) # standard directory format, so duplicates can be identified
  # end while

  directories = list(set(directories)) #remove duplicate paths
  data = []
  
  for d in directories:
    f0 = open(os.path.join(d, "input.json"))
    f1 = open(os.path.join(d, "mesh_input.json"))
    f2 = open(os.path.join(d, "particle_displacement.avg.squared.dat"))
    f3 = open(os.path.join(d, "particle_diffusion_tensor.dat"))
    f4 = open(os.path.join(d, "particle_diffusion_length.dat"))
              
    data.append({"input": json.loads(f0.read()),
                 "mesh_input": json.loads(f1.read()),
                 "displacement_avg_squared": pd.read_csv(f2, comment="#"),
                 "diffusion_tensor": pd.read_csv(f3, comment="#"),
                 "diffusion_length": pd.read_csv(f4, comment="#")
                 })

    f0.close()
    f1.close()
    f2.close()
    f3.close()
    f4.close()
  # end for
  
  plots = []

  # data 
  xAxis = 0
  yAxis = []
  dataPoints = []

  
  
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
    usedData = []

    prompt("Enter directories to plot data from (enter numbers given in above list, on one space-separated line):", ins)
    while len(usedDirectoryIndices) == 0:
      inputval = take_input(ins);
      
      for i in inputval.split():
        try:
          i = int(i)
        except:
          i = -1;
        if i > -1 and i < len(directories):
          usedDirectoryIndices.append(i)
        else:
          prompt(str(i) + " was not a valid selection! (-1 may indicate a non-integer input was entered)", ins)

    usedDirectoryIndices = list(set(usedDirectoryIndices)) # remove duplicates
    
    for i in usedDirectoryIndices:
      usedData.append(data[i])

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

    # prompt for data to graph on y-axis (only two selections possible, since we can only have 2 y-axes...)
    inputval = -1
    prompt("0 average displacement squared \n1 diffusion tensor\n2 diffusion length", ins)
    prompt("Enter data to plot on y-axis (enter up to two numbers given in above list, on one space-separated line):", ins)
    
    while len(yAxis) == 0:
      inputval = take_input(ins)

      for i in inputval.split():
        if len(yAxis) > 2:
          break
        try:
          i = int(i)
        except:
          i = -1
        
        if i > -1 and i < 3:
          yAxis.append(i)
        else:
          prompt(str(i) + " was not a valid selection! (-1 may indicate a non-integer input was entered)", ins)
    # end while
    
    # prompt for diffusion tensor coefficients to use if plotting tensor
    if DIFFUSION_TENSOR in yAxis:
      while not any(i in yAxis for i in DIFFUSION_TENSOR_COEFFICIENTS):
        prompt("Enter tensor elements to plot (single line, space separated, xx xy xz yy yz zz))", ins)
        inputval = take_input(ins)
        
        for c in map(str.lower, inputval.split()):
          if "D" + c in DIFFUSION_TENSOR_COEFFICIENTS:
            yAxis.append("D" + c)
          else:
            prompt(c + " was not a valid coefficient", ins)
    # end if

    prompt("Plot title:", ins)
    plots.append(plotObj(take_input(ins), xAxis, yAxis, usedData))

    plots[len(plots) - 1].outputPlot()
    # TODO prompt for graphical adjustments to graph
    
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

  # save all plots
  for p in range(len(plots)):
    plots[p].savePlot(saveDirectory, p)

  # write all input arguments (with prompts as comments) to file for reuse
  savedInputFile = open(os.path.join(saveDirectory, "input.log"), "w")
  savedInputFile.write("\n".join(ins) + "\n")
  savedInputFile.close()

  print("If any plots were specified incorrectly, the input.log file can be modified and piped as input to this script to produce corrected graphs")
# end main


class plotObj:
  '''
  Holds the data necessary to draw a plot, and contains methods to
  draw or save a plot from that data
  '''
  
  def __init__(self, title, x, y, data):
    '''
    Constructor for plotObj

    Parameters:
      title: title of this plot
      x (int): data to use for x-axis (see globals at top of file)
      y (list): data to use for y-axis
      data (list of dicts): the data sources from which to plot
    '''

    self.title = title
    self.x = x
    self.y = y
    self.data = data

  # end __init__
    
  def createPlot(self):
    '''
    Creates this plot.

    Returns:
      This plot as mpl figure.
    '''
    
    fig = plt.figure()
    ax = fig.subplots()
    ax.set_title(self.title)
    coeffs = list(set(DIFFUSION_TENSOR_COEFFICIENTS).intersection(self.y))

    # TODO calculate average final values when not plotting over time
    if self.x != TIME:
        pass
    
    if self.x == TIME:
      for d in self.data:
        maxTime = len(d["diffusion_tensor"]["time"])
        minTime = int(maxTime / 4) # look into after tensor calculation corrected
        
        for i in range(minTime, len(d["diffusion_tensor"]["time"])):
          print(i)
          for c in coeffs:
            # TODO different colors...
            ax.plot(list(map(float, d["diffusion_tensor"]["time"][minTime : maxTime])), list(map(float, d["diffusion_tensor"][c][minTime : maxTime])), color="black",  marker=".")
      
      ax.plot()
    elif self.x == TUBE_SPACING:
      for d in self.data:
        ax.plot(float(d["mesh_input"]["cnt intertube spacing [nm]"]), 1)
    elif self.x == QUENCHING_SITE_DENSITY:
      for d in self.data:
        ax.plot(float(d["input"]["density of quenching sites"]), 1)
    elif self.x == TEMPERATURE:
      for d in self.data:
        ax.plot(float(d["input"]["temperature [kelvin]"]), 1)
    elif self.x == RELATIVE_PERMITTIVITY:
      for d in self.data:
        ax.plot(float(d["input"]["relative permittivity"]), 1)

    fig.show()
    return fig
  
  # end createPlot

  def outputPlot(self):
    '''
    Creates and outputs this plot.
    '''
    
    self.createPlot().show()
  
  # end savePlot
    
  def savePlot(self, d, n):
    '''
    Creates and saves this plot to directory d.
    
    Parameters:
      d (str): path to directory plot will be saved in
      n (int): number identifying this as the nth plot, used in output filename
    '''
    
    self.createPlot().savefig(os.path.join(d, "plot" + str(n)))
  
  # end savePlot

#end plotObj

if __name__ == '__main__':
  main()
