#! /usr/bin/env python
# dc_gui: Display a simple GLADE-designed gui. The root element
# should be a toplevel (i.e. a window) with the name "guiwindow"
# usage: dc_gui <gladefile.glade>


import sys
import os
if "--gtk3" in sys.argv or sys.version_info[0] >= 3:  # gtk3
    import gi
    gi.require_version('Gtk','3.0')
    from gi.repository import Gtk as gtk
    pass
else :  # gtk2
    import gobject
    import gtk
    pass

#class dummy(object):
#    pass

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
#
#installeddir=os.path.dirname(installedfile)
#
#if os.path.exists(os.path.join(installeddir,"../lib/checklist.py")):
#    installeddir=os.path.join(installeddir,"../")
#    pass
#elif os.path.exists(os.path.join(installeddir,"../gui2/lib/checklist.py")):
#    installeddir=os.path.join(installeddir,"../gui2")
#    pass
#
#sys.path.append(installeddir)
#sys.path.append(os.path.join(installeddir,"lib/"))


#import dg_io

from limatix.dc_gtksupp import build_from_file
from limatix.dc_gtksupp import dc_initialize_widgets
from limatix.dc_gtksupp import import_widgets
from limatix.dc_gtksupp import guistate as create_guistate

from limatix import lm_units


lm_units.units_config("insert_basic_units")

if "gobject" in sys.modules:  # only for GTK2
    gobject.threads_init()
    pass
    
import_widgets()


def main(args=None):
    if args is None:
        args=sys.argv
        pass
    
    argc=1
    gladefile=None
    while argc < len(args):
        arg=args[argc]
        if arg=="--gtk3":
            pass  # handled with imports, above
        elif arg.startswith('-'):
            raise ValueError("Unknown switch: %s" % (arg))
        if gladefile is None:
            gladefile=arg
            pass
        else :
            raise ValueError("Too many positional parameters")
        argc+=1
        pass
    
    # !!! Add paramdb2 instatiation here
    iohandlers={}   #=dg_io.io()
    guistate=create_guistate(iohandlers,None,[os.path.split(gladefile)[0]])
    
    (gladeobjdict,builder)=build_from_file(gladefile)
    
    dc_initialize_widgets(gladeobjdict,guistate)
    
    win=gladeobjdict["guiwindow"]
    win.show()
    gtk.main()
    pass
