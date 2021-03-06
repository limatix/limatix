#! /usr/bin/env python

import sys
import os
import os.path
import string
import datetime
import socket

try:
    # py2.x
    from urllib import pathname2url
    from urllib import url2pathname
    from urllib import quote
    from urllib import unquote
    pass
except ImportError:
    # py3.x
    from urllib.request import pathname2url
    from urllib.request import url2pathname
    from urllib.parse import quote
    from urllib.parse import unquote
    pass


if "--gtk3" in sys.argv or sys.version_info[0] >= 3:  # gtk3
    import gi
    gi.require_version('Gtk','3.0')
    from gi.repository import Gtk as gtk
    from gi.repository import GObject as gobject
    pass
else :  # gtk2
    import gobject
    import gtk
    pass

import subprocess

from limatix import lm_units
lm_units.units_config("insert_basic_units")



class dummy(object):
    pass

## trace symbolic link to find installed directory
#thisfile=sys.modules[dummy.__module__].__file__
#if os.path.islink(thisfile):
#    installedfile=os.readlink(thisfile)
#    if not os.path.isabs(installedfile):
#        installedfile=os.path.join(os.path.dirname(thisfile),installedfile)
#        pass
#    pass
#else:
#    installedfile=thisfile
#    pass

#installeddir=os.path.dirname(installedfile)

#if os.path.exists(os.path.join(installeddir,"../lib/checklist.py")):
#    installeddir=os.path.join(installeddir,"../")
#    pass
#elif os.path.exists(os.path.join(installeddir,"../gui2/lib/checklist.py")):
#    installeddir=os.path.join(installeddir,"../gui2")
#    pass

#installedfile='/usr/local/dataguzzler-2.0.0-beta23-devel/bin/datacollect2'
#installeddir='/usr/local/dataguzzler-2.0.0-beta23-devel/gui2'

#sys.path.append(installeddir)
#sys.path.append(os.path.join(installeddir,"lib/"))
#sys.path.append(os.path.join(installeddir,"steps/"))


from limatix.dc_value import numericunitsvalue as numericunitsv
from limatix.dc_value import stringvalue as stringv
from limatix.dc_value import hrefvalue as hrefv
from limatix.dc_value import integervalue as integerv
from limatix.dc_value import photosvalue as photosv
from limatix.dc_value import datesetvalue as datesetv
from limatix.dc_value import accumulatingdatesetvalue as accumulatingdatesetv
from limatix.dc_value import xmltreevalue as xmltreev

from limatix.dc_dbus_barcode import dc_dbus_barcode

#import dg_io 
import limatix.paramdb2 as pdb
from limatix import paramdbfile
from limatix import dc2_misc

from limatix import checklist

from limatix.dc_gtksupp import build_from_file
from limatix.dc_gtksupp import dc_initialize_widgets
from limatix.dc_gtksupp import import_widgets
from limatix.dc_gtksupp import guistate as create_guistate

from limatix import explogwindow

from limatix import xmldoc
from limatix import xmlexplog
from limatix import checklistdb

# from dc_dbus_paramserver import dc_dbus_paramserver


# Plan -- 
# 1. Build global measnum handler, assign each checklist
#    that either has a save measurement step or 
#    the done_is_save_measurement flag a measnum on open.
# 2. Build "expanding date" field to accumulate dates.
# 3. Add nospecimen <specimen> attribute for checklists
#    that removes the <specimen> field. 
# 4. Add step that can be used for both vibrometer settings
# 5. Add step that clears a set of parameters
# 6. Make Save DGS or Save Settings turn button green after execution

