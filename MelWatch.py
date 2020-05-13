# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 22:16:24 2017

@author: ejb279
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.backends.backend_tkagg
import tkinter.filedialog
import math
import time
import msvcrt
import re

# this is a re-implementation of matplotlib.pyplot.pause() that doesn't call show()
# because show() pulls focus to the window and I don't want that. Found on stackexchange.
def mypause(interval):
    backend = plt.rcParams['backend']
    if backend in matplotlib.rcsetup.interactive_bk:
        figManager = matplotlib._pylab_helpers.Gcf.get_active()
        if figManager is not None:
            canvas = figManager.canvas
            if canvas.figure.stale:
                canvas.draw()
            canvas.start_event_loop(interval)
            return


# A version of input() that times out if the user waits too long.
# I'm using this as an alternative to time.sleep() that can be interrupted.
# Found on the internet and modified.
class TimeoutExpired(Exception):
    pass
def input_with_timeout(prompt, timeout, timer=time.monotonic):
    sys.stdout.write(prompt)
    sys.stdout.flush()
    endtime = timer() + timeout
    result = []
    while timer() < endtime:
        if msvcrt.kbhit():
            result.append(msvcrt.getwche()) #XXX can it block on multibyte characters?
            # print(result)
            if result[-1] == '\n':   #XXX check what Windows returns here
                return ''.join(result[:-1])
            else:
                return result
        time.sleep(0.01) # just to yield to other processes/threads
        mypause(0.001)
    raise TimeoutExpired




