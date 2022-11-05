import math
import os
import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import pandas as pd

# X-AXIS GLOBALS
TIME                   = 0
TUBE_SPACING           = 1
QUENCHING_SITE_DENSITY = 2
TEMPERATURE            = 3
RELATIVE_PERMITTIVITY  = 4

# keys for data set dict to reach x value for given
# 
X_KEYS = [None, ("mesh_input", "cnt intertube spacing [nm]"),
          ("input", "density of quenching sites"),
          ("input", "temperature [kelvin]"),
          ("input", "relative permittivity")]

# Y-AXIS GLOBALS
AVG_DISPLACEMENT_SQUARED      = 0
DIFFUSION_TENSOR              = 1
DIFFUSION_TENSOR_COEFFICIENTS = ["Dxx", "Dxy", "Dxz", "Dyy", "Dyz", "Dzz"]
AVG_DISP_SQ_COEFFICIENTS      = ["x", "y", "z"]
DIFFUSION_LENGTH              = 2

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

def remove_duplicates(l):
  '''
    Remove all but the first instance of each element in a list.

    Parameters:
      l (list): list to remove duplicates from (is modified)
  
    Returns:
      none
  '''
  
  new_l = []
  
  for i in l:
    if not i in new_l:
      new_l.append(i)

  l[:] = new_l