def main(args=None):
    if args is None:
        args=sys.argv
        pass
    
    SingleSpecimen=None
    positionals=[]
    cmdline_guis=[]
    cmdline_plans=[]
    cmdline_checklists=[]
    cmdline_configfiles=[]
    dpdfiles=[]
    explogfile=None
    newlog=False
    parentchecklisturl=None
    
    argc=1
    
    while argc < len(args):
        arg=args[argc]
        
        if arg=="-m":
            SingleSpecimen=False
            pass
        elif arg=="-s":
            SingleSpecimen=True
            pass
        elif arg=="-f":
            argc+=1
            cmdline_configfiles.append(args[argc])
            pass
        elif arg=="-g":
            argc+=1
            cmdline_guis.append(args[argc])
            pass
        elif arg=="-c":
            argc+=1
            cmdline_checklists.append(args[argc])
            pass
        elif arg=="-p":
            argc+=1
            cmdline_plans.append(args[argc])
            pass
        elif arg=='-n':
            newlog=True
            pass
        elif arg=="-d":
            argc+=1
            dpdfiles.append(args[argc])
            pass
        elif arg=='--gtk3':
            # handled at imports, above
            pass
        elif arg=='--parent':
            # get relative url from xlg file to parent checklist
            argc+=1
            parentchecklisturl=args[argc]
            pass
        elif arg=='-h' or arg=="--help":
            print ("""Usage: %s [-s|-m] [-f <config.dcc>]  [-a] <explog.xlg> [-g gui.glade] [-c checklist.chx] [-p plan.plx] ...
            
Flags:
  -s                  Single specimen mode
  -m                  Multiple specimen mode
  -n                  Create new experiment log
  -f <config.dcc>     Open this config file (multiple OK)
  -g <gui.glade>      Open this gui (multiple OK)
  -c <checklist.chx>  Open this checklist (multiple OK)
  -p <plan.plx>       Open this plan (multiple OK)
  -d <params.dpd>     Open this parameter file (multiple OK)
  --gtk3
""" % (args[0]))
            sys.exit(0)
            pass
        elif arg[0]=='-':
            raise ValueError("Unknown command line switch %s" % (arg))
        else :
            positionals.append(arg)
            pass
        argc+=1
        pass
    
    if len(positionals) > 1:
        raise ValueError("Too many positional parameters (see -h for command line help")
    
    #if len(positionals) >= 1:
    #    if os.path.splitext(positionals[0])[1] != ".dcc":
    #        raise ValueError("First positional parameter %s must be a .dcc file (se#e -h for command line help)" % (positionals[0]))
    #    configfile=positionals[0]
    #    pass
    
    if len(positionals) == 1:
        if os.path.splitext(positionals[0])[1] != ".xlg":
            raise ValueError("First positional parameter %s must be a .xlg file (see -h for command line help)" % (positionals[0]))
        explogfile=positionals[0]
        pass
    


    if "gobject" in sys.modules:  # only for GTK2
        gobject.threads_init()
        pass
    
    import_widgets()


    # insert config from dpd files before all other configs. 
    configfiles=[]
    guis=[]
    checklists=[]
    plans=[]
    paramupdates=[]
    
    for dpdfile in dpdfiles: 
        (dpdconfigfiles,dpdguis,dpdchxfiles,dpdplans,dpdexplog,dpdparamupdates,dpdSingleSpecimen)=paramdbfile.load_params(dpdfile)
        configfiles.extend(dpdconfigfiles)
        guis.extend(dpdguis)
        checklists.extend(dpdchxfiles)
        plans.extend(dpdplans)
        paramupdates.append(dpdparamupdates)
        
        if explogfile is None and dpdexplog is not None:
            explogfile=dpdexplog
            pass
        elif explogfile is not None and dpdexplog is not None: 
            raise ValueError("Multiple experiment logs specified: %s as well as %s in %s" % (explogfile,dpdexplog,dpdfile))
        
        if SingleSpecimen is None and dpdSingleSpecimen is not None: 
            SingleSpecimen=dpdSingleSpecimen
            pass
        elif SingleSpecimen is not None and dpdSingleSpecimen is not None:
            raise ValueError("Single/multiple specimen mode specified multiple times.")
        
        pass
    

    configfiles.extend(cmdline_configfiles)
    guis.extend(cmdline_guis)
    checklists.extend(cmdline_checklists)
    plans.extend(cmdline_plans)
    
    

    
    
    iohandlers={}   #dg_io.io()
    
    paramdb=pdb.paramdb(iohandlers)
    #if SingleSpecimen is None: # not already set on command line
    # SingleSpecimen chooser moved to explogwindow.py


    # define parameters
    
    # parameters that are supposed to go in the summary need to have an adddoc() call in explogwindow.syncexplog. Also see "not synced" in paramdbfile.py
    # The adddoc() call can also be used to supply a default value which will be 
    # set only if not read in from the file. 
    #  and a corresponding remdoc call in explogwindow.unsyncexplog

    # paramdb.addparam("clinfo",stringv)
    paramdb.addparam("hostname",stringv,build=lambda param: xmldoc.synced(param),non_settable=True)
    paramdb.addparam("specimen",stringv,build=lambda param: xmldoc.synced(param)) # reset_with_meas_record=not SingleSpecimen)... MonkeyPatched later
    paramdb.addparam("perfby",stringv,build=lambda param: xmldoc.synced(param))
    # paramdb.addparam("date",stringv,build=lambda param: xmldoc.synced(param))
    #paramdb.addparam("date",datesetv,build=lambda param: xmldoc.synced_accumulating_dates(param))
    paramdb.addparam("date",accumulatingdatesetv,build=lambda param: xmldoc.synced(param))
    paramdb.addparam("checklists",xmltreev,build=lambda param: xmldoc.synced(param,tag_index_paths_override={"{http://limatix.org/datacollect}checklist":"@{http://www.w3.org/1999/xlink}href"}),hide_from_meas=True)
    checklistdb.register_paramdb(paramdb,"checklists",None,False)
    
    paramdb.addparam("plans",xmltreev,build=lambda param: xmldoc.synced(param,tag_index_paths_override={"{http://limatix.org/datacollect}checklist":"@{http://www.w3.org/1999/xlink}href"}),hide_from_meas=True)
    checklistdb.register_paramdb(paramdb,"plans",None,True)
    
    
    paramdb.addparam("expnotes",stringv,build=lambda param: xmldoc.synced(param),hide_from_meas=True)
    paramdb.addparam("goal",stringv,build=lambda param: xmldoc.synced(param),hide_from_meas=True)

    # "dest" is the contextdir for XML data and hrefs within paramdb
    # EXCEPT when paramdb is being written out to the experiment log.
    # Will be auto-fixedup because the dcvalue xmlrepr methods will 
    # convert their context to that of the file they are writing.
    paramdb.addparam("dest",hrefv,build=lambda param: xmldoc.synced(param),hide_from_meas=True)
    paramdb.addparam("explogname",stringv,hide_from_meas=True)
    
    #paramdb.addparam("nextmeasnum",integerv,build=lambda param: xmldoc.synced(param),hide_from_meas=True)
    paramdb.addparam("measnum",integerv,build=lambda param: xmldoc.synced(param),hide_from_meas=True)
    paramdb.addparam("expphotos",photosv,build=lambda param: xmldoc.synced(param),hide_from_meas=True)
    paramdb.addparam("measphotos",photosv,reset_with_meas_record=True)
    paramdb.addparam("notes",stringv,build=lambda param: xmldoc.synced(param))  # notes is shared between (the measurement checklist(s) that have done_is_save_measurement set or have a save measurement step) and the experiment log (although notes is not written directly to the experiment log except in a save measurement step)

    # print "Notes value: ", str(type(str(paramdb["notes"].dcvalue)))

    paramdb.addparam("measchecklist",hrefv,reset_with_meas_record=True)
    

    # auto-set date 
    if paramdb["date"].dcvalue.isblank():
        curdate=datetime.date.today()
        paramdb["date"].requestvalstr_sync(curdate.isoformat())
        pass

    # auto-set hostname
    dc2_misc.set_hostname(paramdb)
    # print str(paramdb["date"].dcvalue)
    
    # Connect to dbus (barcode reader)
    dbuslink=dc_dbus_barcode(paramdb)
    
    

    explogwin=explogwindow.explogwindow(os.path.join(os.path.split(explogwindow.__file__)[0],"explogwin.glade"),paramdb,SingleSpecimen)
    
    ## Create dbus paramserver
    #paramserver=dc_dbus_paramserver(paramdb,explogwin.checklists)
    # paramserver is now created within explogwin.createparamserver() and stored as a member of explogwin
    

    guistate=create_guistate(iohandlers,paramdb) # can add search directories as additional parameters here [os.path.split(fname)[0]])

    
    explogwin.dc_gui_init(guistate)
    
    confighrefs=[ hrefv(pathname2url(configfile),contexthref=hrefv("./")) for configfile in configfiles ]
    
    if len(confighrefs)==0:
        confighrefs=None
        pass
    
    if explogfile is not None and newlog:
        #sys.stderr.write("new_explog(%s)\n" % (explogfile))
        explogwin.new_explog(hrefv(pathname2url(explogfile),contexthref=hrefv("./")),parentchecklisturl=parentchecklisturl,confighrefs=confighrefs)
        pass
    elif explogfile is not None and not newlog:
        #sys.stderr.write("open_explog(%s)\n" % (explogfile))
        explogwin.open_explog(hrefv(pathname2url(explogfile),contexthref=hrefv("./")),confighrefs=confighrefs)
        pass


    ## load config files
    #for configfile in configfiles: 
    #    #sys.stderr.write("datacollect2: Loading config file %s\n" % (configfile))
    #    confighref=hrefv(pathname2url(configfile))
    #    explogwin.load_config(confighref)
    #    pass


    # update paramdb entries specified in .dpd file
    dpdlog=[]
    for paramupdate in paramupdates:
        dpdlog.extend(paramdbfile.apply_paramdb_updates(paramupdate,paramdb))
        pass

    for (paramname,status,val1,val2) in dpdlog:
        if status=="dangerous":
            sys.stderr.write("Warning loading %s: Dangerous parameter %s ignored\n" % (dpdfile,paramname))
            pass
        elif status=="mismatch":
            sys.stderr.write("Warning loading %s: Parameter %s request mismatch (requested: %s; actual: %s)\n" % (dpdfile,paramname,str(val1),str(val2)))
            pass
        elif status=="error":
            sys.stderr.write("Warning loading %s: Parameter %s request error (requested: %s)\n" % (dpdfile,paramname,str(val1)))
            pass
        elif status!="match":
            raise ValueError("Unknown status message loading paramdb from %s" % (dpdfile))
        
        pass
    




    if explogwin.explog is not None and explogwin.explog.filehref is not None:
        for gui in guis:
            guihref=hrefv(pathname2url(gui),contexthref=hrefv("./"))
            explogwin.open_gui(guihref)
            #explogwin.open_gui(gui)
            pass
        
        for checklist in checklists:
            checklisthref=hrefv(pathname2url(checklist),contexthref=hrefv("./"))
            
            explogwin.addtochecklistmenu(checklisthref)
            explogwin.open_checklist(checklisthref)
            pass
    
        for plan in plans:
            planhref=hrefv(pathname2url(plan),contexthref=hrefv("./"))
            explogwin.open_plan(planhref)
            pass
        pass
    elif len(guis) > 0 or len(checklists) > 0 or len(plans) > 0:
        print("Cannot auto-open gui, checklist, or plan unless experiment log opened.")
        sys.exit(1)
        pass

    

    #win=explogwin.getwindow()
    explogwin.show_all()
    gtk.main()
    pass
