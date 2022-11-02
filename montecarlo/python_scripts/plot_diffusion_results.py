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
AVG_DISP_SQ_COEFFICIENTS = ["x", "y", "z"]

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
  
  input_val = input()
  while len(input_val) != 0 and input_val[0] == "#":
    input_val = input()
    
  l.append(input_val)
  return input_val

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
    input_val = take_input(ins)
    
    if (input_val == "" and len(directories) != 0):
      break;
    elif not os.path.exists(input_val):
      prompt("Not a valid path!", ins)
    elif os.path.isfile(input_val):
      prompt("Path was to a file, not the directory!", ins)
    elif not os.access(input_val, os.R_OK):
      prompt("Cannot read path!", ins)
    elif not os.path.exists(os.path.join(input_val, "input.json")):
      prompt("Directory doesn't contain input.json!", ins)
    elif not os.path.exists(os.path.join(input_val, "mesh_input.json")):
      prompt("Directory doesn't contain mesh_input.json!", ins)
    elif not os.path.exists(os.path.join(input_val, "particle_diffusion_length.dat")):
      prompt("Directory doesn't contain diffusion length data file, particle_diffusion_length.dat!", ins)
    elif not os.path.exists(os.path.join(input_val, "particle_diffusion_tensor.dat")):
      prompt("Directory doesn't contain diffusion tensor data file, particle_diffusion_tensor.dat!", ins)
    elif (input_val != ""):
      directories.append(os.path.abspath(input_val)) # standard directory format, so duplicates can be identified
  # end while

  directories = list(set(directories)) #remove duplicate paths
  data = []
  
  for d in directories:
    f0 = open(os.path.join(d, "input.json"))
    f1 = open(os.path.join(d, "mesh_input.json"))
    f2 = open(os.path.join(d, "particle_displacement.avg.squared.dat"))
    f3 = open(os.path.join(d, "particle_diffusion_tensor.dat"))
    f4 = open(os.path.join(d, "particle_diffusion_length.dat"))
              
    data.append({"set": len(data),
                 "input": json.loads(f0.read()),
                 "mesh_input": json.loads(f1.read()),
                 "avg_displacement_squared": pd.read_csv(f2, comment="#"),
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
  x_axis = 0
  y_axis = []
  
  # TODO: make x-axis selectable as either time or some quantity from
  # x-axis: time, tube spacing, quenching site density | temperature, permittivity
  # y-axis:
  # data points: random/parallel, single/bundle, chirality (6,5), (8,7), diffusion tensor coefficients
  #   diffusion length, lifetime ;
  # Maybe preview plot and then have option for editing???
  
  # loop broken internally by os.exit
  while 1:
    prompt("Creating Plot " + str(len(plots) + 1), ins)
    
    # prompt user for data directories to use in this plot
    for i in range(len(directories)):
      prompt(str(i) + " " + directories[i] + ("" if i == (len(directories) - 1) else "\n"), ins)

    used_directory_indices = []
    used_data = []

    prompt("Enter directories to plot data from (enter numbers given in above list, on one space-separated line):", ins)
    while len(used_directory_indices) == 0:
      input_val = take_input(ins);
      
      for i in input_val.split():
        try:
          i = int(i)
        except:
          i = -1;
        if i > -1 and i < len(directories):
          used_directory_indices.append(i)
        else:
          prompt(str(i) + " was not a valid selection! (-1 may indicate a non-integer input was entered)", ins)

    used_directory_indices = list(set(used_directory_indices)) # remove duplicates
    
    for i in used_directory_indices:
      used_data.append(data[i])

    # prompt for data to graph on x-axis
    input_val = -1
    
    while input_val < 0 or input_val > 4:
      prompt("0  time\n1  tube spacing\n2  quenching site density\n3  temperature\n4  relative permittivity", ins)
      prompt("Enter data to plot on x-axis (enter a single number given in above list):", ins)
      input_val = take_input(ins)
      try:
        input_val = int(input_val)
      except:
        input_val = -1
    # end while
    
    x_axis = input_val

    # prompt for data to graph on y-axis (only two selections possible, since we can only have 2 y-axes...)
    input_val = -1
    prompt("0 average displacement squared \n1 diffusion tensor\n2 diffusion length (final for each particle, not over time)", ins)
    prompt("Enter data to plot on y-axis (enter up to two numbers given in above list, on one space-separated line):", ins)
    
    while len(y_axis) == 0:
      input_val = take_input(ins)

      for i in input_val.split():
        if len(y_axis) > 2:
          break
        try:
          i = int(i)
        except:
          i = -1
        
        if i > -1 and i < 3:
          if not i in y_axis:
            y_axis.append(i)
        else:
          prompt(str(i) + " was not a valid selection! (-1 may indicate a non-integer input was entered)", ins)
    # end while

    if x_axis == TIME and DIFFUSION_LENGTH in y_axis:
      prompt("Can't plot diffusion length over time, data is per particle", ins)
      y_axis.remove(DIFFUSION_LENGTH)

    # prompt for (direction) coefficients to use if plotting avg displacement squared
    if AVG_DISPLACEMENT_SQUARED in y_axis:
      while not any(i in y_axis for i in AVG_DISP_SQ_COEFFICIENTS):
        prompt("Enter avg displacement squared direction elements to plot (single line, space separated, x, y, z))", ins)
        input_val = take_input(ins)
        
        for c in map(str.lower, input_val.split()):
          if c in AVG_DISP_SQ_COEFFICIENTS:
            if "D" + c in y_axis:
              y_axis.append(c)
          else:
            prompt(c + " was not a valid coefficient", ins)
    # end if
    
    # prompt for diffusion tensor coefficients to use if plotting tensor
    if DIFFUSION_TENSOR in y_axis:
      while not any(i in y_axis for i in DIFFUSION_TENSOR_COEFFICIENTS):
        prompt("Enter tensor elements to plot (single line, space separated, xx xy xz yy yz zz))", ins)
        input_val = take_input(ins)
        
        for c in map(str.lower, input_val.split()):
          if "D" + c in DIFFUSION_TENSOR_COEFFICIENTS:
            if not "D" + c in y_axis:
              y_axis.append("D" + c)
          else:
            prompt(c + " was not a valid coefficient", ins)
    # end if

    prompt("Plot title:", ins)
    plots.append(plotObj(take_input(ins), x_axis, y_axis, used_data))

    plots[len(plots) - 1].output_plot()
    # TODO prompt for graphical adjustments to graph
    
    prompt("All plots created? (Y/y to exit plot menu)", ins)
    
    input_val = take_input(ins).upper()
    if len(input_val) == 1 and input_val[0] == "Y":
      break
  # end while

  # Prompt for properties of data sets to differentiate in data points

  # Prompt for directory to plot data in
  save_directory = "."
  
  while 1:
    prompt("Directory to save plots to (be careful, will overwrite previous plot files if present):", ins)
    save_directory = take_input(ins)

    if not os.path.exists(save_directory):
      try:
        os.mkdir(save_directory)
        prompt("Created directory " + save_directory, ins)
        break
      except:
        prompt("Not a valid path or otherwise couldn't create it!!", ins)
    elif os.path.isfile(input_val):
      prompt("Path was to a file, not the directory!", ins)
    elif not os.access(save_directory, os.W_OK):
      prompt("Cannot write to " + save_directory, ins)
    else:
      prompt("Saving to " + save_directory, ins)
      break
  # end while

  # save all plots
  for p in range(len(plots)):
    plots[p].save_plot(save_directory, p)

  # write all input arguments (with prompts as comments) to file for reuse
  saved_input_file = open(os.path.join(save_directory, "input.log"), "w")
  saved_input_file.write("\n".join(ins) + "\n")
  saved_input_file.close()

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
    
  def create_plot(self):
    '''
    Creates this plot.

    Returns:
      This plot as mpl figure.
    '''
    
    fig = plt.figure()
    ax = fig.subplots()
    if DIFFUSION_TENSOR in self.y and AVG_DISPLACEMENT_SQUARED in self.y:
      # used if two types of y data plotted
      ax2 = ax.twinx() 
    ax.set_title(self.title)
    avg_disp_coeffs = list(set(AVG_DISP_SQ_COEFFICIENTS).intersection(self.y))
    tensor_coeffs = list(set(DIFFUSION_TENSOR_COEFFICIENTS).intersection(self.y))
    
    # used for point data types (avg displacement, certain tensor coeff, etc) and data sets, respectively
    pt_colors = ["black", "blue", "orange", "green", "gray", "magenta", "maroon", "yellow", "turquoise"]
    pt_markers = [".", "x", "d", "o", "s", "+", "|", "v", "1", "^", "3", "*", "2", "<", "4", ">"]

    used_pt_colors = {}
    used_pt_markers = {}

    # diffusion length and tensor are not themselves plotted, their coefficients are, so don't assign them colors
    y_plotted_only = self.y.copy()
    if DIFFUSION_TENSOR in y_plotted_only:
      y_plotted_only.remove(DIFFUSION_TENSOR)
    if AVG_DISPLACEMENT_SQUARED in y_plotted_only:
      y_plotted_only.remove(AVG_DISPLACEMENT_SQUARED)
    
    for i in range(len(y_plotted_only)):
      # modulus for safety but there should never be more than 9
      used_pt_colors.update({y_plotted_only[i]: pt_colors[i % len(pt_colors)]})

    for i in range(len(self.data)):
      # modulus for safety, possible to plot more than 16 data sets but please don't
      used_pt_markers.update({self.data[i]["set"]: pt_markers[i % len(pt_markers)]})
    
    # TODO calculate average final values when not plotting over time
    if self.x != TIME:
        pass
    
    if self.x == TIME:
      plt.xlabel("Time [s]")

      for d in self.data:
        curr_ax = ax
        t = list(map(float, d["diffusion_tensor"]["time"]))
        
        if AVG_DISPLACEMENT_SQUARED in self.y:
          for c in avg_disp_coeffs:
            curr_ax.plot(t, list(map(float, d["avg_displacement_squared"][c])), color=used_pt_colors[c],
                         marker=used_pt_markers[d["set"]], markersize="5", fillstyle="none")
          curr_ax = ax2

        if DIFFUSION_TENSOR in self.y:
          for c in tensor_coeffs:
            curr_ax.plot(t, list(map(float, d["diffusion_tensor"][c])), color=used_pt_colors[c],
                         marker=used_pt_markers[d["set"]], markersize="5", fillstyle="none")
      
    else:
      # final vales for diffusion tensor coeffs, avg displacement coeffs, averages for diffusion length
      
      if self.x == TUBE_SPACING:
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
  
  # end create_plot

  def output_plot(self):
    '''
    Creates and outputs this plot.
    '''
    
    self.create_plot().show()
  
  # end save_plot
    
  def save_plot(self, d, n):
    '''
    Creates and saves this plot to directory d.
    
    Parameters:
      d (str): path to directory plot will be saved in
      n (int): number identifying this as the nth plot, used in output filename
    '''
    
    self.create_plot().savefig(os.path.join(d, "plot" + str(n)))
  
  # end save_plot

#end plotObj

if __name__ == '__main__':
  main()
