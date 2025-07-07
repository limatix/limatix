import os
import os.path
import glob
import copy
import sys

try: 
    import pkg_resources
    pass
except TypeError:
    # Ignore error so we can run pychecker
    pass


import traceback

if "gi" in sys.modules:  # gtk3
    import gi
    gi.require_version('Gtk','3.0')
    from gi.repository import Gtk as gtk
    pass
else : 
    # gtk2
    import gobject
    import gtk
    pass

from lxml import etree

#from . import widgets

__pychecker__="no-import"

class guistate(object):
    iohandlers=None
    paramdb=None
    searchdirs=None  # list of directories to search for things like images

    def __init__(self,iohandlers,paramdb,searchdirs=None):
        self.iohandlers=iohandlers
        self.paramdb=paramdb
        if searchdirs is None:
            self.searchdirs=[]
            pass
        else :
            self.searchdirs=copy.copy(searchdirs)
            pass
        pass
        
    pass



class paramhandler(object):
    myprops=None
    gtksuper=None

    def __init__(self,gtksuper,proplist):
        if self.myprops is None:
            self.myprops={}
            pass
        if gtksuper is not None:
            assert(self.gtksuper is None)  # inheritance from only one C Gtk superclass permitted (set gtksuper to None when inheriting from Python) 
            self.gtksuper=gtksuper
            pass
        
        if proplist is not None:
            for prop in proplist:
                self.myprops[prop]=None
                pass
            pass

        #sys.stderr.write("type(self)=%s\n" % (str(type(self))))
        #sys.stderr.write("proplist=%s\n" % (repr(proplist)))

        # set defaults
        for prop in proplist:
            # sys.stderr.write("type(self)=%s\n" % (str(type(self))))

            # this next line may cause segfaults in gtk3 (!)
            #sys.stderr.write("setting prop %s to default %s\n" % (prop, self.gtksuper.get_property(prop)))
            self.myprops[prop]=self.gtksuper.get_property(prop)
            pass
        pass
    
    def do_set_property(self,property,value):
        if property.name in self.myprops:
            #sys.stderr.write("setting prop %s to %s in %s\n" % (property.name, value, str(type(self))))
            #if len(value)>100:
            #    import pdb as pdb3
            #    pdb3.set_trace()
            self.myprops[property.name]=value
            pass
        else :
            #print("Setting property: %s" % (property.name))
            self.gtksuper.do_set_property(self,property,value)
            pass
        
        pass

    
    def do_get_property(self,property):
        if property.name in self.myprops:
            return self.myprops[property.name]
            pass
        else :
            return self.gtksuper.do_get_property(self,property)
            pass
        
        pass
    
    
    pass


def build_from_file(gladefilename):
    # load specified glade file, build a set of objects, 
    # make sure all widgets and steps are loaded
    #from limatix import widgets
    #from limatix import steps
    builder=gtk.Builder()
    #sys.stderr.write("gladefilename=%s\n" % (gladefilename))
    builder.add_from_file(gladefilename)
    
    doc=etree.parse(gladefilename)
    
    objlist=doc.xpath("//object")

    # extract names of objects
    objnamelist = [o.attrib["id"] for o in objlist]
    
    # get each object into a dictionary
    
    objdict={}
    for objname in objnamelist:
        objdict[objname]=builder.get_object(objname)
        pass

    return (objdict,builder)


def dc_initialize_widgets(objdict,guistate):
    # io=guistate.io
    # initialize! 
    # initialize any dc_gui components with the io link
    for objname in objdict: 
        obj=objdict[objname]
        if hasattr(obj,"dc_gui_init"):
            obj.dc_gui_init(guistate)
            pass
        pass
    pass

def import_widgets():

    # Import all widgets registered with "limatix.widget" entry points

    # This way when we load in a .glade interface description 
    # that uses one of these widgets, it will load. 
    for entrypoint in pkg_resources.iter_entry_points("limatix.widget"):
        try:
            entrypoint.load()
            pass
        except: 
            (exctype,excvalue)=sys.exc_info()[:2]
            sys.stderr.write("Exception loading limatix widget plugin: %s: %s; widget will not be available." % (exctype.__name__,str(excvalue)))
            traceback.print_exc()
            pass
        pass


    #direc=os.path.split(widgets.__file__)[0]
    #
    #to_import=glob.glob(os.path.join(direc,"*.py"))
    #
    #for fname in to_import:
    #    modname=os.path.splitext(os.path.split(fname)[1])[0]
    #    # sys.stderr.write("modname=%s\n" % (modname))
    #    exec("from widgets import %s" % (modname))
    #    pass
    pass