class MelWatch(object):
    def __init__(self, config_file):
        
        
        # MELCOR plot variables listed in config file
        self.plot_vars = []
        self.plot_vars_on = []
        self.pltvar_titles = []
        self.pltvar_pointers = []
        self.pltvar_units = []
        self.pltvar_scale = []
        self.pltvar_offset = []
        
        # horizontal lines defined in config file
        self.hlines = []
        self.hlines_on = []
        self.hline_titles = []
        self.hline_units = []
        
        # formulas defined in config file
        self.formulas = []
        self.formulas_on = []
        self.formula_titles = []
        self.formula_units = []
        
        self.plotfile = ""
        
        self.plots_pltvars = [] # list of the indices for the plot variables that go in each plot
        self.plots_formulas = []    # same for formulas
        self.plots_hlines = []      # same for horizontal lines
        self.plot_titles = []
        self.plot_limits = []
        self.plot_tail = []
        self.plot_all_tails = False
        self.default_tail = 100 # default max number of plot points to plot if "tail" is requested in the config file
        self.t_unit = False
        
        self.write_vars = False
        self.first_header = True
        # num_lines = 0
        # self.line_values = [0.]
        
        # Read the config file
        try:
            if config_file.endswith("ptf"): # if the command line option is a ptf file, not a config file, 
                # then write all the plot variables in that ptf to a text file.
                print("No config file. Writing available plot variables to plot_variables.txt")
                self.write_vars = True
                self.plotfile = config_file
            else:
                # Open the config file
                with open(config_file, 'r') as conf:
                    line = conf.readline()
                    # Skip blanks and comments
                    while len(line.split()) == 0 or line.split()[0].startswith('!'):
                        line = conf.readline()
                    spl = line.split()
                    # First real line starts with the plotfile name
                    if spl[0].startswith('"'):  # in case somebody is using filenames with spaces in them
                        self.plotfile = line.split('"')[1]
                    else:
                        self.plotfile = spl[0]
                    if "tail" in line.split('!')[0].split():   # if tail is in the first line, it applies to all plots
                        try:
                            self.plot_all_tails = int(spl[spl.index("tail")+1]) # see if it lists a number after tail, if so that's the number of points to plot
                        except:
                            self.plot_all_tails = self.default_tail # otherwise use the default number of tail points
                    if "t_unit" in spl:
                        try:
                            self.t_unit = spl[spl.index("t_unit")+1] # see if it lists a time unit (seconds or hours)
                        except:
                            self.t_unit = False # otherwise let the plot routine decide
                    # anything else in the first line gets ignored
                    print("Plots to be generated:")
                    for line in conf.readlines():
                        spl = line.split()
                        if len(spl) == 0 or spl[0].startswith('!'): # skip blanks and comments
                            continue
                        # cut off end-of-line comments
                        if not spl[0].startswith("formula"): # formulas might have good reason to contain !, so it's not treated as starting a comment there.
                            line = line.split("!")[0]
                            spl = line.split()
                        if spl[0].startswith("plot"):   # definition of a new plot, which can contain many curves
                            self.plots_pltvars.append([])   # self.plots_pltvars gets a new entry, which is a list of MELCOR plot variables that go on this plot
                            self.plots_formulas.append([])  # list of formulas that go on this plot
                            self.plots_hlines.append([])    # list of horizontal lines that go on this plot
                            # print(line)
                            
                            if '"' in line:     # look for the plot title in quotes
                                spl2 = line.split('"')
                                self.plot_titles.append(spl2[1])
                                print("\t",spl2[1])
                            else:   # or use a default title
                                self.plot_titles.append("Plot " + str(len(self.plots_pltvars)))
                                print("\tPlot "+ str(len(self.plots_pltvars)))
                            
                            # Check for user-defined axis boundaries
                            limits = None
                            if "xmin" in spl:
                                xmin = float(spl[spl.index("xmin")+1])
                            else:
                                xmin = None
                            if "ymin" in spl:
                                ymin = float(spl[spl.index("ymin")+1])
                            else:
                                ymin = None
                            if "xmax" in spl:
                                xmax = float(spl[spl.index("xmax")+1])
                            else:
                                xmax = None
                            if "ymax" in spl:
                                ymax = float(spl[spl.index("ymax")+1])
                            else:
                                ymax = None
                            limits = [xmin, xmax, ymin, ymax]
                            self.plot_limits.append(limits)
                            
                            # Check for a request to tail just in this plot
                            if "tail" in spl:
                                try:
                                    self.plot_tail.append(int(spl[spl.index("tail")+1]))
                                except:
                                    self.plot_tail.append(self.default_tail)
                            else:   # if nothing specific to this plot, use the one from the first line, if any
                                self.plot_tail.append(self.plot_all_tails)
                        
                        # We've come to a line that isn't a plot heading, so it's a curve.
                        # It could be a MELCOR plot variable, a horizontal line definition, or a formula definition.
                        else:
                            # if no plots are defined, make one for this curve to go into
                            if len(self.plots_pltvars) == 0 and len(self.plot_vars) == 0:
                                self.plots_pltvars.append([])
                                self.plots_formulas.append([])
                                self.plots_hlines.append([])
                                self.plot_titles.append("Plot 0")
                                self.plot_limits.append(None)
                            
                            # get title, which must be short and have no spaces
                            if len(spl) > 1:
                                title = spl[1]
                            else:
                                title = spl[0]
                            
                            # if it's a formula definition
                            if spl[0].startswith("formula"):
                                # title is in quotes for formulas
                                if '"' in line:
                                    spl2 = line.split('"')
                                    self.formula_titles.append(spl2[1])
                                else:
                                    self.formula_titles.append(spl[0])
                                
                                self.formulas.append(spl2[3]) # the meat of the formula definition, after the title, also in quotes
                                if "off" in spl:
                                    self.formulas_on.append(False)
                                else:
                                    self.formulas_on.append(True)
                                
                                if "units" in spl:
                                    self.formula_units.append(spl[spl.index("units")+1])
                                else:
                                    self.formula_units.append("")
                                if self.formulas_on[-1]:
                                    self.plots_formulas[-1].append(len(self.formulas) - 1)
                            
                            # if it's a horizontal line definition
                            elif spl[0].startswith("hline,"):
                                self.hlines.append(float(spl[0].split(',')[1])) # the vertical position of the line
                                self.hline_titles.append(title)
                                if "off" in spl:
                                    self.hlines_on.append(False)
                                else:
                                    self.hlines_on.append(True)
                                if "units" in spl:
                                    self.hline_units.append(spl[spl.index("units")+1])
                                else:
                                    self.hline_units.append("")
                                if self.hlines_on[-1]:
                                    self.plots_hlines[-1].append(len(self.hlines) - 1)
                            
                            # Otherwise, assume it's a MELCOR plot variable
                            else:
                                self.plot_vars.append(spl[0])
                                self.pltvar_titles.append(title)
                                self.pltvar_pointers.append(-1) # this will get updated when we find the variable in the plotfile
                                if "off" in spl:
                                    self.plot_vars_on.append(False)
                                else:
                                    self.plot_vars_on.append(True)
                                if "scale" in spl:
                                    self.pltvar_scale.append(float(spl[spl.index("scale")+1]))
                                else:
                                    self.pltvar_scale.append(1.0)
                                if "offset" in spl:
                                    self.pltvar_offset.append(float(spl[spl.index("offset")+1]))
                                else:
                                    self.pltvar_offset.append(0.0)
                                if "units" in spl:
                                    self.pltvar_units.append(spl[spl.index("units")+1])
                                else:
                                    self.pltvar_units.append("")
                                if self.plot_vars_on[-1]:
                                    self.plots_pltvars[-1].append(len(self.plot_vars) - 1)
        except IOError:
            print("Could not open config file " + config_file)

        if len(self.plots_pltvars) > 15:
            print("Too many plots, limit yourself to 12 or 15 per config file.")
            sys.exit(0)

        self.t = np.zeros(50000,dtype=np.float32) # I've yet to encounter a ptf file with
                                    # more than 50k points in it.
        self.dt = np.zeros(50000,dtype=np.float32)
        self.cpu = np.zeros(50000,dtype=np.float32)
        self.ncycle = np.zeros(50000,dtype=np.uint32)

        # Read in the whole plotfile
        self.n = 0 # the number of the plot point we're reading

        # Make arrays to hold the data points of each variable we're plotting
        self.data_arrays = []
        for ind in range(len(self.plot_vars)):
            self.data_arrays.append(np.zeros(50000,dtype=np.float32))

        self.variable_names = [] # list of all the variable names in the plotfile
        self.pointers = []       # list of pointers to each variable name in the data
        self.var_units = []      # list of units associated with each variable name in the plotfile
        self.nid = []            # list of component numbers for the actual plot data
        self.var_names_combined = []    # this will combine the variable name and component num,
        # so that it can be compared with the names of variables to plot from self.plot_vars
        self.datavar_units = []  # lists the units associated with each entry in self.plot_vars

        self.time_indep_string_array = []
        self.spot = 0

        with open(self.plotfile, 'rb') as ptf:
            self.update_variables(ptf, 0)
            # print("Spot is ", self.spot)
            
    def update_variables(self, ptf, spot):
        ptf.seek(spot)
        remaining = int.from_bytes(ptf.read(4), byteorder="little")
        # print("Remaining: ", remaining)
        # print(ptf.read(100))
        answer = ""
        while remaining == 0:
            # timeout = 10
            # tm = Timer(timeout, print, ['.'])
            # tm.start()
            try:
                answer = input_with_timeout(".", 2)
                # print(answer)
                if 'p' in answer:
                    answer2 = ""
                    print(" Press any key to unpause.")
                    while answer2 == "":
                        try:
                            answer2 = input_with_timeout("", 0.5)
                        except TimeoutExpired:
                            pass
                    # print("now")
                    answer = ""
                if answer:
                    print("\nExiting.\n")
                    sys.exit(0)
            except TimeoutExpired:
                ptf.seek(spot)
                remaining = int.from_bytes(ptf.read(4), byteorder="little")
                # print(spot, remaining)
        assert(remaining == 4)
        flag = ptf.read(4)
        if flag == b"./*/":
            self.read_header(ptf)
        else:
            numnum = int.from_bytes(ptf.read(4), byteorder="little")
            assert(numnum == 4)
            lenplt = int.from_bytes(ptf.read(4), byteorder="little")
            assert(lenplt == self.len_plt_point)


        # check if the user asked for any variables that aren't in the data
        missing = 0
        ncycle_in_pltvars = False
        for ind in range(len(self.plot_vars)):
            if self.pltvar_pointers[ind] < 0:
                missing += 1
            if self.pltvar_pointers[ind] == 2:
                ncycle_in_pltvars = True
        if missing > 0:
            print("Warning: not all plot variables requested are present.")

        # Read in the plot points
        more_points = True
        while more_points and self.n < 50000:
            # print("Before: ", ptf.tell())
            point = ptf.read(self.len_plt_point)
            # print("After: ", ptf.tell())
            self.t[self.n] = np.fromstring(point[0:4], dtype=np.float32)
            self.dt[self.n] = np.fromstring(point[4:8], dtype=np.float32)
            self.cpu[self.n] = np.fromstring(point[8:12], dtype=np.float32)
            self.ncycle[self.n] = int.from_bytes(point[12:16], byteorder="little")

            if missing > 0: # then we have to check if each one is okay before reading it
                for ind in range(len(self.plot_vars)):
                    if self.pltvar_pointers[ind] < 0:
                        self.data_arrays[ind][self.n] = 0.
                        if self.n < 1:
                            print("Error, can't find one of these plot variables in the data -- #", ind)
                    # elif self.pltvar_pointers[ind] < 0:
                        # self.data_arrays[ind][self.n] = self.line_values[-1*self.pltvar_pointers[ind]]
                    else:
                        start = self.pltvar_pointers[ind]*4+4
                        self.data_arrays[ind][self.n] = np.fromstring(point[start:start+4], dtype=np.float32)
                    
                    # ncycle is special: unlike all other plot variables, it has to be read as an integer, not a float
                    if self.pltvar_pointers[ind] == 2 and self.plot_vars[ind] == "ncycle":
                        self.data_arrays[ind][self.n] = int.from_bytes(point[start:start+4], byteorder="little")
            
            elif ncycle_in_pltvars: # then we have to check whether to read each one as an int instead of a float
                for ind in range(len(self.plot_vars)):
                    start = self.pltvar_pointers[ind]*4+4
                    self.data_arrays[ind][self.n] = np.fromstring(point[start:start+4], dtype=np.float32)
                    if self.pltvar_pointers[ind] == 2 and self.plot_vars[ind] == "ncycle":
                        self.data_arrays[ind][self.n] = int.from_bytes(point[start:start+4], byteorder="little")
            
            # the idea here is to speed up the inner loop in the most common situation
            # by eliminating unnecessary checks beforehand.
            else: 
                for ind in range(len(self.plot_vars)):
                    start = self.pltvar_pointers[ind]*4+4
                    self.data_arrays[ind][self.n] = np.fromstring(point[start:start+4], dtype=np.float32)
            
            num1 = int.from_bytes(ptf.read(4), byteorder="little")
            assert(num1 == self.len_plt_point)
            
            # See if there's another plot point after that one.
            numnum = int.from_bytes(ptf.read(4), byteorder="little")
            if numnum == 4: # This is not the end of the file.
                flag = ptf.read(4)
                if not flag == b'.TR/':
                    #print(flag)
                    #print(ptf.read(64).decode())
                    print("Reading header again at restart point, t=" + str(self.t[self.n]) + ", ncycle=" + str(self.ncycle[self.n]))
                    self.read_header(ptf)
                    numnum = int.from_bytes(ptf.read(4), byteorder="little")
                    assert(numnum == 4)
                    lenplt = int.from_bytes(ptf.read(4), byteorder="little")
                    assert(lenplt == self.len_plt_point)
                else:
                    numnum = int.from_bytes(ptf.read(4), byteorder="little")
                    assert(numnum == 4)
                    lenplt = int.from_bytes(ptf.read(4), byteorder="little")
                    assert(lenplt == self.len_plt_point)
            else:
                # print(numnum)
                assert(numnum == 0)
                more_points = False
                # print("End at ", ptf.tell(), " is ", ptf.read(100))
                print("Done reading plotfile.\tt=" + str(self.t[self.n]) + ", ncycle=" + str(self.ncycle[self.n]), end="")
            self.n += 1
        # Done reading plot points
        self.spot = ptf.tell()
        # ptf.seek(spot - 8)
        # print(ptf.read(100))
        print(". Plot points found:",self.n, end="")
        # File closed

 
    def read_header(self, ptf):
        assert(int.from_bytes(ptf.read(4), byteorder="little") == 4)
        assert(int.from_bytes(ptf.read(4), byteorder="little") == 4)
        assert(ptf.read(4) == b"TITL")
        assert(int.from_bytes(ptf.read(4), byteorder="little") == 4)
        title_length = int.from_bytes(ptf.read(4), byteorder="little")
        title = ptf.read(title_length)
        assert(int.from_bytes(ptf.read(4), byteorder="little") == title_length)
        assert(int.from_bytes(ptf.read(4), byteorder="little") == 4)
        assert(ptf.read(4) == b"./*/")
        assert(int.from_bytes(ptf.read(4), byteorder="little") == 4)
        assert(int.from_bytes(ptf.read(4), byteorder="little") == 4)
        assert(ptf.read(4) == b"KEY ")
        assert(int.from_bytes(ptf.read(4), byteorder="little") == 4)
        num = int.from_bytes(ptf.read(4), byteorder="little") # 4 or 8
        num_vars = int.from_bytes(ptf.read(4), byteorder="little")
        ncomponents = -1
        maybe_num = int.from_bytes(ptf.read(4), byteorder="little")
        if maybe_num == 4:
            print("This file is tranptf output that will not work with PTFread.")
            assert(maybe_num == num)
        else:
            ncomponents = maybe_num
            next_num = int.from_bytes(ptf.read(4), byteorder="little")
            assert(next_num == num)
        len_var_names = int.from_bytes(ptf.read(4), byteorder="little")
        # make sure the length of the variable-names string is divisible by 24.
        var_name_length = 24
        num_var_names = len_var_names / var_name_length
        num_vars = int(num_var_names)
        assert(float(num_vars) == num_var_names)
        if self.first_header:
            self.first_header = False
            print("\n" + str(num_var_names) + " variables in file. \nVariables requested from file:")
        self.variable_names = ["dt", "cpu", "ncycle"]
        # Hard-code the first three, like PTFread does
        # Read in the rest
        for var_string in range(int(num_var_names)):
            self.variable_names.append(ptf.read(var_name_length).decode().strip())
        #print(variable_names[0:50])
        assert(self.variable_names[7] == "Messages-Details")
        assert(self.variable_names[8].startswith("CVH"))
        #print(self.variable_names[-2:])
        assert(int.from_bytes(ptf.read(4), byteorder="little") == len_var_names)
        assert(int.from_bytes(ptf.read(4), byteorder="little") == 4 * num_vars)
        self.pointers = [1, 2, 3]
        for pointer in range(num_vars):
            self.pointers.append(3 + int.from_bytes(ptf.read(4), byteorder="little"))
        assert(int.from_bytes(ptf.read(4), byteorder="little") == 4 * num_vars)
        unit_string_length = 16
        assert(int.from_bytes(ptf.read(4), byteorder="little") == unit_string_length * num_vars)
        self.var_units = ["s", "s", "cycles"]
        for unit in range(num_vars):
            self.var_units.append(ptf.read(unit_string_length).decode().strip())
        assert(int.from_bytes(ptf.read(4), byteorder="little") == unit_string_length * num_vars)

        # Now read in the list of component numbers
        len_nid = int.from_bytes(ptf.read(4), byteorder="little")
        if ncomponents >= 0:
            assert(len_nid == ncomponents*4)
        else:
            ncomponents = int(len_nid / 4)
        self.nid = [0, 0, 0]
        for component in range(ncomponents):
            self.nid.append(int.from_bytes(ptf.read(4), byteorder="little"))
        self.pointers.append(ncomponents + 4) # maybe this final pointer entry is
        # supposed to get you to the metadata that follows each plot point's
        # list of variable values. PTFread does it.
        assert(int.from_bytes(ptf.read(4), byteorder="little") == len_nid)
        assert(int.from_bytes(ptf.read(4), byteorder="little") == 4)
        flag = ptf.read(4)


        # self.var_names_combined = []
        # self.datavar_units = []
        # var_name_index = 0
        # for datavar in range(self.pointers[-1] - 1):
            # var_name_combined = self.variable_names[var_name_index]
            # if self.nid[datavar] > 0:
                # var_name_combined += "." + str(self.nid[datavar])
            # self.var_names_combined.append(var_name_combined)
            # self.datavar_units.append(self.var_units[var_name_index])
            # if var_name_combined in self.plot_vars:
                # ind = self.plot_vars.index(var_name_combined)
                # self.pltvar_pointers[ind] = datavar
                # self.pltvar_units[ind] = self.var_units[var_name_index]
           
            # if datavar >= self.pointers[var_name_index+1]-2: # move on to the next category
                # var_name_index += 1
           
        # #print(var_names_combined[-20:])
        # print(self.plot_vars)
        # print(self.pltvar_pointers)
        # print(self.pltvar_units)


        if flag == b'.SP/': # otherwise, it should be b'.TR/' and we can just read the next plot point
            # Find pointers to the variables we want to plot
            # Make arrays of variable name, component number, and unit for all
            # of the variables. Well, we already have component number
            self.var_names_combined = []
            self.datavar_units = []
            var_name_index = 0
            for datavar in range(self.pointers[-1] - 1):
                var_name_combined = self.variable_names[var_name_index]
                if self.nid[datavar] > 0:
                    var_name_combined += "." + str(self.nid[datavar])
                # if self.write_vars:
                    # print(datavar, var_name_combined)
                #print(self.nid[datavar])
                self.var_names_combined.append(var_name_combined)
                self.datavar_units.append(self.var_units[var_name_index])
                if var_name_combined in self.plot_vars:
                    print("\t",var_name_combined)
                    ind = self.plot_vars.index(var_name_combined)
                    self.pltvar_pointers[ind] = datavar
                    if len(self.pltvar_units[ind]) == 0: # if it's been set earlier, don't change it
                        self.pltvar_units[ind] = self.var_units[var_name_index]
               
                if datavar >= self.pointers[var_name_index+1]-2: # move on to the next category
                    var_name_index += 1
            
            if self.write_vars: # then we don't need to read the rest of the file
                with open("plot_variables.txt",'w') as f:
                    for datavar in range(self.pointers[-1] - 1):
                        f.write(str(datavar) + " " + self.var_names_combined[datavar] + " " + self.datavar_units[datavar] + "\n")
                sys.exit(0)
            
            #print(var_names_combined[-20:])
            # print(self.plot_vars)
            # print(self.pltvar_pointers)
            # print(self.pltvar_units)

            #print(self.var_names_combined[0:100])

            # Check through until we find '.SP/' again
            window = ptf.read(4)
            foundSP = False
            i = 0
            while not foundSP and i < 250:
                if window == b'.SP/':
                    foundSP = True
                else:
                    window = window[-3:] + ptf.read(1)
                    #print(window)
                    i += 1

            # Read in all the time-independent variables
            i = 0
            time_indep_strings = []
            while window == b'.SP/' and i < 100000: # don't want it to go forever
                assert(int.from_bytes(ptf.read(4), byteorder="little") == 4)
                assert(int.from_bytes(ptf.read(4), byteorder="little") == 72)
                time_indep_strings.append(ptf.read(72).decode())
                assert(int.from_bytes(ptf.read(4), byteorder="little") == 72)
                assert(int.from_bytes(ptf.read(4), byteorder="little") == 4)
                window = ptf.read(4)
            # print(window)
            if window == b'.TR/': # this means there's a plot point next, i.e., the header is done?
            # assert(window == b'.TR/')
                self.time_indep_string_array.append(time_indep_strings)
                print("Finished reading time-independent variables for this MELCOR run.")

                # Figure out how long a plot point bytestring is
                assert(int.from_bytes(ptf.read(4), byteorder="little") == 4)
                self.len_plt_point = int.from_bytes(ptf.read(4), byteorder="little")
                print(self.len_plt_point, "bytes per plot point.")
                assert(self.len_plt_point == (ncomponents + 4)*4)
            else:
                if window == b'./*/':   # there's another restart with no plot points in between, i guess?
                    self.read_header(ptf)
                else:
                    print(window)   # not sure what would cause this
        else:
            if flag == b'./*/':     # there's another restart with no plot points in between, i guess?
                self.read_header(ptf)
            else:
                assert(flag == b'.TR/') # back to plot points