# end remove_duplicates


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
      break
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

  remove_duplicates(directories)
  data = []
  
  for d in directories:
    f0 = open(os.path.join(d, "input.json"))
    f1 = open(os.path.join(d, "mesh_input.json"))
    f2 = open(os.path.join(d, "particle_displacement.avg.squared.dat"))
    f3 = open(os.path.join(d, "particle_diffusion_tensor.dat"))
    f4 = open(os.path.join(d, "particle_diffusion_length.dat"))
              
    data.append({"input": json.loads(f0.read()),
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

  
  # Maybe preview plot and then have option for editing???
  
  # loop broken internally
  while 1:
    prompt("Creating Plot " + str(len(plots) + 1), ins)
    
    # prompt user for data directories to use in this plot
    for i in range(len(directories)):
      prompt(str(i) + " " + directories[i], ins)

    used_directory_indices = []
    used_data = []

    prompt("Enter directories to plot data from (enter numbers given in above list, on one space-separated line):", ins)
    while len(used_directory_indices) == 0:
      input_val = take_input(ins)
      
      for i in input_val.split():
        try:
          i = int(i)
        except:
          i = -1
        if i > -1 and i < len(directories):
          used_directory_indices.append(i)
        else:
          prompt(str(i) + " was not a valid selection! (-1 may indicate a non-integer input was entered)", ins)

    remove_duplicates(used_directory_indices)
    
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
            if not c in y_axis:
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

    # currently plots all diffusion length coefficients

    prompt("Plot title:", ins)
    plots.append(plotObj(take_input(ins), x_axis, y_axis, used_data))

    plots[-1].output_plot()
    # TODO prompt for graphical adjustments to graph
    
    prompt("All plots created? (Y/y to exit plot menu)", ins)
    
    input_val = take_input(ins).upper()
    if len(input_val) == 1 and input_val[0] == "Y":
      break
  # end while

  # prompt for plot output directory
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

  # write all input arguments (with prompts as comments) to file in output directory for reuse
  saved_input_file = open(os.path.join(save_directory, "input.log"), "w")
  saved_input_file.write("\n".join(ins) + "\n")
  saved_input_file.close()

  # also save input file to current directory
  saved_input_file = open("./last_input.log", "w")
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
      data (list of dicts): the simulation output data sources from which to plot
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
    
    fig = plt.figure(figsize=[8,6])
    ax = fig.subplots()
    ax2 = ax
    if DIFFUSION_TENSOR in self.y and AVG_DISPLACEMENT_SQUARED in self.y:
      # used if two types of y data plotted
      ax2 = ax.twinx() 
    ax.set_title(self.title)

    # isolate coefficient specifiers from y-axis sets list
    avg_disp_coeffs = list(set(AVG_DISP_SQ_COEFFICIENTS).intersection(self.y))
    avg_disp_coeffs.sort() # won't be the order the user specified, but at least it will be consistent
    tensor_coeffs = list(set(DIFFUSION_TENSOR_COEFFICIENTS).intersection(self.y))
    tensor_coeffs.sort()

    # classify data sets on the basis of everything but the x-axis variable (if x-axis variable something
    # other than time) so that data sets with the same parameters aren't plotted as distinct
    # do not classify by parameters which only take one value across all data sets
    seen_params = {"cnt chirality": [], "bundle": [], "parallel": [],
                   TUBE_SPACING: [], QUENCHING_SITE_DENSITY: [],
                   TEMPERATURE: [], RELATIVE_PERMITTIVITY: []}

    for d in self.data:
      for i in ("cnt chirality", "bundle", "parallel"):
        if not d["mesh_input"][i] in seen_params[i]:
          seen_params[i].append(d["mesh_input"][i])
      for i in range(len(X_KEYS)):
        if X_KEYS[i] != None and i != self.x and not d[X_KEYS[i][0]][X_KEYS[i][1]] in seen_params[i]:
          seen_params[i].append(d[X_KEYS[i][0]][X_KEYS[i][1]])
    # end for
    
    data_set_classes = []
    
    for d in self.data:
      data_set_class = ""
      
      for i in ("cnt chirality", "bundle", "parallel"):
        if len(seen_params[i]) > 1:
          data_set_class += str(d["mesh_input"][i]) + " "
      
      for i in range(len(X_KEYS)):
        if X_KEYS[i] != None and i != self.x and len(seen_params[i]) > 1:
          data_set_class += str(d[X_KEYS[i][0]][X_KEYS[i][1]]) + " "

      d.update({"set": data_set_class})
      
      if not data_set_class in data_set_classes:
        data_set_classes.append(data_set_class)
    # end for

    # diffusion length has three coefficients. prefixed with dl_ so as not to conflict with displacement coeffients
    # TODO seems to add wtice, see what's up with that
    if DIFFUSION_LENGTH in self.y:
      self.y.extend(["dl_x", "dl_y", "dl_z"])

    # displacement and diffusion length and tensor are not themselves plotted, their coefficients are
    # so don't assign them colors
    y_plotted_only = self.y.copy()
    if AVG_DISPLACEMENT_SQUARED in y_plotted_only:
      y_plotted_only.remove(AVG_DISPLACEMENT_SQUARED)
    if DIFFUSION_TENSOR in y_plotted_only:
      y_plotted_only.remove(DIFFUSION_TENSOR)
    if DIFFUSION_LENGTH in y_plotted_only:
      y_plotted_only.remove(DIFFUSION_LENGTH)

    # used to distinguish point coefficients, data sets when plotting over time,
    # and data sets when plotting over a different quantity, respectively
    pt_colors  = ["black", "blue", "orange", "green", "gray", "magenta", "maroon", "yellow", "turquoise"]
    linestyles = ["solid", "dashed", "dotted", "dashdot", (0, (5,2,5,2,1,2)), (0,(1,5)), (0, (5,2,1,2,1,2)), (0,(10,5)), (0,(5,10))]
    pt_markers = [".", "x", "d", "o", "s", "+", "|", "v", "1", "^", "3", "*", "2", "<", "4", ">"]

    used_pt_colors  = {}
    used_linestyles = {}
    used_pt_markers = {}
    
    for i in range(len(y_plotted_only)):
      # modulus for safety but there should never be more than 9
      # (maximum 6 tensor coefficients plus maximum 3 from diffusion length or avg displacement sq)
      used_pt_colors.update({y_plotted_only[i]: pt_colors[i % len(pt_colors)]})

    for i in range(len(data_set_classes)):
      # different linestyles used for multiple data sets when plotting over time.
      # modulus for safety, possible to plot more than 9 data sets but please don't do that
      # when plotting over time.
      used_linestyles.update({data_set_classes[i]: linestyles[i % len(linestyles)]})

    for i in range(len(data_set_classes)):
      # modulus for safety but there should never be more than 9
      used_pt_markers.update({data_set_classes[i]: pt_markers[i % len(pt_markers)]})

    ax.legend(handles=[mpatches.Patch(color=used_pt_colors[c], label=c) for c in y_plotted_only], loc="upper right")
    ax.add_artist(ax.get_legend())
    
    if self.x == TIME:
      ax.legend(handles=[mlines.Line2D([], [], linestyle=used_linestyles[s], label=s) for s in data_set_classes], loc="upper left")
      
      # if plotting over time: list of time values vs list of data values can be plotted directly
      ax.set_xlabel("Time [s]")
      
      for d in self.data:
        curr_ax = ax
        
        t = list(map(float, d["diffusion_tensor"]["time"]))
        
        if AVG_DISPLACEMENT_SQUARED in self.y:
          ax.set_ylabel("Average Displacement Squared [m^2]")
          
          for c in avg_disp_coeffs:
            curr_ax.plot(t, list(map(float, d["avg_displacement_squared"][c])), color=used_pt_colors[c],
                         marker="None", linestyle=used_linestyles[d["set"]])
          curr_ax = ax2

        if DIFFUSION_TENSOR in self.y:
          curr_ax.set_ylabel("Diffusion Tensor Element [m^2 / s]")
          
          for c in tensor_coeffs:
            curr_ax.plot(t, list(map(float, d["diffusion_tensor"][c])), color=used_pt_colors[c],
                         marker="None", linestyle=used_linestyles[d["set"]])
      # end for
      
    else:
      ax.legend(handles=[mlines.Line2D([], [], marker=used_pt_markers[s], label=s) for s in data_set_classes], loc="upper left")
      print(used_pt_colors)
      
      # final vales for diffusion tensor coeffs, avg displacement coeffs, averages for diffusion length
      # (final values for coefficients taken as average of latter half of data, which is generally
      # accurate if there are no quenching sites to continally decrease them)
      for d in self.data:
        if AVG_DISPLACEMENT_SQUARED in self.y:
          for c in avg_disp_coeffs:
            count = 0
            total = 0
            
            for v in d["avg_displacement_squared"][c][int(len(d["avg_displacement_squared"]["time"]) / 2):]:
              if not math.isnan(v):
                count += 1
                total += v
            d.update({"ads_" + c + "_final": total / count})
        
        if DIFFUSION_TENSOR in self.y:
          for c in tensor_coeffs:
            count = 0
            total = 0
            
            for v in d["diffusion_tensor"][c][int(len(d["diffusion_tensor"]["time"]) / 2):]:
              if not math.isnan(v):
                count += 1
                total += v
            d.update({"dt_" + c + "_final": total / count})
        
        if DIFFUSION_LENGTH in self.y:
          for c in ("x", "y", "z"):
            count = 0
            total = 0
            
            for v in d["diffusion_length"][c]:
              if isinstance(v, float): #NAN check (parsed nans remain strings...)
                count += 1
                total += abs(v)

            count += 1 if count == 0 else 0 # prevent division by 0
            d.update({"dl_" + c + "_avg": total / count})
      # end for

      x_key_0 = X_KEYS[self.x][0]
      x_key_1 = X_KEYS[self.x][1]

      # if plotting over a property specified in the mesh generation/simulation properties:
      # points are plotted one by one (one for each simulation output/y-data set pair)
      for d in self.data:
        curr_ax = ax
        
        if AVG_DISPLACEMENT_SQUARED in self.y:
          for c in avg_disp_coeffs:
            ax.plot(float(d[x_key_0][x_key_1]), d["ads_" + c + "_final"], color=used_pt_colors[c],
                    marker=used_pt_markers[d["set"]], markersize="8", fillstyle="none")
          curr_ax = ax2
          
        if DIFFUSION_TENSOR in self.y:
          for c in tensor_coeffs:
            ax.plot(float(d[x_key_0][x_key_1]), d["dt_" + c + "_final"], color=used_pt_colors[c],
                    marker=used_pt_markers[d["set"]], markersize="8", fillstyle="none")
          curr_ax = ax2
          
        if DIFFUSION_LENGTH in self.y:
          for c in ("dl_x", "dl_y", "dl_z"):
            ax.plot(float(d[x_key_0][x_key_1]), d[c + "_avg"], color=used_pt_colors[c],
                    marker=used_pt_markers[d["set"]], markersize="8", fillstyle="none")
      # end for
      
    # end else

    fig.tight_layout()
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