if __name__ == '__main__':
    try:
        config_file = sys.argv[1]
    except:
        config_file = "watchconfig.txt"
        print("Using watchconfig.txt.")

    watch = MelWatch(config_file)
    
    keep_going = 1
    sleep = False
    
    # plt.ion()
    
    # TODO: Need to figure out a way to make this work when num_rows or row_size is 1.
    num_rows = int(math.sqrt(len(watch.plots_pltvars)))
    row_size = round((len(watch.plots_pltvars))/num_rows + 0.49)
    f, ax = plt.subplots(num_rows, row_size, figsize=(19,9))
    
    f.show() # do this just once at the start, because it pulls focus to the plot window
    # and we don't want that happening every time it updates
    
    # f = matplotlib.figure.Figure()
    # canvas = matplotlib.backends.backend_agg.FigureCanvasAgg(f)
    # ax = f.subplots(num_rows, row_size, figsize=(19,9))
    
    # print("\nRows: ", num_rows, "  Columns: ", row_size)
    
    # define types of dashes, used for distinguishing horizontal lines
    dash_types = []
    dash_types.append([3, 2, 3, 2])
    dash_types.append([6, 3, 6, 3])
    dash_types.append([5, 3, 10, 3])
    dash_types.append([4, 1, 2, 1])
    dash_types.append([6, 2, 1, 2])
    for foo in range(10):
        dash_types.append([2, 1, 2, 1])
    
    
    
    num_times_plotted = 1   # memory usage increases every time, so we should reset it after a hundred or so
    
    # Plotting loop. It reads the data from the MelWatch object, plots it, and then 
    # if requested, tells it to read more data and keeps plotting.
    while keep_going: 

        if num_times_plotted > 1000: # close the figure and re-plot it, so memory use doesn't grow forever
        # not totally sure if this is necessary, I think most of the memory growth is from the growth in number of plot points
        # so I set it to a high value
            num_times_plotted = 0
            matplotlib.pyplot.close(f)
            f, ax = plt.subplots(num_rows, row_size, figsize=(19,9))
            f.show()

        n = watch.n
        nmin = 0
        t = watch.t
        
        # check what time units to use
        t_unit = "s"
        if watch.t_unit == "s" or watch.t_unit == "second" or watch.t_unit == "seconds":
            t_unit = "s"
        elif t[n-1] >= 7200: #86400.:    # by default use seconds for anything less than 2 hours
            t = watch.t / 3600.
            t_unit = "hrs"
        if watch.t_unit == "h" or watch.t_unit == "hr" or watch.t_unit == "hour" or watch.t_unit == "hours":
            t = watch.t / 3600.
            t_unit = "hrs"
            
        ncycle = watch.ncycle
        cpu = watch.cpu

        #plt.plot(ncycle[0:n],t[0:n])
        #plt.title("Problem time vs Cycle Number")
        #plt.xlabel("Cycle number")
        #plt.ylabel("Time [s]")
        #plt.figure()


        # ax[0,0].plot(t[0:n],cpu[0:n])
        # ax[0,0].set_title("CPU time vs problem time")
        # ax[0,0].set_xlabel("Time [" + t_unit + "]")
        # ax[0,0].set_ylabel("CPU Time [s]")
        # # ax[0,0].axis([min(t[0:n]), max(t[0:n]), min(cpu[0:n]), max(cpu[0:n])])
        # ax[0,0].set_xlim([min(t[0:n]), max(t[0:n])])
        # ax[0,0].yaxis.set_major_formatter(matplotlib.ticker.EngFormatter(unit='s'))

        # plt.ion()
        
        units_fixed = []
        for ind in range(len(watch.plot_vars)):
            # fix units
            if watch.pltvar_units[ind] == "PA":
                units_fixed.append("Pa")
            elif watch.pltvar_units[ind] == "S":
                units_fixed.append("s")
            elif watch.pltvar_units[ind] == "KG":
                units_fixed.append("kg")
            elif watch.pltvar_units[ind] == "M**3":
                units_fixed.append("$m^{3}$")
            elif watch.pltvar_units[ind] == "M":
                units_fixed.append("m")
            elif watch.pltvar_units[ind] == "M/S":
                units_fixed.append("m/s")
            elif watch.pltvar_units[ind] == "KG/S":
                units_fixed.append("kg/s")
            else:
                units_fixed.append(watch.pltvar_units[ind])
        
        # find indexes that correspond to fractions of the final problem time
        # we'll use this later to cut some plots off early
        t_final = t[n-1]
        divisions = 200
        n_frac = [0]*(divisions + 1)
        # for pointnum in range(n):
        for frac in range(divisions + 1):   # make this a binary search
            # if pointnum > 102 and pointnum < 106:
                # print(pointnum, t[pointnum], frac, frac * t_final / 10.0)
            tlim = frac * t_final / divisions # the time we're looking for the index of
            startn = 0
            endn = n - 1
            guess = round(endn * frac / divisions)
            while guess != endn:
                if t[guess] <= tlim:
                    startn = guess
                    guess = round((startn + endn + 0.1)/2)
                else: # t[guess] > tlim
                    endn = guess
                    guess = round((startn + endn + 0.1)/2)
            n_frac[frac] = guess
            # print(frac, t[n_frac[frac]], t[n_frac[frac]+1], tlim)
        # print(n_frac)
        # print(t[n-10:n])
        # print(n)
        
        
        # translate formulas into useable code
        # by replacing the plot variable titles from the config file with watch.data_arrays[ind]
        formula_expressions = []
        # replace "time" with the actual variable for time
        replacements = {"time":"t[0:n]"}
        # and each plot variable's title from the config file with the appropriate array reference, offset and scaled
        for ind, plotvar in enumerate(watch.plot_vars):
            replacements[watch.pltvar_titles[ind]] = "(watch.data_arrays["+str(ind)+"][0:n]*("+str(watch.pltvar_scale[ind])+")+("+str(watch.pltvar_offset[ind])+"))"
            
        def replace(match):
            return replacements[match.group(0)]
        
        for formula_string in watch.formulas:
            out = re.sub('|'.join(r'\b%s\b' % re.escape(s) for s in replacements), replace, formula_string)
            formula_expressions.append(out)
        
        # execute the formula expressions
        formula_results = []
        for expr in formula_expressions:
            # print(expr)
            exec("result = " + expr)
            formula_results.append(result)
        # print("Formulas evaluated: ", len(formula_results))
        # print(formula_results[0])
        
        for graph_ind, pltvar_indices in enumerate(watch.plots_pltvars):
            
            hline_indices = watch.plots_hlines[graph_ind]
            formula_indices = watch.plots_formulas[graph_ind]

            plotx = 0
            ploty = graph_ind
            while ploty >= row_size:
                plotx += 1
                ploty -= row_size
            
            if num_rows > 1 and row_size > 1:
                axe = ax[plotx,ploty]
            elif row_size > 1:
                axe = ax[ploty]
            else:
                axe = ax
            
            # ax[plotx,ploty].lines = []
            axe.cla()
            
            xlimit = 0.
            ymax = -1.e9
            ymin = 1.e9
            peak = -1.e9
            valley = 1.e9
            dashcount = 0
            
            # Check whether we should plot all the data, or just the tail
            nmin = 0
            if watch.plot_tail[graph_ind]:
                nmin = max(0, n - watch.plot_tail[graph_ind])
            
            
            # Now plot all the MELCOR plot variables that go on this plot
            for ind in pltvar_indices: # stuff specific to each curve in this graph
                
                values = watch.data_arrays[ind][nmin:n]
                
                # Apply scale, if any
                if watch.pltvar_scale[ind] != 1.0:
                    values = values * watch.pltvar_scale[ind]
                # Apply offset, if any
                if watch.pltvar_offset[ind] != 0.0:
                    values = values + watch.pltvar_offset[ind]
                
                
                # find the range of variation in this variable
                yvariation = max(values) - min(values)
                
                # use it to find the time at which the variable stops changing noticeably
                done_time = t_final
                if nmin == 0: # but only if we're plotting everything, not if we're doing a tail
                    for frac in range(divisions, 0, -1):
                        frac_yvariation = max(values[n_frac[frac]-nmin:]) - min(values[n_frac[frac]-nmin:])
                        if frac_yvariation < 0.001 * yvariation:
                            done_time = t[n_frac[frac]]
                if done_time < 2./3. * t_final:
                    xmax = done_time * 1.5
                else:
                    xmax = max(t[nmin:n])
                xlimit = max(xlimit, xmax) # the xmax of the graph will be the highest one for any of its curves

                maxval = max(values)
                minval = min(values)
                
                if maxval > 0 or minval < 0:
                    axe.plot(t[nmin:n],values, label=watch.pltvar_titles[ind])
                
                ymax = max(ymax, maxval*1.1)
                ymin = min(ymin, min(0.0, minval*1.1))
                
                
                peak = max(peak, maxval)
                valley = min(valley, minval)
                
                # Adjust axes in ways specific to the units
                if watch.pltvar_units[ind] == "PA":
                    ymin = min(0.8e5, minval/1.1)
                if watch.pltvar_units[ind] == "K":
                    ymin = min(250., minval/1.1)
            
            
            # And plot the formulas that go on this plot (mostly copied from above)
            for f_ind in formula_indices:
                values = formula_results[f_ind][nmin:n]
                yvariation = max(values) - min(values)
                done_time = t_final
                if nmin == 0:
                    for frac in range(divisions, 0, -1):
                        frac_yvariation = max(values[n_frac[frac]-nmin:]) - min(values[n_frac[frac]-nmin:])
                        if frac_yvariation < 0.001 * yvariation:
                            done_time = t[n_frac[frac]]
                if done_time < 2./3. * t_final:
                    xmax = done_time * 1.5
                else:
                    xmax = max(t[nmin:n])
                xlimit = max(xlimit, xmax)
                maxval = max(values)
                minval = min(values)
                if maxval > 0 or minval < 0:
                    axe.plot(t[nmin:n], values, label=watch.formula_titles[f_ind])
                ymax = max(ymax, maxval*1.1)
                ymin = min(ymin, min(0.0, minval*1.1))
                peak = max(peak, maxval)
                valley = min(valley, minval)
                if watch.formula_units[f_ind] == "Pa":
                    ymin = min(0.8e5, minval/1.1)
                if watch.formula_units[f_ind] == "K":
                    ymin = min(250., minval/1.1)


            # Set title and axis labels
            
            axe.set_title(watch.plot_titles[graph_ind])
            axe.set_xlabel("Time [" + t_unit + "]")
            # ax[plotx,ploty].set_ylabel(watch.plot_titles[graph_ind] + " [" + units_fixed[ind] + "]")

            if len(pltvar_indices) > 0:
                graph_unit = units_fixed[ind]
            elif len(formula_indices) > 0:
                graph_unit = watch.formula_units[f_ind]
            
            axe.set_ylabel("[" + graph_unit + "]")
            # Certain units work well with fancy formatting:
            if graph_unit == "m" or graph_unit == "Pa" or graph_unit == "m/s":
                axe.yaxis.set_major_formatter(matplotlib.ticker.EngFormatter(unit=graph_unit))
                if graph_unit == "Pa":
                    axe.set_ylabel("Pressure")
            # For everything else, we'll just use scientific notation where necessary
            elif peak >= 10000000:
                axe.set_ylabel("[$10^{6}$ " + graph_unit + "]")
                axe.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda t, pos: '{0:g}'.format(t/1.e6)))
            elif peak >= 10000:
                axe.set_ylabel("[$10^{3}$ " + graph_unit + "]")
                axe.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda t, pos: '{0:g}'.format(t/1000.)))
            #format_label_string_with_exponent(ax[plotx,ploty], axis='y')
            
            
            
            
            # Now plot horizontal lines
            for ind in hline_indices:
                yvalue = watch.hlines[ind]
                peak = max(peak, yvalue)
                valley = min(valley, yvalue)
                axe.plot([t[nmin], t[n-1]],[yvalue, yvalue], '--', label=watch.hline_titles[ind], color="black", dashes=dash_types[dashcount])
                dashcount += 1
            
            
            
            # Set axis boundaries
            
            yminbound = None
            ymaxbound = None
            
            if abs(valley) > 0 and abs((peak - valley) / valley) < 0.1:
                yminbound = ymin
                ymaxbound = ymax
                # axe.set_ylim([ymin, ymax])
            #ax[plotx,ploty].axis([min(t[0:n]), max(t[0:n]), ymin, ymax])

            # set x-axis limits if they were specified manually in config
            if watch.plot_limits[graph_ind][0] != None:
                xminbound = watch.plot_limits[graph_ind][0]
            else:
                xminbound = min(t[nmin:n])
            if watch.plot_limits[graph_ind][1] != None:
                xmaxbound = watch.plot_limits[graph_ind][1]
            else:
                xmaxbound = xlimit
            axe.set_xlim([xminbound, xmaxbound])
            
            # set y-axis limits if they were specified manually
            if watch.plot_limits[graph_ind][2] != None:
                yminbound = watch.plot_limits[graph_ind][2]
            if watch.plot_limits[graph_ind][3] != None:
                ymaxbound = watch.plot_limits[graph_ind][3]
            if yminbound != None:
                yautomax = axe.get_ylim()[1]
                axe.set_ylim([yminbound, yautomax])
            if ymaxbound != None:
                yprevmin = axe.get_ylim()[0]    # this could be the automatic lower bound, or it could be the manual value we just set
                axe.set_ylim([yprevmin, ymaxbound])
            
            # plt.axes().xaxis.set_tick_params(number=4)
            axe.locator_params(axis='x', nticks=5)  # attempt to set the approximate number of x-ticks, not sure it does anything
            axe.minorticks_on()
            axe.set_axisbelow(True) # make sure axis doesn't overlap with data
            
            axe.grid(color='black', alpha=0.5, linestyle=':')
            
            
            # Put in the legend, to the right of the plot
            fontP = matplotlib.font_manager.FontProperties()
            fontP.set_size('small') # reduce legend font size so it fits better
            
            legend_pos = 1.3
            if row_size == 2:
                legend_pos = 1.15
            # ax[plotx,ploty].legend() #loc='upper center', bbox_to_anchor=(0.5, -0.05),  shadow=False, ncol=1)
            axe.legend(loc='upper center', bbox_to_anchor=(legend_pos, 1.0), shadow=False, ncol=1, prop=fontP)
            
            # yax = axes.coords[1]
            # yax.display_minor_ticks(True)
            



        # f.subplots_adjust(hspace=0.3, wspace = 0.905, left = 0.055, right = 0.995)
        f.tight_layout()
        w = 1.00
        r = 0.92
        h = 0.24
        if row_size == 2:
            w = 0.45
            r = 0.9
        f.subplots_adjust(wspace=w, right=r)  # TODO: adjust this based on the number of graphs

        f.canvas.set_window_title(watch.plotfile)
        # plt.ion()
        # plt.show(block=False)
        f.canvas.draw()
        mypause(0.001)
        
        num_times_plotted += 1
        
        # plt.pause(0.001)
        # plt.show(block=False)
        
        # if keep_going == 1:
        # plt.pause(0.001)
        
        print('. Done plotting.')
        if sleep == False:
            time.sleep(0.1)
            # stuff = input("Input 'sleep' or 'stop': ")
            stuff = ""
            try:
                stuff = input_with_timeout("Press 'w' to watch (live update) or any other key to exit: ", 10000)
            except TimeoutExpired:
                sleep = True
        # exec(stuff)
            if 'w' in stuff:
                sleep = True
            elif stuff:
                keep_going = False
                print("\nExiting.")
                sys.exit(0)
        if num_times_plotted <= 2:
            print("\nWaiting for new plot points. Press 'p' to pause and any other key to exit.")
        else:
            print("Waiting.  ", end="")
        with open(watch.plotfile, 'rb') as ptf:
            # print(watch.spot)
            keep_going += 1
            watch.update_variables(ptf, watch.spot)
    